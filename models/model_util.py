import sqlite3

class Rating:

    def __init__(self, user, item, score):
        self.user = user
        self.item = item
        self.score = score

    def __str__(self):
        return 'User: {0}\nItem: {1}\nScore: {2}'.format(
                self.user, self.item, self.score)

    def __repr__(self):
        return 'User: {0}\nItem: {1}\nScore: {2}'.format(
                self.user, self.item, self.score)


def get_ratings_from_db(db_path, table_name):
    conn = sqlite3.connect(db_path)
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT user_id, anime_name, score FROM {0}'.format(
                    table_name))
        ratings = [Rating(r[0], r[1], r[2]) for r in cur.fetchall()]

    return ratings

