# MGB-BHO-DownScaling

Work in progress...


## Installation with conda

```bash
conda create --no-default-packages -n mgbbho python=3
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install matplotlib numpy pandas geopandas fiona openpyxl
```


## Usage
```bash
conda activate mgbbho
```
### Pre-processing
```bash
python mgbbhods_0_prepro.py
python mgbbhods_1_matlab.py
python mgbbhods_2_main.py
```

### Extract stats and geopackage
```bash
python mgbbhods_solver_base.py
```

### Extract time series
```bash
python mgbbhods_s
