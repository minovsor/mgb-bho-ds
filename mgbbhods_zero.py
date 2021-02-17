# -*- coding: utf-8 -*-
"""
Initial "Zero" step of the Downscaling Pre-processing

Saves 'table_t0.xlsx'   (inpolygon BHO points with MGB polygons)

@author: Mino Sorribas


"""

# standard python
import time
import pickle
from datetime import datetime,timedelta

# plotting, numpy, dataframes and spatial
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd

# downscaling
import funcs_io
import funcs_op



#-----------------------------------------------------------------------------
# INPUT PATHS AND FILES
#-----------------------------------------------------------------------------
print(" Initializing filepaths... ")

PATH_MAIN = '../'
PATH_INPUT = PATH_MAIN + 'input/'

# table mgb topology
FILE_MINI = PATH_INPUT + 'mini.xlsx'

# geopackage BHO drainage
FILE_GDF_BHO = PATH_INPUT + 'geoft_bho_2017_5k_trecho_drenagem.gpkg'

# shapefile MGB
FILE_MGB_CATCHMENTS_SHP = PATH_INPUT + 'mgb_sa_unit_catchments_sirgas2000.shp'


#-----------------------------------------------------------------------------
# OUTPUT FILES
#-----------------------------------------------------------------------------
# geopackage BHO points
FILE_BHO_INTER = 'bho_midpts.gpkg'



#-----------------------------------------------------------------------------
# LOAD TABLES
#-----------------------------------------------------------------------------
print(" Loading datatables and spatial data... ")

# table mgb topology
df_tble_mini = funcs_io.read_tble_mini(FILE_MINI)

# bho trechos (geodataframe)
gdf_tble_bho = funcs_io.read_gdf_bho(FILE_GDF_BHO)

# mgb catchments (shapefile)
gdf_mgb_catchments = gpd.read_file(FILE_MGB_CATCHMENTS_SHP)



#-----------------------------------------------------------------------------
# PRE-PROCESSING - IDENTIFY MGB DOMAIN INSIDE BHO (STEP ZERO)
#-----------------------------------------------------------------------------
print(" Pre-processing domain (MGB inside BHO)... ")

# obtain raw domain (bho inside mgb catchments) -> drop bho_midpts.gpkg and pickle.
dict_bho_domain = funcs_op.associate_bho_mini_domain(gdf_tble_bho,
                                                     gdf_mgb_catchments,
                                                     pts_to_gpkg = FILE_BHO_INTER,
                                                     )



gdf_tble_bho = gdf_tble_bho.drop('geometry',axis=1)

#... from now on, works with the table
#... and adopt 'df_tble_bho' as the variable name
#... thus, the next statement keeps the old object (same memory)
#    id(df_tble_bho)==id(gdf_tble_bho)
df_tble_bho = gdf_tble_bho


#-----------------------------------------------------------------------------
# MAKE INTERSECTION TABLE
#-----------------------------------------------------------------------------
print(" Make intersection table (adjusted for table 1 processing)... ")
df_bho_inter = funcs_op.make_tble_t0(df_tble_mini, df_tble_bho, FILE_BHO_INTER)


