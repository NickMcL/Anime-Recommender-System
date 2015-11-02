import dryscrape
from lxml import html

MAL_RECENT_USERS_URL = 'http://myanimelist.net/users.php'

# This XPath expression will get all of the recent users listed on MAL's recent
# users page.
RECENT_USERS_XPATH = ('//*[@id="content"]/table/tbody/tr/td[1]/table'
                      '/tbody/tr/td/div[1]/a/text()')

def scrape_recent_mal_users(session):
    """Returns a list of users from MAL's recent users page.

    session - a dryscrpage session object that can be used for the scraping.
    """
    session.visit(MAL_RECENT_USERS_URL)
    page_body = session.body()
    page_tree = html.fromstring(page_body)
    return page_tree.xpath(RECENT_USERS_XPATH)
