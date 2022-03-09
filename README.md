# Post-processing of reference discharges from MGB-AS to BHO5K (2017)

Current capabilities:
- calculate mean discharge and Q95 from MGB-AS outputs
- "downscale" to ANA's Base Hidrografica Ottocodificada (BHO 2017 5K)

## Required MGB-AS output files
- discharge binary (e.g. "QTUDO.BIN")
- local runoff binary (e.g. "QITUDO.BIN" or "QCEL.BIN")

## 1. Download files

- [mgb-bho-ds repository](https://github.com/minovsor/mgb-bho-ds/archive/refs/heads/main.zip)
- [Base Hidrografica Ottocodificada Multiescalas 2017 5k](https://metadados.snirh.gov.br/files/f7b1fc91-f5bc-4d0d-9f4f-f4e5061e5d8f/geoft_bho_2017_5k_trecho_drenagem.gpkg)
- [recommended:  pre-processed files at @... (to skip step 3.2)](TODO: insert link googledrive)

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
Use the following commands/scripts OR run through your favorite IDE (e.g. Spyder)

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

### 3.3 Run extraction of reference discharges and export geopackage
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


---
### (Best practice) Do a quick check of inputs and filepaths in .py files, for instance:
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

---
### (Other scripts) Utilities
```bash
# update fields for products.
python version_field_update.py
```


---
### (Experimental) Extract time series
```bash
python mgbbhods_solver_timeseries.py
```
