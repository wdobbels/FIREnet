from pathlib import Path
import pickle
from .fullsetpredictor import FullSetPredictor
from .modelbuilder import create_uncertainty_loss
from .reguncpredictor import RegUncPredictor
from .singlepredictor import SinglePredictor
from .util import get_neuralnetregressor

class ModelStore:
    """Class for saving and loading ML models"""

    def __init__(self, savedir='./models/'):
        self.savedir = Path(savedir)
        if not self.savedir.exists():
            self.savedir.mkdir(parents=True)
        
    def store(self, model, name='nnet', stringify_loss=False, **meta_kwargs):
        """Save model to disk"""

        filename = self.savedir / name
        savefile = filename.with_suffix('.pkl')
        saveobj, callback = self._get_saveobj(model, stringify_loss, **meta_kwargs)
        # Store metafile
        with savefile.open('wb') as outf:
            pickle.dump(saveobj, outf)
        # Callback after save (e.g. unstringify loss)
        callback()

    def load(self, d_data, name='nnet', **kwargs):
        """Load model from disk. The training history is not saved/loaded."""

        savefile = self.savedir / f'{name}.pkl'
        with savefile.open('rb') as inf:
            saveobj = pickle.load(inf)
        classname = saveobj['classname']
        if classname == 'SinglePredictor':
            return self._load_singlepredictor(saveobj, d_data, **kwargs)
        elif classname == 'RegUncPredictor':
            return self._load_reguncpredictor(saveobj, d_data)
        elif classname == 'FullSetPredictor':
            fspred = FullSetPredictor(d_data)
            # Individual predictors are stored as saveobj['pred 0'] etc,
            # with saveobj['prednames'] = ['pred 0', 'pred 1', ...]
            for predname in saveobj['prednames']:
                pred = self._load_reguncpredictor(saveobj[predname], d_data)
                fspred.predictors.append(pred)
            return fspred
        else:
            ValueError("Invalid loaded classname", classname)

    @staticmethod
    def _get_saveobj(model, stringify_loss, **meta_kwargs):
        saveobj = meta_kwargs.copy()
        if isinstance(model, SinglePredictor):
            saveobj['classname'] = 'SinglePredictor'
            saveobj_pred, cb = ModelStore._get_saveobj_singlepredictor(
                            model, stringify_loss)
            saveobj.update(saveobj_pred)
        elif isinstance(model, RegUncPredictor):
            saveobj['classname'] = 'RegUncPredictor'
            saveobj_reg, cb_reg = ModelStore._get_saveobj_singlepredictor(
                                        model.reg, stringify_loss)
            saveobj_unc, cb_unc = ModelStore._get_saveobj_singlepredictor(
                                        model.unc, True)
            def cb():
                cb_reg()
                cb_unc()
            saveobj['reg'] = saveobj_reg
            saveobj['unc'] = saveobj_unc
        elif isinstance(model, FullSetPredictor):
            saveobj['classname'] = 'FullSetPredictor'
            li_cb = []
            li_prednames = []
            for i, predictor in enumerate(model.predictors):
                # Store individual predictors
                saveobj_pred, cb_pred = ModelStore._get_saveobj(predictor, stringify_loss)
                predname = f'pred {i}'
                saveobj[predname] = saveobj_pred
                li_cb.append(cb_pred)
                li_prednames.append(predname)
            saveobj['prednames'] = li_prednames
            def cb():
                for callback in li_cb:
                    callback()
        else:
            raise ValueError("Invalid model class", type(model))
        return saveobj, cb
        
    @staticmethod
    def _get_saveobj_singlepredictor(singlepredictor, stringify_loss):
        is_skorch_model = True
        try:
            nnet = get_neuralnetregressor(singlepredictor)
        except ValueError:  # Not a (standard) NeuralNetworkRegressor
            is_skorch_model = False
        if is_skorch_model:
            # Transform to CPU (can't load CUDA from non-CUDA device)
            nnet.module.cpu()
            nnet.device = 'cpu'
            if 'callbacks' not in nnet.cuda_dependent_attributes_:
                nnet.cuda_dependent_attributes_.append('callbacks')
            # Only save string version of criterion
            if stringify_loss:
                criterion = nnet.criterion_
                nnet.criterion_ = str(nnet.criterion_)
        saveobj = {'model': singlepredictor.model, 'stringify_loss': stringify_loss,
                    'idx_train': singlepredictor.X_train.index,
                    'idx_test': singlepredictor.X_test.index,
                    'correction_factor': singlepredictor.correction_factor}
        def callback():
            if stringify_loss and is_skorch_model:
                nnet.criterion_ = criterion
        return saveobj, callback

    @staticmethod
    def _load_reguncpredictor(saveobj, d_data):
        # Load regressor
        pred_reg = ModelStore._load_singlepredictor(saveobj['reg'], d_data, reg=True)
        # Load uncertainty estimator
        pred_unc = ModelStore._load_singlepredictor(saveobj['unc'], d_data, reg=False,
                                                    Y_pred=pred_reg.Y_pred)
        # Combine into RegUncPredictor
        pred = RegUncPredictor(d_data)
        pred.reg = pred_reg
        pred.unc = pred_unc
        return pred

    @staticmethod
    def _load_singlepredictor(saveobj, d_data, reg=True, Y_pred=None):
        pred = SinglePredictor(d_data, reg=reg)
        pred.preprocess(saveobj['idx_train'], saveobj['idx_test'],
                                   Y_pred=Y_pred)
        # Load model
        model = saveobj['model']
        if saveobj['stringify_loss']:
            ModelStore._unstringify_loss(model)
        pred.model = model
        pred.correction_factor = saveobj['correction_factor']
        # Set model predictions
        pred.Y_pred = pred.predict(pred.X)
        pred.Y_pred_train = pred.Y_pred.loc[pred.X_train.index, :]
        pred.Y_pred_test = pred.Y_pred.loc[pred.X_test.index, :]
        return pred

    @staticmethod
    def _unstringify_loss(model):
        nnet = get_neuralnetregressor(model)
        if 'create_uncertainty_loss' in nnet.criterion_:
            nnet.criterion_ = create_uncertainty_loss()
        else:
            raise ValueError(f"Unknown uncertainty loss '{nnet.criterion_}'")