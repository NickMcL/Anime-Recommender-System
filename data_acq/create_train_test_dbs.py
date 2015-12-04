import sqlite3

from math import ceil
from random import shuffle

TRAIN_SET_PERCENTAGE = 0.7


def create_train_test_dbs(db_path, score_table_name):
    train_table_name = score_table_name + 'Train'
    test_table_name = score_table_name + 'Test'

    conn = sqlite3.connect(db_path)
    with conn:
        cur = conn.cursor()

        # Create train and test tables
        cur.execute('DROP TABLE IF EXISTS {0}'.format(train_table_name))
        cur.execute('''CREATE TABLE {0} (
                        user_name TEXT NOT NULL,
                        anime_name TEXT NOT NULL,
                        score INT)'''.format(train_table_name))
        cur.execute('DROP TABLE IF EXISTS {0}'.format(test_table_name))
        cur.execute('''CREATE TABLE {0} (
                        user_name TEXT NOT NULL,
                        anime_name TEXT NOT NULL,
                        score INT)'''.format(test_table_name))

        cur.execute('SELECT DISTINCT user_name FROM {0}'.format(score_table_name))
        user_rows = cur.fetchall()
        cntr = 0
        for user_row in user_rows:
            cur.execute('''SELECT user_name, anime_name, score FROM {0}
                        WHERE user_name=? and score IS NOT NULL'''.format(
                        score_table_name), user_row)
            user_score_rows = cur.fetchall()

            # Partition user scores between train and test sets
            shuffle(user_score_rows)
            partition = int(ceil(len(user_score_rows) * TRAIN_SET_PERCENTAGE))
            train_score_rows = user_score_rows[:partition]
            insert_into_table(cur, train_table_name, train_score_rows)
            test_score_rows = user_score_rows[partition:]
            insert_into_table(cur, test_table_name, test_score_rows)

            cntr += 1
            if cntr % 50 == 0:
                print cntr
        conn.commit()


def insert_into_table(cur, table_name, rows):
    row_format_list = ['(?']
    for i in xrange(1, len(rows[0])):
        row_format_list.append(',?')
    row_format_list.append(')')
    row_format_str = ''.join(row_format_list)

    for row in rows:
        cur.execute('INSERT INTO {0} VALUES{1}'.format(
                    table_name, row_format_str), row)
