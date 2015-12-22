# Functions for crawling public anime rating data on MyAnimeList.

import dryscrape
import md5
import sqlite3
from lxml import html
from time import sleep

# URL for the page on MyAnimeList that lists users that have recently logged in
MAL_RECENT_USERS_URL = 'http://myanimelist.net/users.php'

# URL format for a user's anime list page on MyAnimeList
MAL_USER_ANIME_LIST_URL_FORMAT = 'http://myanimelist.net/animelist/{username}'

# The crawler will not parse anymore ratings for a user once it comes across
# this status on a user's anime list page
MAL_ANIME_LIST_STOP_STATUS = u'Plan to Watch'


# XPath for getting all of the recent users listed on MAL's recent users page.
RECENT_USERS_XPATH = ('//*[@id="content"]/table/tbody/tr/td[1]/table'
                      '/tbody/tr/td/div[1]/a/text()')

# XPath for getting all of tables in a user's anime list
ANIME_LIST_TABLES_XPATH = '//*[@id="list_surround"]/table'

# XPath for getting the status label for a table in a user's anime list
GET_TABLE_STATUS_XPATH = './/*[@class="header_title"]/span'

# XPath for getting the table header for a table in a user's anime list
GET_TABLE_HEADER_XPATH = './/*[@class="table_header"]'

# XPath for getting the category totals elements in a user's anime list
GET_TABLE_CATEGORY_TOTALS_XPATH = './/*[@class="category_totals"]'

# XPath for getting the anime name from an entry in a table in a user's anime
# list
GET_TABLE_ANIME_NAME_XPATH = './/*[@class="animetitle"]/span/text()'

# XPath for getting the score from an entry in a table in a user's anime list
GET_TABLE_ANIME_SCORE_XPATH = './/td[3]/text()'


# Name of the sqlite3 database to store the anime rating data
MAL_RATINGS_DB_NAME = u'data_acquisition/temp_ratings.db'

# Name of the table in the sqlite3 database to store the anime rating data
MAL_RATINGS_TABLE_NAME = u'MALRatings'

# A MyAnimeList user must have at least this many scores to be stored in the
# database. This limit is used to avoid adding ratings from fake or incomplete
# users to the database because those users will have very few ratings on their
# anime list.
MIN_SCORES_FOR_STORAGE = 5


class MALUserScore:
    """Object for encapsulating the information for a score given by a MAL
    user.
    """

    def __init__(self, user_id, anime_name, status, score):
        self.user_id = user_id
        self.anime_name = anime_name
        self.status = status
        self.score = score

    def write_to_db(self, cursor, table_name):
        """Uses the given cursor to add a row to the given table with this
        object's score information.
        """
        db_score = self.score if self.score is None else self.score.decode('utf-8')
        cursor.execute(u'INSERT INTO {0} VALUES(?,?,?,?)'.format(table_name),
                       [self.user_id.decode('utf-8'),
                        self.anime_name.decode('utf-8'),
                        self.status.decode('utf-8'),
                        db_score]);

    def __repr__(self):
        return '{0}\t{1}\t{2}\t{3}'.format(self.user_id, self.anime_name,
                                           self.status, self.score)


def get_recent_mal_users(session):
    """Returns a list of users from MAL's recent users page.

    session - a dryscrape session object that can be used for the crawling.
    """
    session.visit(MAL_RECENT_USERS_URL)
    page_tree = html.fromstring(session.body())
    return [u.encode('utf-8') for u in page_tree.xpath(RECENT_USERS_XPATH)]

def get_mal_user_scores(session, mal_user):
    """Returns a list of MALUserScore objects with the scores for the given
    MAL user.

    session - a dryscape session object that can be used for the crawling.
    mal_user - a string of the username for a MAL user.
    """
    # Generate anonymous user ID for this user to associate with their ratings
    user_id = md5.new(mal_user).hexdigest().encode('utf-8')

    anime_scores = []
    session.visit(MAL_USER_ANIME_LIST_URL_FORMAT.format(username=mal_user))
    page_tree = html.fromstring(session.body())

    page_tables = page_tree.xpath(ANIME_LIST_TABLES_XPATH)
    # There will be no table objects on the page if the user made their anime
    # list private.
    if len(page_tables) == 0:
        return []

    page_tables.pop(0)  # The first table is a navigation bar
    for table in page_tables:
        # Check if the table holds a status type
        table_status = table.xpath(GET_TABLE_STATUS_XPATH)
        if len(table_status) > 0:
            # The text attribute is None when the element has no text in it
            if table_status[0].text is None:
                current_status = ''
            else:
                current_status = table_status[0].text.encode('utf-8')

            if current_status == MAL_ANIME_LIST_STOP_STATUS:
                break
            continue

        # Skip over the table holding the table headers
        if len(table.xpath(GET_TABLE_HEADER_XPATH)) > 0:
            continue

        # Skip over the table category totals information
        if len(table.xpath(GET_TABLE_CATEGORY_TOTALS_XPATH)) > 0:
            continue

        # Create MALUserScore object with the score info from this table
        try:
            anime_name = table.xpath(GET_TABLE_ANIME_NAME_XPATH)[0].encode('utf-8')
            score = table.xpath(GET_TABLE_ANIME_SCORE_XPATH)[0].encode('utf-8')
        except IndexError:
            # If an IndexError occurs, the anime list page uses custom
            # formatting instead of the default, so don't try to parse it
            return []

        score = score if score.isdigit() else None
        anime_scores.append(
                MALUserScore(user_id, anime_name, current_status, score))

    return anime_scores

def crawl_mal_ratings(request_delay, iterations):
    """Crawl MAL user ratings and insert them into a database.

    request_delay - the number of seconds to wait between each request to MAL.
                    This should at least be 30-60 seconds to ensure that the
                    crawler doesn't send requests any faster than a human could
                    so that it doens't spam MAL's servers.
    iterations - the number of crawling iterations to do. Each iteration checks
                 15 MAL users.
    """
    conn = sqlite3.connect(MAL_RATINGS_DB_NAME)
    cur = conn.cursor()

    session = dryscrape.Session()
    session.set_attribute('auto_load_images', False)
    for i in range(iterations):
        mal_users = get_recent_mal_users(session)

        for mal_user in mal_users:
            # Space out requests to avoid spamming MAL servers
            sleep(request_delay)
            print u'Crawling scores for user: {0}'.format(
                    md5.new(mal_user).hexdigest())
            scores = get_mal_user_scores(session, mal_user)

            # Only keep users that have at least the minimum number of scores
            total_scores = sum(1 for s in scores if s.score is not None)
            print u'User had {0} scores.\n'.format(total_scores)
            if total_scores < MIN_SCORES_FOR_STORAGE:
                continue

            try:
                for score in scores:
                    score.write_to_db(cur, MAL_RATINGS_TABLE_NAME)
            except:
                conn.close()
                raise
            conn.commit()
    conn.close()

