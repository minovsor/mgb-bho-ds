# MGB-BHO-DownScaling

Work in progress...

## Download files

## Installation with conda

```bash
conda create --no-default-packages -n mgbbho python=3
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install matplotlib numpy pandas geopandas fiona openpyxl
```

### Check filepaths 
PATH_MAIN = '../'
PATH_INPUT = PATH_MAIN + 'input/'
```python
# table mgb topology
FILE_MINI = PATH_INPUT + 'mini.xlsx'

# geopackage BHO drainage
FILE_GDF_BHO = PATH_INPUT + 'geoft_bho_2017_5k_trecho_drenagem.gpkg'

# shapefile MGB
FILE_MGB_CATCHMENTS_SHP = PATH_INPUT + 'mgb_sa_unit_catchments_sirgas2000.shp'
```python


## Usage
### Activate Environment
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
python mgbbhods_solver_timeseries.py
