
def create_model(opt, physicsModel=None):
    model = None
    if opt.model == 'cycleGAN_PFL':
        assert(opt.dataset_mode == 'unaligned')
        from .cycleGAN_PFL import CycleGAN_PFL
        model = CycleGAN_PFL(opt)
    elif opt.model == 'cycleGAN_spectra':
        assert(opt.dataset_mode == 'dicom_spectral_dataset')
        from .cycleGAN_spectra import CycleGAN_spectra
        model = CycleGAN_spectra(opt)
    elif opt.model == 'cycleGAN_WGP':
        assert(opt.dataset_mode == 'dicom_spectral_dataset')
        from .cycleGAN_WGP import CycleGAN_WGP
        model = CycleGAN_WGP(opt)
    elif opt.model == 'cycleGAN_WGP_REG':
        assert(opt.dataset_mode == 'spectra_component_dataset')
        from .cycleGAN_WGP_REG import cycleGAN_WGP_REG
        model = cycleGAN_WGP_REG(opt, physicsModel)
    elif opt.model == 'cycleGAN_WSN':
        assert(opt.dataset_mode == 'dicom_spectral_dataset')
        from .cycleGAN_WSN import CycleGAN_WSN
        model = CycleGAN_WSN(opt)
    elif opt.model == 'cycleGAN_WGP_IFL':
        assert(opt.dataset_mode == 'dicom_spectral_dataset')
        from .cycleGAN_WGP_IFL import CycleGAN_WGP_IFL
        model = CycleGAN_WGP_IFL(opt)
    else:
        raise ValueError("Model [%s] not recognized." % opt.model)
    print("model [%s] was created" % (model.name()))
    return model
