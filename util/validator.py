from argparse import Namespace

from torch.utils.data.dataloader import DataLoader
from models.cycleGAN_WGP_REG import cycleGAN_WGP_REG
from util.util import compute_error
import numpy as np
import torch
import time

from data.data_loader import CreateDataLoader
from validation_networks.MLP.MLP import MLP


class Validator:
    """
    The Validator can validate a given cycleGAN model end to end by running a pretrained random forest on the generated fakes and computing the average relative error. 
    """
    def __init__(self, opt):
        if opt.phase != 'val':
            self.opt = Namespace(**vars(opt))
            self.opt.phase = 'val'
        else:
            self.opt = opt
        # self.opt.batch_size=1
        print('------------ Creating Validation Set ------------')
        data_loader = CreateDataLoader(self.opt)     # get training options
        self.dataset = data_loader.load_data()       # create a dataset given opt.dataset_mode and other options
        self.dataset_size = len(data_loader)         # get the number of samples in the dataset.
        if not opt.quiet:
            print('val spectra = %d' % self.dataset_size)
            print('val batches = %d' % len(self.dataset))

        self.num_test = min(self.dataset_size, self.opt.num_test*self.opt.batch_size)
        self.opt.num_test = int(self.num_test/self.opt.batch_size)

        # self.val_network = MLP(self.opt.val_path, gpu=self.opt.gpu_ids[0], in_out= (512, 2))
        # assert self.val_network.pretrained

    def get_validation_score(self, model: cycleGAN_WGP_REG, dataset: DataLoader = None):
        """
        Computes various validation metrics for the given model.

        Parameters
        ----------
            - model (CycleGAN): The current CycleGAN model
            - dataset (DataLoader): The dataset the validation samples should be taken from. If none is given, the configured validation set will be used. Default=None

        Returns
        -------
            - The Mean Absolute Error (L1) per metabolite. (M) with M=number of metabolites, N=number of test samples
            - The relative error per metabolite per fake. (MxN) with M=number of metabolites, N=number of test samples
            - The Average Relative Error per metabolite. (M) with M=number of metabolites
            - The Coefficient of Determination (R^2) pre metabolite. (M) with M=number of metabolites
        """
        # print('Validating', self.num_test, 'samples')
        start = time.time()
        fakes = []
        labels = []
        if dataset is None:
            dataset = self.dataset
        for i, data in enumerate(dataset):
            if i>=self.opt.num_test:
                break
            model.set_input(data)  # unpack data from data loader
            labels.append(data['label_A'])
            model.test()           # run inference
            fake = model.get_fake()
            # fake = torch.reshape(fake, (fake.shape[0] * fake.shape[1], *fake.shape[2:])).detach().cpu().numpy()
            fakes.append(fake)
        fakes = torch.cat(fakes)
        labels = torch.cat(labels)

        # predictions = self.val_network.predict(np.squeeze(fakes))
        predictions = np.array(fakes)
        labels = np.array(labels)
        avg_abs_err, err_rel, avg_err_rel, r2 = compute_error(predictions, labels)
        # print('prediction of', self.num_test, 'samples completed in {:.3f} sec'.format(time.time()-start))
        return avg_abs_err, err_rel, avg_err_rel, r2