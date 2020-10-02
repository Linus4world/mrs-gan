from torch.utils.data import DataLoader
from data.base_data_loader import BaseDataLoader

class CustomDatasetDataLoader(BaseDataLoader):
    def name():
        return 'CustomDatasetDataLoader'

    def initialize(self, opt):
        BaseDataLoader.initialize(self, opt)
        self.dataset = self.createDataset(opt)

        self.dataloader = DataLoader(self.dataset,
                                        batch_size=opt.batchSize,
                                        shuffle=opt.shuffle,   # Already included when the dataset is split
                                        num_workers=int(opt.nThreads),
                                        drop_last=False)

    def createDataset(opt):
        dataset = None
        if opt.dataset_mode == 'unaligned':
            from data.unaligned_dataset import UnalignedDataset
            dataset = UnalignedDataset()
        elif opt.dataset_mode == 'dicom_spectral_dataset':
            from data.dicom_spectral_dataset import DicomSpectralDataset
            dataset = DicomSpectralDataset()
        else:
            raise ValueError("Dataset [%s] not recognized." % opt.dataset_mode)

        dataset.initialize(opt)
        print("dataset [%s] was created" % (dataset.name()))
        return dataset

    def load_data(self):
        return self.dataloader

    def __len__(self):
        return min(len(self.dataset), self.opt.max_dataset_size)
