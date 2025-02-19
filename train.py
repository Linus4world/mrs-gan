import os
import sys
from models.auxiliaries.mrs_physics_model import MRSPhysicsModel
import time
from util.validator import Validator
from options.train_options import TrainOptions
from data.data_loader import CreateDataLoader
from models.models import create_model
from util.visualizer import Visualizer
from util.visdom import Visdom

opt = TrainOptions().parse()
if not opt.quiet:
    print('------------ Creating Training Set ------------')
pysicsModel = MRSPhysicsModel(opt)

data_loader = CreateDataLoader(opt, 'train')     # get training options
train_set = data_loader.load_data()       # create a dataset given opt.dataset_mode and other options
dataset_size = len(data_loader)         # get the number of samples in the dataset.
if not opt.quiet:
    print('training spectra = %d' % dataset_size)
    print('training batches = %d' % len(train_set))

val_set = CreateDataLoader(opt, 'val').load_data()

model = create_model(opt, pysicsModel)       # create a model given opt.model and other options
latest_path = os.path.join(model.save_dir, 'latest')
best_path = os.path.join(model.save_dir, 'best')
best_score = sys.maxsize
if opt.continue_train:
    model.load_checkpoint(latest_path)
visualizer = Visualizer(opt)    # create a visualizer that display/save images and plots
visdom = Visdom(opt)

total_iters = 0                 # the total number of training iterations
t_data = 0

validator = Validator(opt)

if not opt.quiet:
    print('------------- Beginning Training -------------')
for epoch in range(opt.epoch_count, opt.n_epochs + opt.n_epochs_decay + 1):
    print('>>>>> Epoch: ', epoch)
    epoch_start_time = time.time()  # timer for entire epoch
    iter_data_time = time.time()    # timer for data loading per iteration
    epoch_iter = 0                  # the number of training iterations in current epoch, reset to 0 every epoch
    visdom.reset()              # reset the visualizer: make sure it saves the results to HTML at least once every epoch
    # Loads batch_size samples from the dataset
    for i, data in enumerate(train_set):
        iter_start_time = time.time()  # timer for computation per iteration

        total_iters += opt.batch_size
        epoch_iter += opt.batch_size
        model.set_input(data)         # unpack data from dataset and apply preprocessing
        # Only update critic every n_critic steps
        optimize_gen = not(i % opt.n_critic)
        model.optimize_parameters(optimize_G=optimize_gen)   # calculate loss functions, get gradients, update network weights

        if total_iters % opt.print_freq == 0:    # print training losses and save logging information to the disk
            t_data = iter_start_time - iter_data_time
            losses = model.get_current_losses()
            t_comp = (time.time() - iter_start_time) / opt.batch_size
            visualizer.print_current_losses(epoch, epoch_iter, losses, t_comp, t_data, total_iters)
            
        if total_iters % opt.plot_freq == 0:
            visualizer.plot_current_losses()
            visualizer.save_smooth_loss()

        if total_iters % opt.save_latest_freq == 0:   # cache our latest model every <save_latest_freq> iterations
            # if opt.val_path:
            opt.phase = 'val'
            avg_abs_err, err_rel, avg_err_rel, r2 = validator.get_validation_score(model, val_set, num_batches=20)
            visualizer.plot_current_validation_score(avg_err_rel, total_iters)
            if best_score > sum(avg_err_rel):
                best_score = sum(avg_err_rel)
                model.create_checkpoint(best_path)

            avg_abs_err, err_rel, avg_err_rel, r2 = validator.get_validation_score(model, train_set, num_batches=20)
            visualizer.plot_current_training_score(avg_err_rel, total_iters)
            opt.phase = 'train'
            print('saving the latest model (epoch %d, total_iters %d)' % (epoch, total_iters))
            model.create_checkpoint(latest_path)
            visdom.display_current_results(model.get_current_visuals(), epoch, True)

        model.set_input(data)
        iter_data_time = time.time()

    # visdom.display_current_results(model.get_current_visuals(), epoch, True)

    model.update_learning_rate()    # update learning rates in the end of every epoch.

    if epoch % opt.save_epoch_freq == 0:              # cache our model every <save_epoch_freq> epochs
        print('saving the model at the end of epoch %d, iters %d' % (epoch, total_iters))
        model.create_checkpoint(latest_path)
        model.create_checkpoint(os.path.join(model.save_dir, str(epoch)))

    print('End of epoch %d / %d \t Time Taken: %d sec' %
          (epoch, opt.n_epochs + opt.n_epochs_decay, time.time() - epoch_start_time))

# if opt.val_path:
opt.phase = 'val'
avg_abs_err, err_rel, avg_err_rel, r2 = validator.get_validation_score(model, val_set)
visualizer.plot_current_validation_score(avg_abs_err, total_iters)
if best_score > sum(avg_err_rel):
    best_score = sum(avg_err_rel)
    model.create_checkpoint(best_path)
avg_abs_err, err_rel, avg_err_rel, r2 = validator.get_validation_score(model, train_set)
visualizer.plot_current_training_score(avg_abs_err, total_iters)
opt.phase = 'train'
model.create_checkpoint(latest_path)