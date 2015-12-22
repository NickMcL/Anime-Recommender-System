Anime Recommender System README

Main project contributor:
    Nick McLaughlin (mclaughn@umich.edu)

Other group members:
    Josh Visscher (joshviss@umich.edu)
    Josh Sauter (sauterj@umich.edu)
    Toshiki Sutisna Jahja (tsjahja@umich.edu)

Table of Contents:
    1. Project requirements
    2. Data sets
    3. Code used for data acquistion
    4. Code used for Recommender System models


1   PROJECT REQUIREMENTS

All of the code for this project was done with Python 2.7.6, so Python must be
installed to run the code for the project.

The code for the recommender system models for the project uses numpy, so numpy
must be installed to use the models. If you do not have numpy install already,
instructions for installing numpy can be found at
http://www.scipy.org/scipylib/download.html

The other required Python packages for running the code for the project are
listed in the requirements.txt file in the root directory for the project. The
requirements can be installed using pip with the following command:

$ pip install -r requirements.txt

If you do not have pip installed already, instructions for installing pip can
be found at https://pip.pypa.io/en/stable/installing/


2   DATA SETS

The data sets used in this project are stored in three sqlite3 databases. The
following gives details on each database. Also, each of these databases can be
downloaded from MBox here: https://umich.box.com/s/0plt2t6smwcv2jd2o8fj8art3ziekbwf

- MyAnimeList rating sets (mal_rating_sets.db)
This database contains the training, validation, and test sets of anime ratings
from MyAnimeList that were used for the project. The training set is in the
table 'MALRatingsTrain', the validation set is in the table 'MALRatingsValid',
and the test set is in the table 'MALRatingsTest'. Each of these tables has the
following three columns:

    - user_id - A string containing the MD5 hex digest of the username of a
      MyAnimeList user.
    - anime_name - A string containing the name of an anime rated by the user
      with user_id.
    - score - An integer between 1 and 10 that is the score given by the user
      with user_id on the anime named anime_name.

- MyAnimeList implicit feedback set (mal_imp_set.db)
This database contains anime that the MyAnimeList users in our MyAnimeList
rating sets did not rate but still gave some status for. This implicit feedback
data is in the table 'MALRatingsImp'. This table has the following three
colums:

    - user_id - A string containing the MD5 hex digest of the username of a
      MyAnimeList user.
    - anime_name - A string containing the name of an anime that the user
      with user_id did not rate but still gave some status for.
    - status - A string of the status given by the user with user_id on the
      anime named anime_name. Will be either 'Dropped', 'Completed',
      'Watching', or 'On-Hold'.

- Top-k test data set (topk_data.db)
This database contains the data needed to run the top-k test proposed by Yehuda
Koren in his "Factorization Meets the Neighborhood: a Multifaceted
Collaborative Filtering Model" paper. This data is in the table 'TopKTestData'.
Specifically, this table contains 1000 randomly selected anime for some of the
top rated anime for each user in the validation set in our MyAnimeList rating
sets. This table has the following three rows:

    - user_id - A string containing the MD5 hex digest of the username of a
      MyAnimeList user.
    - anime_name - A string containing the name of one of the anime that the
      user with user_id rated very highly.
    - rand_anime_name - A string containing the name of a randomly selected
      anime to be tested with the anime named anime_name for the user with
      user_id in the top-k test.


3   CODE USED FOR DATA ACQUISITION

All of the code dealing with acquiring anime rating data from MyAnimeList and
splitting the ratings into the various data sets used by our models can be
found in the data_acquistion directory in the root project directory.
Specifically, the code is contained in two files: crawl_mal.py and
create_ml_sets.py.

The crawl_mal.py file contains the functions used to crawl MyAnimeList to
collect public anime rating data. Specifically, the crawl_mal_ratings function
is used to initiate a crawling session that collects public anime rating data
from MyAnimeList into a database specified by the constant MAL_RATINGS_DB_NAME
in the file. The function can be used in the following manner in a Python shell
run in the root directory for the project:

>>> from data_acquisition.crawl_mal import crawl_mal_ratings
>>> crawl_mal_ratings(60, 1)
...

See the documentation within the crawl_mal.py file for more details on the
parameters and behavior of the crawl_mal_ratings function.

The create_ml_sets.py file contains functions for creating the data sets used
in the machine learning process for our models from the collected anime rating
data. This includes a function to split the data set into a training,
validation, and test set, a function to create the implicit data set, and a
function to create the top-k test data set. See the documentation for each
function within the create_ml_sets.py file for more details on the parameters
and behavior of these functions.


4   CODE USED FOR RECOMMENDER SYSTEM MODELS

All of the code used for our recommender system models can be found in the
models directory in the root project directory. We used these models with the
data sets specified in section 2 to produce all or the results specified in our
paper. The following steps can be used to train and test these models.

1. Load the data sets from the databases

Before the recommender system models can be trained, the training set,
validation set, test set, and implicit feedback data set must be loaded from
their databases into Python objects that the models can work with. The
model_util.py file contains two functions for handling this task:
get_ratings_from_db and get_implicit_feedback_from_db. Assuming that you have
downloaded the databases for the data sets and placed them in the root
directory for the project, these functions can be used in the following manner
in a Python shell run in the root directory for the project to load all of the
needed data sets:

>>> from models.model_util import *
>>> training_ratings = get_ratings_from_db('mal_rating_sets.db', 'MALRatingsTrain')
>>> validation_ratings = get_ratings_from_db('mal_rating_sets.db', 'MALRatingsValid')
>>> test_ratings = get_ratings_from_db('mal_rating_sets.db', 'MALRatingsTest')
>>> implicit_feedback = get_implicit_feedback_from_db('mal_imp_set.db', 'MALRatingsImp')

