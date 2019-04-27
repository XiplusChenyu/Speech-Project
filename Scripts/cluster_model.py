import torch.nn as nn
import torch
from data_loader import test_loader
from config import PARAS
torch.manual_seed(1)


class Model(nn.Module):
    def __init__(self, feature=150, hidden_size=500, embedding_dim=20):
        super(Model, self).__init__()
        self.embedding_dim = embedding_dim

        self.blstm = nn.LSTM(input_size=feature,
                             hidden_size=hidden_size,
                             num_layers=4,
                             batch_first=True,
                             dropout=0.4,
                             bidirectional=True)

        self.embedding = nn.Linear(
            hidden_size * 2,
            PARAS.N_MEL * embedding_dim,
        )

        self.activation = nn.Tanh()

    @staticmethod
    def l2_normalize(x, dim=0, eps=1e-12):
        assert (dim < x.dim())
        norm = torch.norm(x, 2, dim, keepdim=True)
        return x / (norm + eps)

    def forward(self, inp):
        # batch, seq, feature
        out, _ = self.blstm(inp)
        out = self.embedding(out)
        out = self.activation(out)

        out = out.view(PARAS.BATCH_SIZE, -1, self.embedding_dim)
        # batch, TF, embedding

        # normalization over embedding dim
        out = self.l2_normalize(out, -1)

        return out


D_model = Model()

if __name__ == '__main__':
    print(D_model)
    from utils import loss_function_dc

    for _index, data in enumerate(test_loader):
        spec_input = data['mix']
        label = data['target']

        if PARAS.CUDA:
            spec_input = spec_input.cuda()
            label = label.cuda()

        with torch.no_grad():

            predicted = D_model(spec_input)
            shape = label.size()
            label = label.view((shape[0], shape[1]*shape[2], -1))
            print(loss_function_dc(predicted, label))

        break