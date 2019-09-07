"""
Helper functions to build (sklearn-compatible) predictors.
"""
import os
import torch
import skorch
from sklearn.compose import TransformedTargetRegressor
from sklearn.preprocessing import StandardScaler

ACTIVATIONS = {'sigmoid': torch.nn.Sigmoid(), 'relu': torch.nn.ReLU(),
               'elu': torch.nn.ELU(), 'selu': torch.nn.SELU(),
               'softplus': torch.nn.Softplus()}

def build_pytorch_nnet(arch, activation='relu', output_activation='linear',
                       pre_layers=None):
    '''
    Builds a sequential model from an architecture layout.
    Each layer except for the last one is followed by a ReLU.

    Parameters
    ----------

    arch : list, length n_layers - 1
        Each element gives the number of neurons in that layer. The first
        element is the number of expected inputs (input layer).

    pre_layers : list or None, default None
        The layers before this simple model building routine. Will be part
        of the final Sequential model.

    Returns
    -------

    model : torch.nn.modules.container.Sequential
        The pytorch model
    '''

    if pre_layers is None:
        layers = []
    else:
        layers = pre_layers
    for i in range(len(arch) - 1):
        layers.append(torch.nn.Linear(arch[i], arch[i+1]))
        if i != (len(arch) - 2):
            layers.append(ACTIVATIONS[activation])
        elif output_activation != 'linear':
            layers.append(ACTIVATIONS[output_activation])
    return torch.nn.Sequential(*layers)

def default_skorch_nnet(reg=True, insize=14, outsize=6, **kwargs):
    model = kwargs.pop('model', None)
    if model is None:
        hl_size = kwargs.pop('hidden_layer_sizes', [100, 100])
        activation = kwargs.pop('activation', 'relu')
        default_outact = 'linear' if reg else 'softplus'
        outact = kwargs.pop('outact', default_outact)
        model = build_pytorch_nnet([insize] + list(hl_size) + [outsize],
                                   output_activation=outact, activation=activation)
    kwargs.setdefault('lr', 1e-3)
    kwargs.setdefault('batch_size', 200)
    kwargs.setdefault('verbose', True)
    kwargs.setdefault('warm_start', True)
    kwargs.setdefault('optimizer', torch.optim.Adam)
    lr_policy = kwargs.pop('lr_policy', 'CosineAnnealingLR')
    lr_policy_kwargs = kwargs.pop('lr_policy_kwargs', {})
    lr_policy_kwargs.setdefault('T_max', 50)
    checkpoint = kwargs.pop('checkpoint', True)
    suff = 'reg' if reg else 'unc'
    f_param = kwargs.pop('checkpoint',
        f'./models/checkpoints/{suff}.pt')
    callbacks = [skorch.callbacks.LRScheduler(policy=lr_policy, **lr_policy_kwargs)]
    if checkpoint:
        if not os.path.isdir(os.path.dirname(f_param)):
            os.makedirs(os.path.dirname(f_param))
        # Disable saving history and optimizer state
        callbacks.append(skorch.callbacks.Checkpoint(f_params=f_param, f_history=None,
                                                     f_optimizer=None))
        callbacks.append(LoadCheckPointer(f_param))
    kwargs.setdefault('callbacks', callbacks)
    if reg:
        kwargs.setdefault('optimizer__weight_decay', 1e-4)
        kwargs.setdefault('max_epochs', 150)
    else:
        kwargs.setdefault('optimizer__weight_decay', 1)
        kwargs.setdefault('max_epochs', 50)
        kwargs.setdefault('criterion', create_uncertainty_loss)
    return skorch.NeuralNetRegressor(model, **kwargs)

def default_scaled_nnet(**skorchnet_kwargs):
    skorch_nnet = default_skorch_nnet(**skorchnet_kwargs)
    # Don't check inverse since we use float32, which can lead to
    # absolute differences of the order 1e-7 (leading to warnings).
    regr = TransformedTargetRegressor(regressor=skorch_nnet, transformer=StandardScaler(),
                                      check_inverse=False)
    return regr

class LoadCheckPointer(skorch.callbacks.Callback):
    """Class that loads the last checkpoint (i.e. best validation score) on train end."""

    def __init__(self, f_params="params.pt"):
        super(LoadCheckPointer, self).__init__()
        self.f_params = f_params

    def on_train_end(self, net, X, y):
        net.module_.load_state_dict(torch.load(self.f_params))

def create_uncertainty_loss():
    def softplus_loss(outputs, labels):
        '''
        Loss function: \sum [ (y_true - y_pred)^2 * z - ln(z)]
        
        z = 1 / V (see Gurevich & Stuke 2019) and (Dobbels et al. 2019) Eq. 2.
        We discard the factor 1/2, since it can be absorbed in the learning rate.

        Parameters
        ----------
            Outputs: z (= 1 / V)
            Labels: (y_true - y_pred)^2
        '''
        return torch.sum(labels*outputs - torch.log(outputs))
    return softplus_loss