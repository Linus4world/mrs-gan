
def create_model(opt, physicsModel=None):
    model = None
    if opt.model == 'cycleGAN':
        assert(opt.dataset_mode == 'dicom_spectral_dataset')
        from .cycleGAN import CycleGAN
        model = CycleGAN(opt)
    elif opt.model == 'cycleGAN_WGP':
        assert(opt.dataset_mode == 'dicom_spectral_dataset')
        from .cycleGAN_W import CycleGAN_W
        model = CycleGAN_W(opt)
    elif opt.model == 'cycleGAN_WGP_REG':
        assert(opt.dataset_mode == 'spectra_component_dataset')
        from .cycleGAN_W_REG import cycleGAN_WGP_REG
        model = cycleGAN_WGP_REG(opt, physicsModel)
    else:
        raise ValueError("Model [%s] not recognized." % opt.model)
    if not opt.quiet:
        print("model [%s] was created" % (model.name()))
    return model