After running these commands, training_ratings will contain a list of the
rating data for the training set, validation_ratings will contain a list of
rating data for the validation set, test_ratings will contain a list of rating
data for the test set, and implicit_feedback will contain a list of implicit
feedback data from the data set. We will reference these data sets when
training and testing the models in the next steps.

2. Training a simple average model on the anime rating data set

The simple average model that we use as a baseline comparision for our latent
factors models in our paper can be trained and tested using the
SimpleAverageModel class in the simple_average.py file. Using the data sets
loaded in step 1, the simple average model can be trained and tested on the
anime rating data set in the following manner in a Python shell run in the root
directory for the project:

>>> from models.simple_average import *
>>> simple_average_model = SimpleAverageModel(training_ratings)
>>> simple_average_model.train()
True
>>> simple_average_model.test(test_ratings)
...

These commands will train a simple average model using our training set of
anime rating data followed by testing the model using our test set of anime
rating data. The test() method will print out the root mean square error of the
model on the test set as well as the distribution of the differences between
the model's predicted ratings and the test set ratings. For more details on the
behavior of the SimpleAverageModel, see the object in the simple_average.py
file.

3. Training our latent factors models on the anime rating data set

The various latent factors models that we gave the results for in our paper
were all trained and tested using the LatentFactorModel class in the
latent_factors.py file. This model has several adjustable parameters and
options. The documentation for the object in the latent_factors.py file gives
specific details on the different functions, parameters, and options for the
object, but we will just explain here how to train and test the final models
whose results we used in our paper.

WARNING: All of the latent factors models have a fairly long training time. In
particular, the latent factors model with biases and implicit feedback data
takes many hours to train on my machine. The train method will print out the
current iteration of stochastic gradient descent it is working on as it runs,
so you can look at the rate that iterations are completed and compare them to
the total iterations specified for the model to judge how long it will take
each model to train on your machine.

  3.1. Basic latent factors model

  After validating the model using the validation set of ratings, the best
  performing parameters we found for the basic latent factors model without
  biases or implicit feedback data were 150 latent factors, 0.1 normalizaition
  factor, 0.01 learning rate, and 200 total iterations. The basic latent
  factors model can be trained with these parameters and tested on the anime
  rating data set in the following manner in a Python shell run in the root
  directory for the project:

  >>> from models.latent_factors import *
  >>> basic_lf_model = LatentFactorModel(training_ratings, 150, 0.1, 0.01, 200, False)
  >>> basic_lf_model.train()
  ... (This will take a long time) ...
  >>> basic_lf_model.test(test_ratings)
  ...

  3.2. Latent factors model with biases

  After validating the model using the validation set of ratings, the best
  performing parameters we found for the latent factors model with biases but
  without implicit feedback data were 200 latent factors, 0.1 normalizaition
  factor, 0.01 learning rate, and 200 total iterations. The basic latent
  factors model can be trained with these parameters and tested on the anime
  rating data set in the following manner in a Python shell run in the root
  directory for the project:

  >>> from models.latent_factors import *
  >>> lf_bias_model = LatentFactorModel(training_ratings, 200, 0.1, 0.01, 200, True)
  >>> lf_bias_model.train()
  ... (This will take an even longer time) ...
  >>> lf_bias_model.test(test_ratings)
  ...

  3.3. Latent factors model with biases and implicit feedback data

  After validating the model using the validation set of ratings, the best
  performing parameters we found for the latent factors model with biases and
  implicit feedback data were 200 latent factors, 0.11 normalizaition factor,
  0.01 learning rate, and 300 total iterations. The basic latent factors model
  can be trained with these parameters and tested on the anime rating data set
  in the following manner in a Python shell run in the root directory for the
  project:

  >>> from models.latent_factors import *
  >>> lf_bias_imp_model = LatentFactorModel(training_ratings, 200, 0.11, 0.01, 300, True, implicit_feedback)
  >>> lf_bias_imp_model.train()
  ... (This will take a very long time) ...
  >>> lf_bias_imp_model.test(test_ratings)
  ...

For each of these models, the test() method will print out the root mean square
error of the model on the test set as well as the distribution of the
differences between the model's predicted ratings and the test set ratings.

4. Running Yehuda Koren's top-k test using our recommender system models

We implemented a function for running the top-k test proposed by Yehuda Koren
in his "Factorization Meets the Neighborhood: a Multifaceted Collaborative
Filtering Model" paper, but because of lack of space and because we felt it was
not as important of a result for the purpose of our investigation, we did not
include our results for it in our final paper.

Regardless, the top-k test can be run using the topk_test function in the
model_util.py file if you would like to see the results of it on our data.
Assuming that you have downloaded the database for the top-k data for our anime
rating data set and placed the database file in the root directory for the
project, this function can be used in the following manner in a Python shell
run in the root directory for the project:

>>> from models.model_util import *
>>> ranks, cummulative_prob_dist = topk_test('topk_data.db', 'TopKTestData', basic_lf_model, 1000)
... (The function will print how many anime it has completed the test for so far) ...

In this example, the basic latent factors model trained in step 3.1 is used for
the top-k test, but any of the latent factors models trained in step 3 or the
simple average model trained in step 2 can be used in that manner when passed
as a parameter to the function.

The function returns two lists after completing the test. The first list is an
ordered list of the possible ranks (between [0, 1]) in the top-k test, and the
second list is an ordered list of cummulative probabilities (between [0, 1])
that correspond to each rank in the first list. Comparing to the graph in
Koren's paper, the first list is the x-axis vales and the second list is the
y-axis values for the top-k test results, so these two lists can be used to
plot a graph of the results.

For more information on the top-k test, see the documentaiton for the topk_test
function in the model_util.py file and see the description of the test in
Koren's paper.
