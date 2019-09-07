from sklearn.base import RegressorMixin
from sklearn.compose import TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from skorch import NeuralNetRegressor
from .singlepredictor import SinglePredictor

def get_neuralnetregressor(model):
    """Unpack model to get skorch's NeuralNetRegressor"""

    if isinstance(model, SinglePredictor):
        return get_neuralnetregressor(model.model)
    if isinstance(model, Pipeline):
        for stepname, stepmodel in model.named_steps.items():
            if isinstance(stepmodel, RegressorMixin):
                return get_neuralnetregressor(stepmodel)
        raise ValueError("Could not find neural network in model", model)
    if isinstance(model, TransformedTargetRegressor):
        return get_neuralnetregressor(model.regressor)
    if isinstance(model, NeuralNetRegressor):
        return model
    raise ValueError("Could not find Neural network in model", model)