# Anime Recommender System project for EECS 445


## MyAnimeList User Scores database

### Database used

For simplicity, I'm currently using sqlite3 for the database for the
scores.

The full training, validation, and test sets are available in the
database file
[here](https://mega.nz/#!Ch1kiZYI!94NUzFEc62QojCINUhm-GTCYXECaQqZCXFJsItNYfOE).
This data set should be used for getting the final results for our dataset.

A database with a smaller training, validation, and test set is
available in `small_rating_sets.db`. This database can be used to test
models to make sure they are working correctly.

For using the sqlite3 database in python,
[here](http://zetcode.com/db/sqlitepythontutorial/) is a tutorial, and
[here](https://docs.python.org/2/library/sqlite3.html) is the
documentation for the DB-API inferface.


### User scores table format

The Ratings tables in our databases have three columns: user\_id,
anime\_name, and score.

- user\_id - A string containing the md5 hash of a username from MAL.
  This is hashed to anonymize the user.

- anime\_name - A string containing the name of the anime rated by the
user.

- score - An integer of the score the user gave for this anime. The
  score can be any number between 1 and 10.
