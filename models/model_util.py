# Utility functions and objects for working with model objects.

import sqlite3
from collections import defaultdict

# MyAnimeList possible rating statuses
DROPPED_STATUS = 'Dropped'
COMPLETED_STATUS = 'Completed'
ON_HOLD_STATUS = 'On-Hold'
WATCHING_STATUS = 'Watching'


class Rating:
    """Encapsulates the information for a user rating on an item."""

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
    """Encapsulates the information for implicit feedback given by a user on an
    item.
    """

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

    def is_dropped(self):
        return self.status == DROPPED_STATUS


def topk_test(topk_data_db_path, topk_data_table_name, model, rand_anime_total):
    """Runs the top-k test proposed by Yehuda Koren in his "Factorization Meets
    the Neighborhood: a Multifaceted Collaborative Filtering Model" paper.

    topk_data_db_path - String of the path to the database containing the table
                        with the data for the top-k test.
    topk_data_db_path - String of the name of the table with the top rated
                        anime and selected random anime for the top-k test.
    model - Model object to use for the top-k test. Must have a
            predict(user, item) method to predict the score a user would give
            an item.
    rand_anime_total - Amount of random anime selected for each top rated anime
                       in the top-k data set.

    Returns two lists. The first list is an ordered list of the possible ranks
    in the top-k test, and the second list is an ordered list of cummulative
    probabilities that correspond to each rank in the first list. Comparing to
    the graph in Koren's paper, the first list is the x-axis values and the
    second list is the y-axis values for the top-k test results.
    """
    anime_ranks = defaultdict(int)
    user_anime_pairs = defaultdict(list)
    conn = sqlite3.connect(topk_data_db_path)

    # Load all of the top-k test data into memory
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
        # Predict the score the user would give each of the random anime for
        # selected for this top rated anime for the user
        score_predictions = []
        for anime in rand_anime:
            score_predictions.append((
                model.predict(user_anime_pair[0], anime),
                anime
            ))

        # Determine where the predicted score of the top rated anime for the
        # user would rank in comparison to the predicted scores for the random
        # anime
        score_predictions.append((
            model.predict(user_anime_pair[0], user_anime_pair[1]),
            user_anime_pair[1]
        ))
        sorted_predictions = sorted(score_predictions, key=lambda i: i[0],
                reverse=True)
        rank = [s[1] for s in sorted_predictions].index(user_anime_pair[1])
        anime_ranks[rank] += 1

        # Print progress
        cntr += 1
        if cntr % 200 == 0:
            print cntr

    # Determine cummulative probability distribution for each possible rank
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
    """Loads ratings from the given table in the given database. Returns a list
    of Rating objects for the ratings in the table.
    """
    conn = sqlite3.connect(db_path)
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT user_id, anime_name, score FROM {0}'.format(
                    table_name))
        ratings = [Rating(r[0], r[1], r[2]) for r in cur.fetchall()]

    return ratings

def get_implicit_feedback_from_db(db_path, table_name):
    """Loads implicit feedback data from the given table in the given database.
    Returns a list of ImplicitFeedback objects for the implicit feedback data
    in the table.
    """
    conn = sqlite3.connect(db_path)
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT user_id, anime_name, status FROM {0}'.format(
                    table_name))
        imps = [ImplicitFeedback(f[0], f[1], f[2]) for f in cur.fetchall()]

    return imps

def run_validation(train_ratings, valid_ratings, Model, use_bias, valid_params,
                   log_file):
    """Runs validation testing for the given models using the given set of
    validation parameters.

    train_ratings - List of rating objects to use to train the model.
    valid_ratings - List of rating objects to use to test the model for
                    validation testing.
    Model - Class of the model to run the validation testing for.
    use_bias - Boolean indicating whether to use bias factors for the given
               model type or not.
    valid_params - List of tuples of different sets of parameters to try during
                   the validation testing.
    log_file - String of path to a file to log the results of the validation
               testing to.
    """
    rmses = {}
    for params in valid_params:
        m = Model(train_ratings, params[0], params[1],
                  params[2], params[3], use_bias)
        successful = m.train()
        if not successful:
            rmses[params] = -1
            continue

        rmse = m.test(valid_ratings)
        rmses[params] = rmse

        f = open(log_file, 'a')
        f.write('RMSE: {0}\n'.format(rmse))
        f.write('D: {0} Lambda: {1} Nu: {2} I: {3}\n\n'.format(*params))
        f.close()

    for k, v in sorted(rmses.items(), key=lambda i: i[1]):
        print '{0}: {1} '.format(k, v)

