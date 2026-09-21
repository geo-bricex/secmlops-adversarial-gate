import torch
from torch import nn


class MLP(nn.Module):
    def __init__(self, input_dim: int, hidden_layers=(128, 64), dropout=0.2):
        super().__init__()
        layers = []
        previous = input_dim
        for width in hidden_layers:
            layers.extend([nn.Linear(previous, width), nn.ReLU(), nn.Dropout(dropout)])
            previous = width
        layers.append(nn.Linear(previous, 2))
        self.network = nn.Sequential(*layers)

    def forward(self, inputs):
        return self.network(inputs)

