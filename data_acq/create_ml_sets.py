import sqlite3

from math import ceil, floor
from random import shuffle

class BadRatiosException(Exception):
    pass


def create_implicit_feedback_set(source_db_path, dest_db_path,
                                 ratings_table_name):
    imp_table_name = ratings_table_name + 'Imp'

    source_conn = sqlite3.connect(source_db_path)
    dest_conn = sqlite3.connect(dest_db_path)
    with source_conn, dest_conn:
        scur = source_conn.cursor()
        dcur = dest_conn.cursor()

        dcur.execute('DROP TABLE IF EXISTS {0}'.format(imp_table_name))
        dcur.execute('''CREATE TABLE {0} (
                       user_id TEXT NOT NULL,
                       anime_name TEXT NOT NULL,
                       status TEXT NOT NULL)'''.format(imp_table_name))

        scur.execute('''SELECT user_id, anime_name, status FROM {0}
                        WHERE score IS NULL'''.format(ratings_table_name))

        insert_into_table(dcur, imp_table_name, scur.fetchall())
        source_conn.commit()


def create_ml_sets(source_db_path, dest_db_path, ratings_table_name,
                   train_percent, valid_percent, max_users=None):
    """Splits the source rating data into a training, validation, and test set
    using the given ratios.

    train_percent and valid_percent should be floats between 0 and 1 that
    represent what percentage of the data should go into the training and
    validation sets respectively. The remaining data will then go into the test
    set. Therefore, train_percent + valid_percent must be less than 1.

    source_db_path - A string with the path to the source database.
    dest_db_paht - A string with the path to the destination database.
    ratings_table_name - The name of the table with all of the rating data in
                         the source database.
    max_users_to_use - If given, no more than this number of users will be used
                       from the source table when creating the ML tables.
    """
    if not (train_percent + valid_percent < 1.0):
        raise BadRatiosException(
                'train_percent + valid_percent is not less than 1')

    train_table_name = ratings_table_name + 'Train'
    valid_table_name = ratings_table_name + 'Valid'
    test_table_name = ratings_table_name + 'Test'

    source_conn = sqlite3.connect(source_db_path)
    dest_conn = sqlite3.connect(dest_db_path)
    with source_conn, dest_conn:
        scur = source_conn.cursor()
        dcur = dest_conn.cursor()

        # Create train, valid, and test tables
        init_ml_tables(dcur, train_table_name, valid_table_name,
                       test_table_name)

        scur.execute('SELECT DISTINCT user_id FROM {0}'.format(
            ratings_table_name))
        user_rows = scur.fetchall()
        if max_users is None:
            total_users = len(user_rows)
        else:
            total_users = min(max_users, len(user_rows))

        cntr = 0
        for user_row in user_rows[:total_users]:
            scur.execute('''SELECT user_id, anime_name, score FROM {0}
                            WHERE user_id=? and score IS NOT NULL'''.format(
                        ratings_table_name), user_row)
            user_ratings = scur.fetchall()
            total_ratings = len(user_ratings)

            # Randomly partition user scores between train, valid, and test sets
            shuffle(user_ratings)
            train_split = int(ceil(total_ratings * train_percent))
            valid_split = train_split + int(floor(total_ratings * valid_percent))

            train_ratings = user_ratings[:train_split]
            insert_into_table(dcur, train_table_name, train_ratings)
            valid_ratings = user_ratings[train_split:valid_split]
            insert_into_table(dcur, valid_table_name, valid_ratings)
            test_ratings = user_ratings[valid_split:]
            insert_into_table(dcur, test_table_name, test_ratings)

            dest_conn.commit()
            cntr += 1
            if cntr % 50 == 0:
                print cntr

def init_ml_tables(cur, train_table_name, valid_table_name, test_table_name):
    cur.execute('DROP TABLE IF EXISTS {0}'.format(train_table_name))
    cur.execute('''CREATE TABLE {0} (
                   user_id TEXT NOT NULL,
                   anime_name TEXT NOT NULL,
                   score INT)'''.format(train_table_name))
    cur.execute('DROP TABLE IF EXISTS {0}'.format(valid_table_name))
    cur.execute('''CREATE TABLE {0} (
                    user_id TEXT NOT NULL,
                    anime_name TEXT NOT NULL,
                    score INT)'''.format(valid_table_name))
    cur.execute('DROP TABLE IF EXISTS {0}'.format(test_table_name))
    cur.execute('''CREATE TABLE {0} (
                   user_id TEXT NOT NULL,
                   anime_name TEXT NOT NULL,
                   score INT)'''.format(test_table_name))

def insert_into_table(cur, table_name, rows):
    row_format_list = ['(?']
    for i in xrange(1, len(rows[0])):
        row_format_list.append(',?')
    row_format_list.append(')')
    row_format_str = ''.join(row_format_list)

    for row in rows:
        cur.execute('INSERT INTO {0} VALUES{1}'.format(
                    table_name, row_format_str), row)

