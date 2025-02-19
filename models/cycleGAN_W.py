from torch.nn.utils.spectral_norm import spectral_norm
from models.auxiliaries.physics_model_interface import PhysicsModel
from models.cycleGAN import CycleGAN
import torch
import models.auxiliaries.auxiliary as aux

class CycleGAN_W(CycleGAN):
    """
    This class implements a CycleGAN model for learning 1d signal translation without paired data,
    using the wasserstein loss function with gradient penalty.
    The model training requires '--dicom_spectral_dataset' dataset.
    """

    def name(self):
        return 'CycleGAN_WGP'

    def __init__(self, opt, physicsModel: PhysicsModel):
        opt.gan_mode = 'wasserstein'
        opt.clip_value = 0.01
        opt.beta1 = 0
        opt.beta2 = 0.9
        aux.weight_norm = spectral_norm
        super().__init__(opt, physicsModel)
        
    def backward_D_basic(self, netD, real, fake):
        """Calculate GAN loss for the discriminator

        Parameters:
            netD (network)      -- the discriminator D
            real (tensor array) -- real images
            fake (tensor array) -- images generated by a generator

        Return the discriminator loss.
        We also call loss_D.backward() to calculate the gradients.
        """
        # Real
        pred_real = netD.forward(real)
        loss_D_real = self.criterionGAN(pred_real, True)
        # Fake
        pred_fake = netD.forward(fake.detach())
        loss_D_fake = self.criterionGAN(pred_fake, False)

        if self.opt.weight_norm == 'gp':
            gradient_penalty = self.cal_gradient_penalty(netD,real,fake,'cuda')
        else: 
            gradient_penalty = 0
        # Combined loss and calculate gradients
        loss_D = 0.5 * (loss_D_real + loss_D_fake) + gradient_penalty
        loss_D.backward()
        return loss_D

    def clip_weights_D(self, opt):
        """ 
        DEPRECATED!
        Clip weights of discriminator to enforce Lipschitz continuity of the learned function f_w to compute the wasserstein distance.
        Used for standart Wasserstein GAN.
        Usage of gradient penalty is recommended.
        """
        for p in self.netD_A.parameters():
            p.data.clamp_(-opt.clip_value, opt.clip_value)
        for p in self.netD_B.parameters():
            p.data.clamp_(-opt.clip_value, opt.clip_value)

    def cal_gradient_penalty(self, netD, real_data, fake_data, device, constant=1.0, lambda_gp=10.0):
        """Calculate the gradient penalty loss, used in WGAN-GP paper https://arxiv.org/abs/1704.00028

        Arguments:
            netD (network)              -- discriminator network
            real_data (tensor array)    -- real images
            fake_data (tensor array)    -- generated images from the generator
            device (str)                -- GPU / CPU: from torch.device('cuda:{}'.format(self.gpu_ids[0])) if self.gpu_ids else torch.device('cpu')
            constant (float)            -- the constant used in formula ( ||gradient||_2 - constant)^2
            lambda_gp (float)           -- weight for this loss

        Returns the gradient penalty loss
        """
        if lambda_gp > 0.0:
            alpha = torch.rand(real_data.shape[0], 1, device=device)
            alpha = alpha.expand(real_data.shape[0], real_data.nelement() // real_data.shape[0]).contiguous().view(*real_data.shape)
            interpolatesv = alpha * real_data + ((1 - alpha) * fake_data)

            interpolatesv.requires_grad_(True)
            disc_interpolates = netD(interpolatesv)
            gradients = torch.autograd.grad(outputs=disc_interpolates, inputs=interpolatesv,
                                            grad_outputs=torch.ones(disc_interpolates.size()).to(device),
                                            create_graph=True, retain_graph=True, only_inputs=True)
            gradients = gradients[0].view(real_data.size(0), -1)  # flat the data
            gradient_penalty = (((gradients + 1e-16).norm(2, dim=1) - constant) ** 2).mean() * lambda_gp        # added eps
            return gradient_penalty
        else:
            return 0.0

    def optimize_parameters(self, optimize_G=True, optimize_D=True):
        """Calculate losses, gradients, and update network weights; called in every training iteration"""
        super().optimize_parameters(optimize_G, optimize_D)
        if self.opt.weight_norm == 'clip':
            self.clip_weights_D()
