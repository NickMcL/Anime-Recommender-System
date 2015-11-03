import dryscrape
import sqlite3
from lxml import html

MAL_RECENT_USERS_URL = 'http://myanimelist.net/users.php'

MAL_USER_ANIME_LIST_URL_FORMAT = 'http://myanimelist.net/animelist/{username}'

MAL_ANIME_LIST_STOP_STATUS = 'Plan to Watch'


# This XPath expression will get all of the recent users listed on MAL's recent
# users page.
RECENT_USERS_XPATH = ('//*[@id="content"]/table/tbody/tr/td[1]/table'
                      '/tbody/tr/td/div[1]/a/text()')

ANIME_LIST_TABLES_XPATH = '//*[@id="list_surround"]/table'

GET_TABLE_STATUS_XPATH = './/*[@class="header_title"]/span/text()'

GET_TABLE_HEADER_XPATH = './/*[@class="table_header"]'

GET_TABLE_CATEGORY_TOTALS_XPATH = './/*[@class="category_totals"]'

GET_TABLE_ANIME_NAME_XPATH = './/*[@class="animetitle"]/span/text()'

GET_TABLE_ANIME_SCORE_XPATH = './/td[3]/text()'


MAL_USER_DB_NAME = 'mal_users.db'

MAL_USER_SCORES_TABLE_NAME = 'MALUserScores'


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
        db_score = self.score if self.score != -1 else 'NULL'
        cursor.execute('INSERT INTO {0} VALUES(?,?,?,?)'.format(table_name),
                       [self.user_name, self.anime_name, self.status,
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
    return page_tree.xpath(RECENT_USERS_XPATH)

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
    page_tables.pop(0)  # The first table is a navigation bar
    for table in page_tables:
        # Check if the table holds a status type
        table_status = table.xpath(GET_TABLE_STATUS_XPATH)
        if len(table_status) > 0:
            current_status = str(table_status[0])
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
        anime_name = table.xpath(GET_TABLE_ANIME_NAME_XPATH)[0].encode('utf-8')
        score = str(table.xpath(GET_TABLE_ANIME_SCORE_XPATH)[0])
        score = int(score) if score.isdigit() else -1
        anime_scores.append(
                MALUserScore(mal_user, anime_name, current_status, score))

    return anime_scores
