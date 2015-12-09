import math
import random
import numpy as np

from collections import defaultdict

class LatentFactorModel:

    def __init__(self, train_ratings, total_factors, norm_factor,
                 learning_rate, iterations, use_biases=True):
        self.train_ratings = train_ratings
        self.total_factors = total_factors
        self.norm_factor = norm_factor
        self.learning_rate = learning_rate
        self.iterations = iterations
        self.use_biases = use_biases

        self.user_vectors = {}
        self.item_vectors = {}
        self.user_biases = {}
        self.item_biases = {}
        if use_biases:
            self.rating_average = self._get_item_rating_average()
        else:
            self.rating_average = 0

    def train(self):
        for i in xrange(1, self.iterations + 1):
            # Print progress
            if i % 5 == 0:
                print i
            #learning_rate = (
                    #float(start_learning_rate) /
                    #(1 + i * start_learning_rate))

            for rating in self.train_ratings:
                successful = self._update_model(rating)
                if not successful:
                    return False
        return True

    def test(self, test_ratings):
        diff_totals = defaultdict(int)
        total_squared_error = 0

        for rating in test_ratings:
            uv = self.user_vectors.get(rating.user)
            iv = self.item_vectors.get(rating.item)
            ub = self.user_biases.get(rating.user)
            ib = self.item_biases.get(rating.item)
            if uv is None or iv is None or ub is None or ib is None:
                diff_totals[100] += 1
                continue

            # Bound guess to be between [1, 10]
            guess = self.rating_average + ub + ib + np.dot(uv, iv)
            guess = min(10, max(1, guess))
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

    def _get_item_rating_average(self):
        item_ratings = defaultdict(int)
        item_totals = defaultdict(int)
        for rating in self.train_ratings:
            item_ratings[rating.item] += rating.score
            item_totals[rating.item] += 1
        for item in item_ratings:
            item_ratings[item] = float(item_ratings[item]) / item_totals[item]

        rating_total = sum(avg for item, avg in item_ratings.items())
        return rating_total / len(item_ratings)

    def _update_model(self, rating):
        user_vector = self._get_user_vector(rating.user)
        item_vector = self._get_item_vector(rating.item)
        if self.use_biases:
            user_bias = self._get_user_bias(rating.user)
            item_bias = self._get_item_bias(rating.item)
        else:
            user_bias = 0
            item_bias = 0

        # Determine gradient for parameters
        error = (rating.score - self.rating_average - user_bias -
                 item_bias - np.dot(user_vector, item_vector))
        userv_grad = (np.multiply(self.learning_rate,
            np.subtract(
                np.multiply(error, item_vector),
                np.multiply(self.norm_factor, user_vector)
            )
        ))
        itemv_grad = (np.multiply(self.learning_rate,
            np.subtract(
                np.multiply(error, user_vector),
                np.multiply(self.norm_factor, item_vector)
            )
        ))
        if self.use_biases:
            userb_grad = (self.learning_rate *
                    (error - self.norm_factor * user_bias))
            itemb_grad = (self.learning_rate *
                    (error - self.norm_factor * item_bias))

        # Update parameters
        user_vector = np.add(user_vector, userv_grad)
        item_vector = np.add(item_vector, itemv_grad)
        self.user_vectors[rating.user] = user_vector
        self.item_vectors[rating.item] = item_vector
        if self.use_biases:
            self.user_biases[rating.user] = user_bias + userb_grad
            self.item_biases[rating.item] = item_bias + itemb_grad

        # Things went wrong if NaNs are showing up, so break
        if any(np.isnan(item_vector)) or any(np.isnan(user_vector)):
            print 'NaN in vectors'
            return False
        return True

    def _make_random_vector(self, dimension):
        return [random.uniform(-1, 1) for i in xrange(dimension)]

    def _get_user_vector(self, user):
        user_vector = self.user_vectors.get(user)
        if user_vector is None:
            user_vector = self._make_random_vector(self.total_factors)
        return user_vector

    def _get_item_vector(self, item):
        item_vector = self.item_vectors.get(item)
        if item_vector is None:
            item_vector = self._make_random_vector(self.total_factors)
        return item_vector

    def _get_user_bias(self, user):
        user_bias = self.user_biases.get(user)
        if user_bias is None:
            user_bias = self._make_random_vector(1)[0]
        return user_bias

    def _get_item_bias(self, item):
        item_bias = self.item_biases.get(item)
        if item_bias is None:
            item_bias = self._make_random_vector(1)[0]
        return item_bias

