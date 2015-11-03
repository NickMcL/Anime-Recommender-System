# Anime Recommender System project for EECS 445


## MyAnimeList User Scores database

### Database used

For simplicity, I'm currently using sqlite3 for the database for the
scores. I might switch to a more heavy-duty database engine in the
future, but sqlite3 should be fine for now.

A sample of the database with around ~275 users and ~85,000 ratings is
stored in `data_acq/mal_users.db`.

For using the sqlite3 database in python,
[here](http://zetcode.com/db/sqlitepythontutorial/) is a tutorial, and
[here](https://docs.python.org/2/library/sqlite3.html) is the
documentation for the DB-API inferface.


### User scores table format

The MyAnimeList User Scores table has four columns: user\_name,
anime\_name, status, and score.

- user\_name - A string containing the name of a MyAnimeList user.

- anime\_name - A string containing the name of the anime rated by the
user.

- status - A string containing the current status of the user for this
  anime. It can be one of the following values:
  * Watching - The user is currently in the middle of watching this
    anime, but has not yet completed it.
  * Completed - The user has completed watching this anime.
  * On-Hold - The user has stalled watching this anime, but plans to
    start watching it again at a later time.
  * Dropped - The user stopped watching this anime before finishing it,
    and does not plan to start watching it again.

- score - An integer of the score the user gave for this anime. The
  score can be any number between 1 and 10. If the user did not score
  this anime, this field will be NULL.
