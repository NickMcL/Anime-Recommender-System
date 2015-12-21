import sqlite3

from collections import defaultdict

DROPPED_STATUS = 'Dropped'
COMPLETED_STATUS = 'Completed'
ON_HOLD_STATUS = 'On-Hold'
WATCHING_STATUS = 'Watching'

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

class ImplicitFeedback:

    def __init__(self, user, item, status):
        self.user = user
        self.item = item
        self.status = status

    def __str__(self):
        return 'User: {0}\nItem: {1}\nStatus: {2}'.format(
                self.user, self.item, self.status)

    def __repr__(self):
        return 'User: {0}\nItem: {1}\nStatus: {2}'.format(
                self.user, self.item, self.status)

    def is_positive(self):
        return self.status != DROPPED_STATUS


def topk_test(topk_data_db_path, topk_data_table_name, model, rand_anime_total):
    anime_ranks = defaultdict(int)
    user_anime_pairs = defaultdict(list)
    conn = sqlite3.connect(topk_data_db_path)
    with conn:
        cur = conn.cursor()
        cur.execute('''SELECT user_id, anime_name, rand_anime_name
                       FROM {0}'''.format(topk_data_table_name))
        while True:
            row = cur.fetchone()
            if row is None:
                break
            user_anime_pairs[(row[0], row[1])].append(row[2])

    cntr = 0
    for user_anime_pair, rand_anime in user_anime_pairs.iteritems():
        score_predictions = []
        for anime in rand_anime:
            score_predictions.append((
                model.predict(user_anime_pair[0], anime),
                anime
            ))
        score_predictions.append((
            model.predict(user_anime_pair[0], user_anime_pair[1]),
            user_anime_pair[1]
        ))
        sorted_predictions = sorted(score_predictions, key=lambda i: i[0],
                reverse=True)
        rank = [s[1] for s in sorted_predictions].index(user_anime_pair[1])
        anime_ranks[rank] += 1

        cntr += 1
        if cntr % 200 == 0:
            print cntr

    rank_distribution_x = []
    rank_distribution_y = []
    total_pairs = len(user_anime_pairs)
    cummulative_total = 0
    cntr = 0
    for possible_rank in xrange(rand_anime_total + 1):
        rank_total = anime_ranks.get(possible_rank)
        if rank_total is not None:
            cummulative_total += float(rank_total) / total_pairs
            cntr += rank_total
        rank_distribution_x.append(float(possible_rank) / rand_anime_total)
        rank_distribution_y.append(cummulative_total)
    return (rank_distribution_x, rank_distribution_y)


def get_ratings_from_db(db_path, table_name):
    conn = sqlite3.connect(db_path)
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT user_id, anime_name, score FROM {0}'.format(
                    table_name))
        ratings = [Rating(r[0], r[1], r[2]) for r in cur.fetchall()]

    return ratings

def get_implicit_feedback_from_db(db_path, table_name):
    conn = sqlite3.connect(db_path)
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT user_id, anime_name, status FROM {0}'.format(
                    table_name))
        imps = [ImplicitFeedback(f[0], f[1], f[2]) for f in cur.fetchall()]

    return imps


basic_params = [
    (50, 0.1, 0.01, 200),
    (100, 0.1, 0.01, 200),
    (150, 0.1, 0.01, 200),
    (200, 0.1, 0.01, 200),
    (100, 0.5, 0.01, 200),
    (100, 0.01, 0.01, 200),
    (100, 0.001, 0.01, 200),
    (100, 0.0001, 0.01, 200),
    (100, 0.1, 0.5, 200),
    (100, 0.1, 0.1, 200),
    (100, 0.1, 0.001, 200),
    (100, 0.1, 0.0001, 200),
    (100, 0.1, 0.01, 100),
    (100, 0.1, 0.01, 300),
]

bias_params = [
    (200, 0.1, 0.01, 150),
    (200, 0.1, 0.01, 250),
    (200, 0.1, 0.01, 300),
    (250, 0.1, 0.01, 200),
    (300, 0.1, 0.01, 200),
    (350, 0.1, 0.01, 200),
]

def run_validation(train_ratings, valid_ratings, Model, use_bias):
    if use_bias:
        file_name = 'valid_biases.log'
        vparams = bias_params
    else:
        file_name = 'valid_basic.log'
        vparams = basic_params

    rmses = {}
    for params in vparams:
        m = Model(train_ratings, params[0], params[1],
                  params[2], params[3], use_bias, None,
                  pickle_dir='trained_models/basic')
        successful = m.train()
        if not successful:
            rmses[params] = -1
            continue

        rmse = m.test(valid_ratings)
        rmses[params] = rmse

        f = open(file_name, 'a')
        f.write('RMSE: {0}\n'.format(rmse))
        f.write('D: {0} Lambda: {1} Nu: {2} I: {3}\n\n'.format(*params))
        f.close()

    for k, v in sorted(rmses.items(), key=lambda i: i[1]):
        print '{0}: {1} '.format(k, v)
