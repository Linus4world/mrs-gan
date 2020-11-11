# Script to train a random forest model to quantify the given number of metabolites of an MR spectrum.
# The model is trained on the given training set and validated on a given validation set.

from sklearn.ensemble import RandomForestRegressor
import numpy as np
import matplotlib.pyplot as plt
import os
import time
from joblib import dump, load

class RandomForest:
    """
    Create a multi regression random forest for the given labels.

    Parameters
    ---------
    - num_trees: Number of decision trees used in the random forest.
    - labels: List of metabolite names.
    """
    def __init__(self, num_trees, labels, load_from=None):
        # set random state to 0 for reproducability
        self.num_trees = num_trees
        self.labels = labels
        if load_from:
            self.load(load_from)
        else:
            self.regressor = RandomForestRegressor(n_estimators=num_trees, random_state=0)

    def train(self, x, y):
        """
        Train the random forest on the given dataset.
        Parameters
        ---------
        - x: List of spectra. N1 x L double, N1 = number of spectra, L length of spectra
        - y: List of quantifications. M x N2, M = number of metabolites, N2 = number of spectra
        """
        print('training random forest with {0} trees on {1} data samples...'.format(self.num_trees, len(x)))
        start = time.time()
        self.regressor.fit(x, y)
        print('training completed in {:.3f} sec'.format(time.time()-start))
            

    def store(self, filepath):
        print('storing random forest weights at', filepath)
        dump(self.regressor, filepath)

    def load(self, filepath):
        print('Loading pretrained model from', filepath)
        self.regressor = load(filepath)


    def test(self, x) -> list:
        """
        Test the random forest on the given dataset.
        Parameters
        ---------
        - x: List of spectra. N1 x L double, N1 = number of spectra, L length of spectra

        Returns
        -------
        prediction : The predicted values. N2 x M
        """
        start = time.time()
        prediction =  self.regressor.predict(x)
        print('prediction of', len(x), 'samples completed in {:.3f} sec'.format(time.time()-start))
        return np.array(prediction)

    def compute_error(self, predictions: list, y):
        """
        Compute the realtive errors and the average per metabolite

        Parameters
        ---------
        - predictions: List of predicted quantifications by the random forest
        - y: List of quantifications. N2xM, M = number of metabolites, N2 = number of spectra
        
        Returns
        -------
        - err_rel: List of relative errors. M x N2
        - avg_err_rel: Average relative error per metabolite. M x 1
        """
        err_rel = []
        avg_err_rel = []
        for metabolite in range(len(self.labels)):
            err_rel.append((abs(predictions[:,metabolite] - y[:,metabolite])) / (abs(y[:,metabolite])))
            avg_err_rel.append(np.mean(err_rel[metabolite]))
        return err_rel, avg_err_rel

    def save_plot(self, err_rel, avg_err_rel, path: str):
        """
        Save a boxplot from the given relative errors.

        Parameters
        ---------
        - err_rel: List of relative errors. M x N2
        - path: directory where the plot should be saved.
        """
        max_y = min(max(np.array(avg_err_rel)+0.15),1)
        if not hasattr(self, 'figure'):
            self.figure = plt.figure()
        else:
            plt.figure(self.figure.number)
        plt.boxplot(err_rel, notch = True, labels=self.labels)
        plt.ylabel('Relative Error')
        plt.title('Error per predicted metabolite')
        plt.gca().set_ylim([0,max_y])
        path = path+'_rel_err_boxplot.png'
        plt.savefig(path, format='png')
        plt.cla()
        print('Saved error plot at', path)

def train_val(x_train, x_test, y_train, y_test, labels, path, rf_path = None, num_trees=100):
    """
    Performs training and validation for the given dataset
    """
    if rf_path and os.path.isfile(rf_path):
        rf = RandomForest(num_trees, labels, rf_path)
    else:
        rf = RandomForest(num_trees, labels)
        rf.train(x_train, y_train)
        if rf_path:
            rf.store(rf_path)
        else:
            rf.store(path+'.joblib')
    predictions = rf.test(x_test)
    err_rel, avg_err_rel = rf.compute_error(predictions, y_test)
    for metabolite in range(len(avg_err_rel)):
        print('Average Relative Error {0}: {1}'.format(labels[metabolite], avg_err_rel[metabolite]))
    rf.save_plot(err_rel, avg_err_rel, path)