# Objects for working with a simple average model.

import numpy as np
from collections import defaultdict

class ModelException(Exception):
    """Indicates that there was an error within the model"""
    pass


class SimpleAverageModel:
    """Object that encapsulates the parameters for a simple average model."""

    def __init__(self, train_ratings):
        self.train_ratings = train_ratings

    def train(self):
        """Trains the simple average model by finding the average rating for
        each item in the training ratings.

        Returns True if the training completed successfully, and returns False
        if the training could not be completed successfully because of some
        issue.
        """
        self.item_ratings = defaultdict(int)
        item_totals = defaultdict(int)
        for rating in self.train_ratings:
            self.item_ratings[rating.item] += rating.score
            item_totals[rating.item] += 1

        for item in self.item_ratings:
            self.item_ratings[item] = (
                    float(self.item_ratings[item]) / item_totals[item])
        return True

    def test(self, test_ratings):
        """Tests the simple average model against the given list of test
        ratings. Note that this function should only be called after the model
        has been trained.

        Prints out a summary of the root mean square error of the model on the
        test ratings as well as the distribution of the differences between the
        predicted ratings and the test ratings.

        Returns the root mean square error of the model on the test ratings.
        """
        diff_totals = defaultdict(int)
        total_squared_error = 0

        for rating in test_ratings:
            guess = self.item_ratings.get(rating.item)
            if guess is None:
                raise ModelException(
                        'Item ({0}) is not in the model'.format(test_item))
                continue

            total_squared_error += (rating.score - guess) ** 2
            diff = abs(rating.score - int(round(guess)))
            diff_totals[diff] += 1

        rmse = np.sqrt(float(total_squared_error) / len(test_ratings))
        print 'RMSE: {0}'.format(rmse)
        for k in sorted(diff_totals.keys()):
            print '{0}: {1} ({2})'.format(
                    k, diff_totals[k],
                    100 * (float(diff_totals[k]) / len(test_ratings)))
        return rmse

    def predict(self, test_user, test_item):
        """Predicts the score the given user would give the given item using
        the model. Note that this function should only be called after the
        model has been trained.

        Returns the predicted score which, in the case of the simple average
        model, is just the average rating given to the item in the train
        ratings.
        """
        guess = self.item_ratings.get(test_item)
        if guess is None:
            raise ModelException(
                    'Item ({0}) is not in the model'.format(test_item))
        return guess

