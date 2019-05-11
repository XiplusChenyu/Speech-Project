import torch
import numpy as np
from sklearn.cluster import KMeans
from config import PARAS


def loss_function_simple(embedding, target):
    """
    Implement loss function
    :param embedding: N * TF * Embedding Dim
    :param target: N * TF * 1 (vocal)
    :return: Loss value for one batch N * scalar
    """

    def create_diag(target_m):
        """
        create dialog
        :param target_m: N * TF * 1 (vocal)
        :return: N * TF * TF
        """
        d_m = torch.bmm(target_m, torch.transpose(target_m, 1, 2))
        d_m = torch.sum(d_m, dim=2)  # notice there is batch
        d_m = torch.diag_embed(d_m)
        return torch.sqrt(d_m)

    def f2_norm(x):
        norm = torch.norm(x, 2)
        return norm ** 2

    diags = create_diag(target)
    n, tf, _ = embedding.shape
    part1 = f2_norm(torch.bmm(torch.bmm(torch.transpose(embedding, 1, 2), diags), embedding))
    part2 = f2_norm(torch.bmm(torch.bmm(torch.transpose(embedding, 1, 2), diags), target))
    part3 = f2_norm(torch.bmm(torch.bmm(torch.transpose(target, 1, 2), diags), target))

    return abs(part1 - 2 * part2 + part3) / (n*tf)


def loss_function(embedding, target):
    """
    This is the original function, which may need large GPU memory
    :param embedding: N * TF * Embedding Dim
    :param target: N * TF * 1 (vocal)
    :return: Loss value for one batch N * scalar
    """
    n, tf, _ = embedding.shape
    # ans = torch.bmm(embedding, torch.transpose(embedding, 1, 2)).sub(torch.bmm(target, torch.transpose(target, 1, 2)))
    loss1 = torch.bmm(torch.transpose(embedding, 1, 2), embedding)
    loss2 = torch.bmm(torch.transpose(target, 1, 2), target)
    loss3 = torch.bmm(torch.transpose(embedding, 1, 2), target)
    result = torch.sum(torch.norm(loss1, dim=(1, 2)) + torch.norm(loss2, dim=(1, 2)) - 2 * torch.norm(loss3, dim=(1, 2)))
    return result / PARAS.BATCH_SIZE


criterion = torch.nn.MSELoss()


def mask_scale_loss(mask: torch.Tensor, target: torch.Tensor):
    """
    This function returns the loss defined by intersection over union
    :param mask: the binary mask generated by model N * T * F * 2 (voice prob, background prob)
    :param target: the target should be N * T * F * 1
    :return: we should generate a IoU mask over the voice source
    """
    music_mask, _ = torch.unbind(mask, dim=3)  # split the output mask
    return criterion(mask, target)


def embedding_to_mask(embedding_out):
    """
    Convert embedding out as a binary mask
    :param embedding_out: tensor, TF * Embedding Dim
    :return: mask, which T * F
    """
    tmp = embedding_out.view((PARAS.N_MEL, PARAS.N_MEL, PARAS.E_DIM))
    tmp = tmp.numpy()
    tmp.resize((PARAS.N_MEL ** 2, PARAS.E_DIM))
    k_means_client = KMeans(n_clusters=2, random_state=0).fit(tmp)
    mask = k_means_client.labels_.copy()
    mask = np.resize(mask, (PARAS.N_MEL, PARAS.N_MEL))
    r_mask = np.ones(mask.shape) - mask
    return mask, r_mask

