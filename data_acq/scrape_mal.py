import dryscrape
import sqlite3
from lxml import html
from random import random
from time import sleep

MAL_RECENT_USERS_URL = 'http://myanimelist.net/users.php'

MAL_USER_ANIME_LIST_URL_FORMAT = 'http://myanimelist.net/animelist/{username}'

MAL_ANIME_LIST_STOP_STATUS = u'Plan to Watch'


# This XPath expression will get all of the recent users listed on MAL's recent
# users page.
RECENT_USERS_XPATH = ('//*[@id="content"]/table/tbody/tr/td[1]/table'
                      '/tbody/tr/td/div[1]/a/text()')

ANIME_LIST_TABLES_XPATH = '//*[@id="list_surround"]/table'

GET_TABLE_STATUS_XPATH = './/*[@class="header_title"]/span'

GET_TABLE_HEADER_XPATH = './/*[@class="table_header"]'

GET_TABLE_CATEGORY_TOTALS_XPATH = './/*[@class="category_totals"]'

GET_TABLE_ANIME_NAME_XPATH = './/*[@class="animetitle"]/span/text()'

GET_TABLE_ANIME_SCORE_XPATH = './/td[3]/text()'


MAL_USER_DB_NAME = u'mal_users.db'

MAL_USER_SCORES_TABLE_NAME = u'MALUserScores'

# A MAL user must have at least this many scores to be stored in the database
MIN_SCORES_FOR_STORAGE = 5


class MALUserScore:
    """Object for encapsulating the information for a score given by a MAL
    user.
    """

    def __init__(self, user_name, anime_name, status, score):
        self.user_name = user_name
        self.anime_name = anime_name
        self.status = status
        self.score = score

    def write_to_db(self, cursor, table_name):
        db_score = self.score if self.score is None else self.score.decode('utf-8')
        cursor.execute(u'INSERT INTO {0} VALUES(?,?,?,?)'.format(table_name),
                       [self.user_name.decode('utf-8'),
                        self.anime_name.decode('utf-8'),
                        self.status.decode('utf-8'),
                        db_score]);

    def __repr__(self):
        return '{0}\t{1}\t{2}\t{3}'.format(self.user_name, self.anime_name,
                                           self.status, self.score)


def scrape_recent_mal_users(session):
    """Returns a list of users from MAL's recent users page.

    session - a dryscrape session object that can be used for the scraping.
    """
    session.visit(MAL_RECENT_USERS_URL)
    page_tree = html.fromstring(session.body())
    return [u.encode('utf-8') for u in page_tree.xpath(RECENT_USERS_XPATH)]

def get_mal_user_scores(session, mal_user):
    """Returns a list of MALUserScore objects with the scores for the given
    MAL user.

    session - a dryscape session object that can be used for the scraping.
    mal_user - a string of the username for a MAL user.
    """
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
                MALUserScore(mal_user, anime_name, current_status, score))

    return anime_scores

def mine_mal_scores(min_delay, iterations):
    """Mine MAL user scores and insert them into a database.

    min_delay - the minimum number of minutes to wait between each request to
                MAL.
    iterations - the number of mining iterations to do. Each iteration checks
                 15 MAL users.
    """
    conn = sqlite3.connect(MAL_USER_DB_NAME)
    cur = conn.cursor()

    session = dryscrape.Session()
    session.set_attribute('auto_load_images', False)
    for i in range(iterations):
        mal_users = scrape_recent_mal_users(session)
        for mal_user in mal_users:
            # Space out requests to avoid spamming MAL servers
            sleep(min_delay * 60 + random() * 60)
            print u'Mining scores for user: {0}'.format(mal_user)
            scores = get_mal_user_scores(session, mal_user)

            # Only keep users that have are least the minimum number of scores
            total_scores = sum(1 for s in scores if s.score is not None)
            print u'User had {0} scores.\n'.format(total_scores)
            if total_scores < MIN_SCORES_FOR_STORAGE:
                continue

            try:
                for score in scores:
                    score.write_to_db(cur, MAL_USER_SCORES_TABLE_NAME)
            except:
                conn.close()
                raise
            conn.commit()
    conn.close()
