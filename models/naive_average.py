import numpy as np

from collections import defaultdict

class NaiveAverageModel:

    def __init__(self, train_ratings):
        self.train_ratings = train_ratings

    def train(self):
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
        diff_totals = defaultdict(int)
        total_squared_error = 0

        for rating in test_ratings:
            guess = self.item_ratings.get(rating.item)
            if guess is None:
                diff_totals[100] += 1
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

