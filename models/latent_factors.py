import dill
import math
import os
import random
import numpy as np

from collections import defaultdict

class ModelException(Exception):
    pass


class LatentFactorModel:
    PICKLE_FILE_NAME = ('{imp}_{biases}_{total_factors}_{norm_factor}_'
                        '{learning_rate}_{iterations}')

    def __init__(self, train_ratings, total_factors, norm_factor,
                 learning_rate, max_iterations, use_biases=True,
                 implicit_feedback=None, only_neg=False,
                 pickle_dir='', pickle_freq=10):
        self.train_ratings = train_ratings
        self.total_factors = total_factors
        self.norm_factor = norm_factor
        self.start_learning_rate = learning_rate
        self.max_iterations = max_iterations
        self.use_biases = use_biases
        self.implicit_feedback = implicit_feedback
        self.only_neg = only_neg
        self.pickle_dir = pickle_dir
        self.pickle_freq = pickle_freq

        self.user_vectors = {}
        self.item_vectors = {}
        self.completed_iterations = 0

        if use_biases:
            self.user_biases = {}
            self.item_biases = {}
            self.rating_average = self._get_item_rating_average()
        else:
            self.rating_average = 0

        if implicit_feedback is not None:
            self.negative_imp_vectors = {}
            self.positive_imp_vectors = {}
            self._init_implicit_feedback()

    @classmethod
    def load_model(cls, file_path):
        return dill.load(open(file_path, 'rb'))

    def train(self):
        for i in xrange(self.completed_iterations + 1, self.max_iterations + 1):
            # Print progress
            print i
            #learning_rate = (
                    #float(self.start_learning_rate) /
                    #(1 + i * self.start_learning_rate))

            for rating in self.train_ratings:
                successful = self._update_model(rating, self.start_learning_rate)
                if not successful:
                    return False
            self.completed_iterations += 1

            # Periodically save the progress of the model by pickling this
            # object
            if i % self.pickle_freq == 0:
                self._pickle_model(i)
        return True

    def test(self, test_ratings):
        diff_totals = defaultdict(int)
        total_squared_error = 0

        for rating in test_ratings:
            uv = self.user_vectors.get(rating.user)
            iv = self.item_vectors.get(rating.item)
            if self.use_biases:
                ub = self.user_biases.get(rating.user)
                ib = self.item_biases.get(rating.item)
            else:
                ub = 0
                ib = 0
            if uv is None or iv is None or ub is None or ib is None:
                diff_totals[100] += 1
                continue

            # Bound guess to be between [1, 10]
            imp_uv = self._get_imp_user_vector(rating.user, uv)
            guess = self.rating_average + ub + ib + np.dot(imp_uv, iv)
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

    def predict(self, test_user, test_item):
        uv = self.user_vectors.get(test_user)
        iv = self.item_vectors.get(test_item)
        if self.use_biases:
            ub = self.user_biases.get(test_user)
            ib = self.item_biases.get(test_item)
        else:
            ub = 0
            ib = 0
        if uv is None or ub is None:
            raise ModelException('User ({0}) not in model'.format(test_user))
        if iv is None or ib is None:
            raise ModelException('Item ({0}) not in model'.format(test_item))

        imp_uv = self._get_imp_user_vector(test_user, uv)
        guess = self.rating_average + ub + ib + np.dot(imp_uv, iv)
        return guess

    def _pickle_model(self, training_iterations):
        file_name = self.PICKLE_FILE_NAME.format(
                imp=bool(self.implicit_feedback),
                biases=self.use_biases,
                total_factors=self.total_factors,
                norm_factor=self.norm_factor,
                learning_rate=self.start_learning_rate,
                iterations=training_iterations)
        file_path = os.path.join(self.pickle_dir, file_name)
        dill.dump(self, open(file_path, 'wb'), 2)

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

    def _init_implicit_feedback(self):
        self.user_imp_items = defaultdict(
                lambda: {'negative': [], 'positive': []})
        for imp in self.implicit_feedback:
            if imp.is_positive():
                self.user_imp_items[imp.user]['positive'].append(imp.item)
            else:
                self.user_imp_items[imp.user]['negative'].append(imp.item)

    def _update_model(self, rating, learning_rate):
        user_vector = self._get_user_vector(rating.user)
        item_vector = self._get_item_vector(rating.item)
        if self.use_biases:
            user_bias = self._get_user_bias(rating.user)
            item_bias = self._get_item_bias(rating.item)
        else:
            user_bias = 0
            item_bias = 0

        # Determine gradient for parameters
        imp_user_vector = self._get_imp_user_vector(rating.user, user_vector)
        error = (rating.score - self.rating_average - user_bias -
                 item_bias - np.dot(imp_user_vector, item_vector))
        userv_grad = (np.multiply(learning_rate,
            np.subtract(
                np.multiply(error, item_vector),
                np.multiply(self.norm_factor, user_vector)
            )
        ))
        itemv_grad = (np.multiply(learning_rate,
            np.subtract(
                np.multiply(error, user_vector),
                np.multiply(self.norm_factor, item_vector)
            )
        ))
        if self.use_biases:
            userb_grad = (learning_rate *
                    (error - self.norm_factor * user_bias))
            itemb_grad = (learning_rate *
                    (error - self.norm_factor * item_bias))

        # Update parameters
        user_vector = np.add(user_vector, userv_grad)
        item_vector = np.add(item_vector, itemv_grad)
        self.user_vectors[rating.user] = user_vector
        self.item_vectors[rating.item] = item_vector
        if self.use_biases:
            self.user_biases[rating.user] = user_bias + userb_grad
            self.item_biases[rating.item] = item_bias + itemb_grad

        self._update_imp_items(rating.user, error, learning_rate, item_vector)

        # Things went wrong if NaNs are showing up
        if any(np.isnan(item_vector)) or any(np.isnan(user_vector)):
            print 'NaN in vectors'
            return False
        return True

    def _get_imp_user_vector(self, user, user_vector):
        if self.implicit_feedback is None:
            return user_vector

        imp_items = self.user_imp_items.get(user)
        if imp_items is None:
            return user_vector
        imp_user_vector = user_vector

        if imp_items['negative']:
            neg_imp_total = np.zeros(self.total_factors)
            for neg_item in imp_items['negative']:
                item_vector = self.negative_imp_vectors.get(neg_item)
                if item_vector is None:
                    item_vector = self._make_random_vector(self.total_factors)
                    self.negative_imp_vectors[neg_item] = item_vector
                neg_imp_total = np.add(neg_imp_total, item_vector)
            neg_imp_total = np.multiply(neg_imp_total,
                    float(1) / np.sqrt(len(imp_items['negative'])))

            imp_user_vector = np.add(imp_user_vector, neg_imp_total)

        if imp_items['positive'] and not self.only_neg:
            pos_imp_total = np.zeros(self.total_factors)
            for pos_item in imp_items['positive']:
                item_vector = self.positive_imp_vectors.get(pos_item)
                if item_vector is None:
                    item_vector = self._make_random_vector(self.total_factors)
                    self.positive_imp_vectors[pos_item] = item_vector
                pos_imp_total = np.add(pos_imp_total, item_vector)
            pos_imp_total = np.multiply(pos_imp_total,
                    float(1) / np.sqrt(len(imp_items['positive'])))

            imp_user_vector = np.add(imp_user_vector, pos_imp_total)

        return imp_user_vector

    def _update_imp_items(self, user, error, learning_rate, item_vector):
        if self.implicit_feedback is None:
            return

        imp_items = self.user_imp_items.get(user)
        if imp_items is None:
            return

        if imp_items['negative']:
            neg_norm_factor = (
                    float(1) / np.sqrt(len(imp_items['negative'])))
            for neg_item in imp_items['negative']:
                neg_vector = self.negative_imp_vectors[neg_item]
                item_grad = (np.multiply(learning_rate,
                    np.subtract(
                        np.multiply(error * neg_norm_factor, item_vector),
                        np.multiply(self.norm_factor, neg_vector)
                    )
                ))
                self.negative_imp_vectors[neg_item] = np.add(neg_vector, item_grad)

        if imp_items['positive'] and not self.only_neg:
            pos_norm_factor = (
                    float(1) / np.sqrt(len(imp_items['positive'])))
            for pos_item in imp_items['positive']:
                pos_vector = self.positive_imp_vectors[pos_item]
                item_grad = (np.multiply(learning_rate,
                    np.subtract(
                        np.multiply(error * pos_norm_factor, item_vector),
                        np.multiply(self.norm_factor, pos_vector)
                    )
                ))
                self.positive_imp_vectors[pos_item] = np.add(pos_vector, item_grad)

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

