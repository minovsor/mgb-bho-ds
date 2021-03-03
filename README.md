# MGB-BHO-DownScaling

Em desenvolvimento

# Installation with conda

conda create --no-default-packages -n mgbbho python=3

conda config --add channels conda-forge

conda config --set channel_priority strict

conda install matplotlib numpy pandas geopandas fiona openpyxl

# Usage

# Pre-processing
mgbbhods_0_prepro.py

mgbbhods_1_matlab.py

mgbbhods_2_main.py

# Extract stats and geopackage
mgbbhods_solver_base.py

# Extract time series
mgbbhods_solver_timeseries.py
