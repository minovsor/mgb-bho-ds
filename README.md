# MGB-BHO-DownScaling for the MGB-South America

Guidelines to extract mean discharge and Q95 from MGB-AS simulations to the ANA's Base Hidrografica Ottocodificada (BHO 2017 5K)


## 1. Download files

- mgb-bho-ds repository
- Base Hidrografica Ottocodificada Multiescalas 2017 5k at https://metadados.snirh.gov.br
(geoft_bho_2017_5k_trecho_drenagem.gpkg)
- optional: pre-processed files at @...

## 2. Installation with conda

```bash
conda create --no-default-packages -n mgbbho python=3
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install matplotlib numpy pandas geopandas fiona openpyxl
```


## 3. Usage
Use the following commands or use your favorite IDE (e.g. Spyder/Pycharm, check ur environment)

### 3.1 Activate Environment 
```bash
conda activate mgbbho
```

### 3.2 Check inputs and filepaths
```bash
# main path
PATH_MAIN = './'
PATH_INPUT = PATH_MAIN + 'input/'

# table mgb topology
FILE_MINI = PATH_INPUT + 'mini.xlsx'

# geopackage BHO drainage
FILE_GDF_BHO = PATH_INPUT + 'geoft_bho_2017_5k_trecho_drenagem.gpkg'

# shapefile MGB
FILE_MGB_CATCHMENTS_SHP = PATH_INPUT + 'mgb_sa_unit_catchments_sirgas2000.shp'
```

### 3.3 Pre-processing (skip to 3.4 if you downloaded)
```bash
python mgbbhods_0_prepro.py
python mgbbhods_1_matlab.py
python mgbbhods_2_main.py
```

### 3.4 Extract stats and geopackage
```bash
python mgbbhods_solver_base.py
```

### 3.X Extract time series (experimental!)
```bash
python mgbbhods_solver_timeseries.py
