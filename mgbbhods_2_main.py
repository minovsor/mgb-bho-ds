# -*- coding: utf-8 -*-
"""

Main script for Pre-processing of MGB Downscaling to the BHO drainage

@author: Mino Sorribas

@updates:
    - may/2020: 1st version - test case
    - aug/2020: MGB-AS (types 1, 2 and 3)
    - sep/2020: include type 4 (external)
    - dec/2020: main block revision (mgbbho_v2), funcs_op, funcs_op_t2
    - jan/2020: funcs_ops_t2->funcs_op, funcs_utils, funcs_op_t1, funcs_gpkg
    - fev/2020:

@todo
    - adjust preprocessing steps between companion files:
        1) _zero.py could deal call the .associate_bho_mini_domain
        2) _matlab.py could consume results from _zero.py
        3) _main.py would not call .associate_bho_mini_domain but only read
             the dict_bho_domain.pickle


"""

# standard python
import os
import time
import itertools
import pickle

# plotting, numpy, dataframes and spatial
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd


# downscaling functions
import funcs_utils
import funcs_io
import funcs_op



print("---------------------------------------------------")
print(" Main Pre-processing for the MGB-BHO Downscaling   ")
print("---------------------------------------------------")



#-----------------------------------------------------------------------------
# SYSTEM INFO
#-----------------------------------------------------------------------------

# timer
start = time.time()


'''
mem_threshold = 3.0 * 1024 * 1024 * 1024  # 3GB
mem_info = psutil.virtual_memory()
mem_swap = psutil.swap_memory()
if mem_info.available < mem_threshold:
    print(" Warning: not enough memory (3GB RAM)")
    break
'''



#-----------------------------------------------------------------------------
# INPUT PATHS AND FILES
#-----------------------------------------------------------------------------
print(" Initializing filepaths... ")

PATH_MAIN = '../'
PATH_INPUT = PATH_MAIN + 'input/'

# table mgb topology
FILE_MINI = PATH_INPUT + 'mini.xlsx'

# table type 1
#FILE_TBLE_T1 = PATH_INPUT + 'table_t1.xlsx'  #made in matlab old
#FILE_TBLE_T1 = PATH_INPUT + 'table_t1_2021_inter2.xlsx'
FILE_TBLE_T1 = 'table_t1_py.xlsx'  #made in python

# geopackage BHO drainage
FILE_GDF_BHO = PATH_INPUT + 'geoft_bho_2017_5k_trecho_drenagem.gpkg'

# shapefile MGB
FILE_MGB_CATCHMENTS_SHP = PATH_INPUT + 'mgb_sa_unit_catchments_sirgas2000.shp'




#-----------------------------------------------------------------------------
# PARAMETERS
#-----------------------------------------------------------------------------
print(" Reading parameters... ")
# tolerance for drainage area relative error (%) in type 1
#tol_diffp = 20.  #testing - fixed threshold

# area threshold for targeting bho drainage as type 1 and 2
area_threshold_t12 = 1000.      # MGB-AS (VS pers.comm.)


# flag to drop geometry of bho after pre-processing
# note: free lots of memory (but wont export gpkg or plot maps here)
flag_drop_geom = True


# flag preprocessing
flag_prepro = False     # True to run prepro.


#-----------------------------------------------------------------------------
# LOAD TABLES
#-----------------------------------------------------------------------------
print(" Loading datatables and spatial data... ")

# table mgb topology
df_tble_mini = funcs_io.read_tble_mini(FILE_MINI)

# table bho
#df_tble_bho = funcs_io.read_tble_bho(FILE_TBLE_BHO)

# bho trechos (geodataframe)
gdf_tble_bho = funcs_io.read_gdf_bho(FILE_GDF_BHO)

# mgb catchments (shapefile)
gdf_mgb_catchments = gpd.read_file(FILE_MGB_CATCHMENTS_SHP)


# table type 1 (+ filter)
df_tble_t1 = funcs_io.read_tble_t1(FILE_TBLE_T1, tol_t1 = True) #new version



#-----------------------------------------------------------------------------
# PRE-PROCESSING - IDENTIFY MGB DOMAIN INSIDE BHO (STEP ZERO)
#-----------------------------------------------------------------------------
print(" Pre-processing domain (MGB inside BHO)... ")
if flag_prepro:
    # obtain raw domain (bho inside mgb catchments)
    dict_bho_domain = funcs_op.associate_bho_mini_domain(gdf_tble_bho,
                                                         gdf_mgb_catchments,
                                                         pts_to_gpkg='bho_midpts.gpkg'
                                                         )
else:
    # read pre-processed domain
    with open('dict_bho_domain.pickle','rb') as f:
            dict_bho_domain = pickle.load(f)


if flag_drop_geom:
    #... dont need geometries anymore (drop because they're heavy!)
    gdf_tble_bho = gdf_tble_bho.drop('geometry',axis=1)

#... from now on, works with the table
#... and adopt 'df_tble_bho' as the variable name
#... thus, the next statement keeps the old object (same memory)
#    id(df_tble_bho)==id(gdf_tble_bho)
df_tble_bho = gdf_tble_bho




#-----------------------------------------------------------------------------
# BUILD INITIAL TYPE 3 (BACKGROUND)
#-----------------------------------------------------------------------------
print(" Associating background domain as initial type 3... ")

# associate type 3
dict_bho_mini_t3 = funcs_op.associate_bho_mini_t3(dict_bho_domain)

# extract parameters for type 3
dict_parameters_t3 = funcs_op.define_parameters_t3(dict_bho_mini_t3,
                                                   df_tble_mini,
                                                   df_tble_bho)
