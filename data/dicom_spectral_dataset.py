import os
import os.path
import numpy as np
from torch import from_numpy

from data.base_dataset import BaseDataset

index = {'train': 0, 'val': 1, 'test': 2}

class DicomSpectralDataset(BaseDataset):
    """
    DicomSpectralDataset loads spectra from .dat files and returns a sample as a numpy array
    """
    def initialize(self, opt):
        self.opt = opt
        self.root = opt.dataroot
        if opt.real:
            self.channel_index = 0 
        elif opt.imag:
            self.channel_index = 1
        else:
            self.channel_index = None

        if self.opt.phase == 'val':
            return self.init_val(opt)

        self.dir_A = os.path.join(opt.dataroot, opt.phase + 'A')
        self.dir_B = os.path.join(opt.dataroot, opt.phase + 'B')

        sizes_A = np.genfromtxt(os.path.join(self.root,'sizes_A') ,delimiter=',').astype(np.int64)
        sizes_B = np.genfromtxt(os.path.join(self.root,'sizes_B') ,delimiter=',').astype(np.int64)

        path_A = str(os.path.join(self.root, self.opt.phase + '_A.dat'))
        path_B = str(os.path.join(self.root, self.opt.phase + '_B.dat'))

        self.A_size = sizes_A[index[self.opt.phase]]
        self.B_size = sizes_B[index[self.opt.phase]]

        self.sampler_A = np.memmap(path_A, dtype='double', mode='r', shape=(self.A_size,sizes_A[4],sizes_A[3]))
        self.sampler_B = np.memmap(path_B, dtype='double', mode='r', shape=(self.B_size,sizes_B[4],sizes_B[3]))
        self.counter=0
        print('Dataset sampler loaded')

    def init_val(self, opt):
        self.letter = 'A' if opt.AtoB else 'B'
        self.dir = os.path.join(opt.dataroot, opt.phase + self.letter)
        sizes = np.genfromtxt(os.path.join(self.root,'sizes_' + self.letter) ,delimiter=',').astype(np.int64)

        path = str(os.path.join(self.root, self.opt.phase + '_{0}.dat'.format(self.letter)))
        self.size = sizes[index[self.opt.phase]]
        self.sampler = np.memmap(path, dtype='double', mode='r', shape=(self.size,sizes[4],sizes[3]))
        self.counter=0
        print('Dataset sampler loaded')

    def __getitem__(self, index):
        # 'Generates one sample of data'
        if self.opt.phase != 'val':
            if self.channel_index is not None:
                A = np.expand_dims(np.asarray(self.sampler_A[index % self.A_size,self.channel_index,:]).astype(float),0)
                B = np.expand_dims(np.asarray(self.sampler_B[index % self.B_size,self.channel_index,:]).astype(float),0)
            else:
                A = np.asarray(self.sampler_A[index % self.A_size,:,:]).astype(float)
                B = np.asarray(self.sampler_B[index % self.B_size,:,:]).astype(float)
            return {
                'A': from_numpy(A),
                'B': from_numpy(B),
                'A_paths': '{:03d}.foo'.format(index % self.A_size),
                'B_paths': '{:03d}.foo'.format(index % self.B_size)
            }
        else:
            if self.channel_index is not None:
                data = np.expand_dims(np.asarray(self.sampler[index % self.size,self.channel_index,:]).astype(float),0)
            else:
                data = np.asarray(self.sampler[index % self.size,:,:]).astype(float)
            return {
                self.letter: from_numpy(data),
                'A_paths': '{:03d}.foo'.format(index % self.size)
            }

    def __len__(self):
        if self.opt.phase is not 'val':
            return max(self.A_size, self.B_size) # Determines the length of the dataloader
        else:
            return self.size

    def name(self):
        return 'DicomSpectralDataset'
