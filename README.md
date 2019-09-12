# FIRE-net
Far-InfraRed Emission Networks (FIRE-net) is a machine learning framework that
aims to estimate the far-infrared (FIR) spectral energy distribution (SED) of a
galaxy, based on the ultraviolet to mid-infrared (UV-MIR) SED.

## >>> **Interactive plots** can be found **[here](https://wdobbels.github.io/FIREnet/)** <<<

This github repo provides the following:  
* jupyter notebooks that guide the process from raw data to a fully trained model
* a jupyter notebook that shows how to apply our fiducial model quickly
* a library of helper classes/functions
* the DustPedia + H-ATLAS SED fitted data (about 23 MB)

## Notebooks

If you want an example of how the neural networks are trained or used, see the jupyter notebooks in the `notebooks` directory. We recommend viewing them using [nbviewer](https://nbviewer.jupyter.org/github/wdobbels/FIREnet/tree/master/notebooks/), although they can be opened directly from github as well.

## Using the code locally

The environment that was used to run the notebooks can be built from the either
`environment.yml` (conda) or `environment.txt` (pip). We strongly recommend using
a "virtual environment": a separate python installation which does not interfere
with your base environment. Possible options are [conda](https://docs.conda.io/en/latest/),
[pipenv](https://pipenv-fork.readthedocs.io/en/latest/) or [virtualenv/venv](https://docs.python.org/3/library/venv.html).

[Jupyter lab](https://jupyterlab.readthedocs.io/en/stable/) is the recommended tool
to run the jupyter notebooks. You can install it in a separate environment 
(e.g. the base environment), and add your environment as separate kernel. In that case,
you can remove jupyterlab from `environment.yml`. Alternatively,
jupyter lab can be installed in the current environment and run from there.

For conda users:
```
conda env create -f environment.yml
conda activate firenet
jupyter lab
```

For pip users:
```
python3 -m venv firenet-env
source firenet-env/bin/activate
pip install -r requirements.txt
jupyter lab
```

Alternatively, manually install the missing packages from `environment.yml` into
your favourite machine learning environment.

## Citation

This work is accompanied by the paper *"Predicting the global far-infrared SED of galaxies via machine learning techniques"*. The paper will be linked here once accepted.