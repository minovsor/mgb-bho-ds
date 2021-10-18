# MGB-BHO-DownScaling for the MGB-South America

Guidelines to extract mean discharge and Q95 from MGB-AS simulations to the ANA's Base Hidrografica Ottocodificada (BHO 2017 5K)


## 1. Download files

- mgb-bho-ds repository (https://github.com/minovsor/mgb-bho-ds/archive/refs/heads/main.zip)
- geoft_bho_2017_5k_trecho_drenagem.gpkg (Base Hidrografica Ottocodificada Multiescalas 2017 5k) at https://metadados.snirh.gov.br
- recommended:  pre-processed files at @... (to skip step 3.2)

## 2. Setup
Use your favorite python 3.7+ environment/IDE. I like Spyder!

Required packages:
```bash
matplotlib numpy pandas geopandas fiona openpyxl
```

(Example) Setting environment with Miniconda/Anaconda
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

### 3.2 (Advanced) Pre-processing
Recommended: download optional pre-processed files (MGB-SA -> BHO5k2017 compatible) and skip to 3.3
```bash
python mgbbhods_0_prepro.py
python mgbbhods_1_matlab.py
python mgbbhods_2_main.py
```

### 3.3 Extract discharge stats and export geopackage
```bash
python mgbbhods_solver_base.py
```

---
### (Advanced) Customize defaults for your MGB-AS version
Two-steps to adapt the downscaling to a customized MGB-AS version:
 1. Update mgb info at mgbsa_default at funcs_solver.py
```bash
def mgbsa_default(version = '1979'):
    """ Default settings for MGB-SA """
    if version == '1990':
        nc = 33749
        nt = 7305
        dstart = datetime(1990,1,1)
        file_qtudo = 'QTUDO_1990.MGB'
        file_qcel  = 'QITUDO_1990.MGB'
     
     # customized version
     if version == 'custom':
        nc = 33749  #number of mgb catchments
        nt = 7305   #number of time steps 
        dstart = datetime(1990,1,1)
        file_qtudo = 'QTUDO_CUSTOM.MGB'
        file_qcel  = 'QITUDO_CUSTOM.MGB'
      ...
```
2. Update argument at mgbbhods_solver_base.py
```bash
version = 'custom'
nt, nc, dstart, file_qtudo, file_qcel = funcs_solver.mgbsa_default(version)
...
```


### (Experimental) Extract time series
```bash
python mgbbhods_solver_timeseries.py
```

---
### (Best practise) Check inputs and filepaths in .py, for instance:
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


