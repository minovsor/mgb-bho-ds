# -*- coding: utf-8 -*-
"""
JOIN DOWNSCALED RESULTS TO SINGLE GPKG

@author:
"""

# standard python
import time
from datetime import datetime,timedelta

# plotting, numpy, dataframes and spatial
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd


#-----------------------------------------------------------------------------
# Main path and general input files
#-----------------------------------------------------------------------------
PATH_MAIN = './'
PATH_INPUT = PATH_MAIN + 'input/'

FILE_GDF_BHO = PATH_INPUT + 'geoft_bho_2017_5k_trecho_drenagem.gpkg'


#-----------------------------------------------------------------------------
# Results from downscale
#-----------------------------------------------------------------------------

df_ol = pd.read_excel('base_mgbbhods_flows_1979.xlsx',index_col = 0)

df_m02 = pd.read_excel('base_mgbbhods_flows_enkf_m02.xlsx',index_col = 0)

df_m25 = pd.read_excel('base_mgbbhods_flows_enkf_rev.xlsx',index_col = 0)

df_m48 = pd.read_excel('base_mgbbhods_flows_enkf_m48.xlsx',index_col = 0)

# make a info dataframe
df_info = df_ol[['cotrecho','mini_t1','mini_t2','mini_t3','solver']].copy()

df_info = df_info.astype(pd.Int64Dtype())

#select columns
sel = ['cotrecho','D_Q95','D_QMLT','D_Q95e','D_QMLTe']

df_ol = df_ol[sel]
df_m02 = df_m02[sel]
df_m25 = df_m25[sel]
df_m48 = df_m48[sel]

#rename
df_ol = df_ol.rename(columns = {'D_Q95':'q95_ol',
                       'D_QMLT':'qmlt_ol',
                       'D_Q95e':'q95e_ol',
                       'D_QMLTe':'qmlte_ol',
                       }
                     )


df_m02 = df_m02.rename(columns={'D_Q95':'q95_m02',
                       'D_QMLT':'qmlt_m02',
                       'D_Q95e':'q95e_m02',
                       'D_QMLTe':'qmlte_m02',
                       }
                       )

df_m25 = df_m25.rename(columns={'D_Q95':'q95_m25',
                       'D_QMLT':'qmlt_m25',
                       'D_Q95e':'q95e_m25',
                       'D_QMLTe':'qmlte_m25',
                       }
                       )


df_m48 = df_m48.rename(columns={'D_Q95':'q95_m48',
                       'D_QMLT':'qmlt_m48',
                       'D_Q95e':'q95e_m48',
                       'D_QMLTe':'qmlte_m48',
                       }
                       )

# set same index for join
df_info = df_info.set_index('cotrecho')
df_ol = df_ol.set_index('cotrecho')
df_m02 = df_m02.set_index('cotrecho')
df_m25 = df_m25.set_index('cotrecho')
df_m48 = df_m48.set_index('cotrecho')

df_join = pd.concat([df_info,df_ol,df_m02,df_m25,df_m48],axis=1)

#----------------------------------------------------------------------------
# read geopackage and join with results
#----------------------------------------------------------------------------
gdf_bho = gpd.read_file(FILE_GDF_BHO)

sel_bho = ['cotrecho','cobacia','nuareacont','nuareamont','nutrjus','geometry']

gdf_bho = gdf_bho[sel_bho]

# make join on 'cotrecho'
gdf_join = gdf_bho.join(df_join,on='cotrecho',how='left')

# export to geopackage
gdf_join.to_file('base_mgbbhods_20211013.gpkg',driver='GPKG')

gdf_join.drop('geometry',axis=1).to_excel('base_mgbbhods_20211013.xlsx')