import sqlite3
import md5

def anon_db(s_db, d_db, s_table, d_table):
    source_conn = sqlite3.connect(s_db)
    dest_conn = sqlite3.connect(d_db)
    with source_conn, dest_conn:
        scur = source_conn.cursor()
        dcur = dest_conn.cursor()

        # Create dest table
        dcur.execute('DROP TABLE IF EXISTS {0}'.format(d_table))
        dcur.execute('''CREATE TABLE {0} (
                        user_id TEXT NOT NULL,
                        anime_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        score INT)'''.format(d_table))

        scur.execute('SELECT DISTINCT user_name FROM {0}'.format(s_table))
        user_rows = scur.fetchall()
        user_hash_dict = {}
        for r in user_rows:
            m = md5.new()
            m.update(r[0])
            user_hash_dict[r[0]] = m.hexdigest()

        scur.execute('SELECT user_name, anime_name, status, score FROM {0}'.format(s_table))
        rows = scur.fetchall()
        cntr = 0
        for r in rows:
            dcur.execute('INSERT INTO {0} VALUES(?,?,?,?)'.format(d_table),
                    [user_hash_dict[r[0]], r[1], r[2], r[3]])
            cntr += 1
            if cntr % 50000 == 0:
                dest_conn.commit()
                print cntr

