from argparse import Namespace
import numpy as np
import json

from models.cycleGAN import CycleGANModel
from data.data_loader import CreateDataLoader
from random_forest.random_forest import RandomForest


class Validator:
    """
    The Validator can validate a given cycleGAN model end to end by running a pretrained random forest on the generated fakes and computing the average relative error. 
    """
    def __init__(self, opt):
        self.opt = Namespace(**vars(opt))
        self.opt.phase = 'val'
        self.opt.batch_size=1
        print('------------ Creating Validation Set ------------')
        data_loader = CreateDataLoader(self.opt)     # get training options
        self.dataset = data_loader.load_data()       # create a dataset given opt.dataset_mode and other options
        self.dataset_size = len(data_loader)         # get the number of samples in the dataset.
        print('#test spectra = %d' % self.dataset_size)
        print('#test batches = %d' % len(self.dataset))

        label_path = self.opt.dataroot + '/labels.dat'
        with open(label_path, 'r') as file:
            params:dict = json.load(file)
            self.labels = list(params.keys())
            self.y_test =  np.transpose(np.array([params[k] for k in params]))
        self.rf = RandomForest(num_trees=100, labels= self.labels, load_from=self.opt.rf_path)

    def get_validation_score(self, model: CycleGANModel):
        """
        Compute the (average) relative error per metabolite for the given model.

        Parameters
        ----------
            - model: The current CycleGAN model

        Returns
        -------
            - The relative error per metabolite per fake. (MxN) with M=number of metabolites, N=number of fakes
            - The average relative error per metabolite. (M) with M=number of metabolites
        """
        fakes = []
        num_test = min(self.dataset_size, self.opt.num_test)
        for i, data in enumerate(self.dataset):
            if i>=num_test:
                break
            model.set_input(data)  # unpack data from data loader
            model.test()           # run inference
            fakes.append(model.get_fake().detach().squeeze(dim=0).cpu().numpy())
        fakes = np.squeeze(np.array(fakes))

        predictions = self.rf.test(fakes)
        err_rel, avg_err_rel = self.rf.compute_error(predictions, self.y_test[:num_test])
        return err_rel, avg_err_rel