#TODO: could dump parameters to pickle to save memory.



#-----------------------------------------------------------------------------
# BUILD TYPE 1 FROM TABLE GENERATED IN EXTERNAL APPLICATION (MATLAB)
#-----------------------------------------------------------------------------
print(" Associating type 1 drainage... ")

#TODO: insert matlab algorithm here + filters -> df_tble_t1
# ... actually, could update the funcs_op.associate_bho_mini_t1()

# sets area_threshold for main rivers
#area_threshold_t12 = df_tble_mini[df_tble_mini['ordem']==1]['aream_km2'].min()


# associate type 1
dict_bho_mini_t1 = funcs_op.associate_bho_mini_t1(df_tble_t1)

# extract parameters for type 1
dict_parameters_t1 = funcs_op.define_parameters_t1(df_tble_t1)




#-----------------------------------------------------------------------------
# INITIAL SCREENING FOR TYPE 2
#-----------------------------------------------------------------------------
print(" Associating type 2 drainage... ")

# evaluates connectivity by mgb topology
# for each pair {cotrecho:mini} in table type 1
# - check if all affluent mgb catchments also have a cotrecho assoaciated
# - check if the associated cotrecho actually flows downstream into the current
# - check if routes dont runover type 1


# merge topologies (mgb and bho) into tble t1 for connectivity analyses
df_tble_topo_t1 = funcs_op.merge_topologies_t1(
    df_tble_t1,
    df_tble_mini,
    df_tble_bho,
    )

# initial screening of routes for type 2
dict_routes_t2, dict_mini_afl_t2 = funcs_op.screening_candidates_t2(
    df_tble_topo_t1,
    df_tble_mini,
    df_tble_bho,
    )

# associate type 2 in valid routes
dict_bho_mini_t2, dict_mini_afldum_t2 = funcs_op.associate_bho_mini_t2(
    dict_mini_afl_t2,
    dict_routes_t2,
    df_tble_mini,
    )

# extract parameters for type 1
dict_parameters_t2 = funcs_op.define_parameters_t2(
    dict_bho_mini_t2,
    dict_mini_afl_t2,
    dict_routes_t2,
    dict_bho_mini_t1,
    df_tble_bho,
    )




#-----------------------------------------------------------------------------
# POST-PROCESSING: CHECK DRAINAGE TYPES (SETS) FOR TYPES 1, 2 and 3
#-----------------------------------------------------------------------------
print(" Validating drainage for types 1, 2 and 3... ")

# validates types 1, 2 and 3 and make candidates for type 4
groups_t123, dicts_t123, group_t4_candidates = funcs_op.validate_t123(
    df_tble_bho,
    dict_bho_domain,
    area_threshold_t12,
    dict_bho_mini_t1,
    dict_bho_mini_t2,
    dict_bho_mini_t3,
    )

# recover post-processed groups and dictionaries
group_t1_post, group_t2_post, group_t3_post = groups_t123
dict_bho_mini_t1_post, dict_bho_mini_t2_post, dict_bho_mini_t3_post = dicts_t123




#-----------------------------------------------------------------------------
# TYPE 4
#-----------------------------------------------------------------------------
print(" Dealing with type 4 candidates... ")

# make parameters for type 4
group_t4_post, dict_parameters_t4, lost_t4 = funcs_op.define_parameters_t4(
    group_t4_candidates,
    dict_parameters_t3,
    df_tble_bho,
    dict_bho_mini_t1_post,
    df_tble_mini,
    )




#-----------------------------------------------------------------------------
# MAKE SOLUTION TAGS
#-----------------------------------------------------------------------------
print(" Making dictionary of solutions... ")
#  make dictionary of solutions
dict_bho_solver = funcs_op.make_dict_solver(
    group_t1_post,
    group_t2_post,
    group_t3_post,
    group_t4_post,
    )




#-----------------------------------------------------------------------------
# SAVE PARAMETERS
#-----------------------------------------------------------------------------
print(" Dumping dictionaries to disk... ")
# dump dictionaries to disk
_ = funcs_io.dump_the_dicts(
    dict_bho_mini_t1_post,
    dict_bho_mini_t2_post,
    dict_bho_mini_t3_post,
    dict_parameters_t1,
    dict_parameters_t2,
    dict_parameters_t3,
    dict_parameters_t4,
    dict_bho_solver,
    )




#-----------------------------------------------------------------------------
# PLOT
#-----------------------------------------------------------------------------
flag_plot = False
if flag_plot & flag_drop_geom:
    fig,ax=plt.subplots(figsize=(12,8))
    gdf_tble_bho.plot(ax=ax,color='black')
    gdf_tble_bho[gdf_tble_bho['cotrecho'].isin(group_domain)].plot(ax=ax,color='blue')
    gdf_tble_bho[gdf_tble_bho['cotrecho'].isin(group_t1_post)].plot(ax=ax,color='red')
    gdf_tble_bho[gdf_tble_bho['cotrecho'].isin(group_t2_post)].plot(ax=ax,color='green')
    gdf_tble_bho[gdf_tble_bho['cotrecho'].isin(group_t3_post)].plot(ax=ax,color='cyan')
    gdf_tble_bho[gdf_tble_bho['cotrecho'].isin(group_t4_post)].plot(ax=ax,color='olive')
    gdf_tble_bho[gdf_tble_bho['cotrecho'].isin(lost_t4)].plot(ax=ax,color='magenta')


end = time.time()
print("\n Done in {} seconds".format(round(end-start,2)))


