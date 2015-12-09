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

valid_params = [
    (50, 0.1, 0.01, 200),
    (150, 0.1, 0.01, 200),
    (200, 0.1, 0.01, 200),
    (100, 0.01, 0.01, 200),
    (100, 0.001, 0.01, 200),
    (100, 0.0001, 0.01, 200),
    (100, 0.1, 0.1, 200),
    (100, 0.1, 0.001, 200),
    (100, 0.1, 0.0001, 200),
    (100, 0.1, 0.01, 100),
    (100, 0.1, 0.01, 300),
]

def run_validation(train_ratings, valid_ratings, Model):
    f = open('valid.log', 'w')
    rmses = {}
    for params in valid_params:
        m = Model(train_ratings, params[0], params[1],
                  params[2], params[3], True)
        successful = m.train()
        if not successful:
            rmses[params] = -1
            continue

        rmse = m.test(valid_ratings)
        rmses[params] = rmse

        f.write('RMSE: {0}\n'.format(rmse))
        f.write('D: {0} Lambda: {1} Nu: {2} I: {3}\n\n'.format(*params))
    f.close()

    for k, v in sorted(rmses.items(), key=lambda i: i[1]):
        print '{0}: {1} '.format(k, v)
