from models.cycleGAN_spectra import CycleGAN_spectra
import torch
import torch.nn as nn
T = torch.Tensor

def wasserstein_distance(input):
    return torch.mean(input)

class CycleGAN_WGP(CycleGAN_spectra):
    """
    This class implements a CycleGAN model for learning 1d signal translation without paired data.
    The model training requires '--dataset_mode unaligned' dataset.
    By default, it uses a '--netG resnet_9blocks' ResNet generator,
    a '--netD basic' discriminator (PatchGAN introduced by pix2pix),
    and a least-square GANs objective ('--gan_mode lsgan').
    CycleGAN paper: https://arxiv.org/pdf/1703.10593.pdf
    """

    def name(self):
        return 'CycleGAN_WGP'

    def __init__(self, opt):
        opt.no_lsgan = False
        # TODO add option
        opt.clip_value = 0.01
        opt.lambda_gp = 10
        opt.gp = True
        super().__init__(opt)
        
    def backward_D_basic(self, netD: nn.Module, real: T, fake: T):
        """Calculate Wasserstein loss for the discriminator\n
            netD (network)      -- the discriminator D\n
            real (tensor array) -- real images\n
            fake (tensor array) -- images generated by a generator\n
        Return the discriminator loss.\n
        We also call loss_D.backward() to calculate the gradients.
        """
        # Real
        pred_real = netD.forward(real)
        loss_D_real = wasserstein_distance(pred_real)
        # Fake
        pred_fake = netD.forward(fake.detach())
        loss_D_fake = wasserstein_distance(pred_fake)

        if self.opt.gp:
            gradient_penalty = self.compute_gradient_penalty(netD, real, fake)
        else:
            gradient_penalty = 0

        # Combined wasserstein loss. Larger score for real images results in a larger resulting loss for the critic, penalizing the model
        loss_D = loss_D_real - loss_D_fake + self.opt.lambda_gp * gradient_penalty
        # backward
        loss_D.backward()
        return loss_D

    def backward_G(self):
        """Calculate the loss for generators G_A and G_B"""
        # Identity loss
        self.calculate_identity_loss()

        # GAN loss
        # D_A(G_A(A))
        self.loss_G_A = -wasserstein_distance(self.netD_A(self.fake_B))
        # D_B(G_B(B))
        self.loss_G_B = -wasserstein_distance(self.netD_B(self.fake_A))
        # Forward cycle loss
        self.loss_cycle_A: T = self.criterionCycle(self.rec_A, self.real_A) * self.lambda_A
        # Backward cycle loss
        self.loss_cycle_B: T = self.criterionCycle(self.rec_B, self.real_B) * self.lambda_B

        # combined wasserstein loss. Larger score from the critic will result in a smaller loss for the generator, encouraging the critic to output larger scores for fake images
        self.loss_G: T = self.loss_G_A + self.loss_G_B + self.loss_cycle_A + self.loss_cycle_B + self.loss_idt_A + self.loss_idt_B
        self.loss_G.backward()

    def clip_weights_D(self, opt):
        """ 
        Clip weights of discriminator to enforece Lipschitz continuity of the learned function f_w to compute the wasserstein distance.
        Used for standart Wasserstein GAN.
        Usage of gradient penalty is recommended.
        """
        for p in self.netD_A.parameters():
            p.data.clamp_(-opt.clip_value, opt.clip_value)
        for p in self.netD_B.parameters():
            p.data.clamp_(-opt.clip_value, opt.clip_value)

    def compute_gradient_penalty(self, D, real_samples, fake_samples):
        """Calculates the gradient penalty loss for WGAN GP"""
        # Random weight term for interpolation between real and fake samples
        alpha = torch.rand(real_samples.size(0), 1, 1)
        alpha = alpha.expand(real_samples.size()).cuda()
        
        # Get random interpolation between real and fake samples
        interpolates = (alpha * real_samples + ((1 - alpha) * fake_samples)).requires_grad_(True)
        d_interpolates = D(interpolates)
        fake = torch.autograd.Variable(torch.ones(d_interpolates.size()).fill_(1.0), requires_grad=False).cuda()
        # Get gradient w.r.t. interpolates
        gradients = torch.autograd.grad(
            outputs=d_interpolates,
            inputs=interpolates,
            grad_outputs=fake,
            create_graph=True,
            retain_graph=True,
            only_inputs=True,
        )[0]
        gradients = gradients.view(gradients.size(0), -1)
        gradient_penalty = ((gradients.norm(2, dim=1) - 1) ** 2).mean()
        return gradient_penalty

    def optimize_parameters(self, optimize_G=True, optimize_D=True):
        """Calculate losses, gradients, and update network weights; called in every training iteration"""
        super().optimize_parameters(optimize_G, optimize_D)
        if not self.opt.gp:
            self.clip_weights_D()
