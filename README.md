# MGB-BHO-DownScaling for the MGB-South America

Guidelines to extract mean discharge and Q95 from MGB-AS simulations to the ANA's Base Hidrografica Ottocodificada (BHO 2017 5K)


## 1. Download files

- mgb-bho-ds repository (https://github.com/minovsor/mgb-bho-ds/archive/refs/heads/main.zip)
- geoft_bho_2017_5k_trecho_drenagem.gpkg (Base Hidrografica Ottocodificada Multiescalas 2017 5k) at https://metadados.snirh.gov.br
- recommended:  pre-processed files at @... (to skip step 3.3)

## 2. Setup
Use your favorite python 3.7+ environment/IDE.
```bash
# required packages (nothing complicated)
matplotlib numpy pandas geopandas fiona openpyxl
```

## (Example) Setting environment with Miniconda/Anaconda
```bash
conda create --no-default-packages -n mgbbho python=3
conda config --add channels conda-forge
conda config --set channel_priority strict
conda install matplotlib numpy pandas geopandas fiona openpyxl
```


## 3. Usage
Use the following commands or use your favorite IDE (e.g. Spyder/Pycharm)

### 3.1 Activate Environment (or use your IDE)
```bash
conda activate mgbbho
```

### 3.2 Check inputs and filepaths in .py, for instance:
TODO: describe these in a .txt file
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

### 3.3 (Advanced) Pre-processing
Recommended: download optional pre-processed files (MGB-SA -> BHO5k2017 compatible) and skip to 3.4
```bash
python mgbbhods_0_prepro.py
python mgbbhods_1_matlab.py
python mgbbhods_2_main.py
```

### 3.4 Extract discharge stats and export geopackage
```bash
python mgbbhods_solver_base.py
```

### 3.X Extract time series (experimental!)
```bash
python mgbbhods_solver_timeseries.py
```

### (Advanced) Customize defaults for your MGB-AS version:
 - Update mgb info at mgbsa_default at funcs_solver.py
