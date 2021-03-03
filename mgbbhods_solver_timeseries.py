
# -*- coding: utf-8 -*-
"""
Main script to runs the downscaling of MGB results into BHO drainage
   and extract time series

@author: Mino Sorribas

@disclaimer:
    CAREFUL IT CAN GENERATE LOTS OF GBytes of DATA

    -> timeseries ofh 12420 days results in:
        ~ 400 KB   for each file of daily time-series
        - 20-30 KB  for each file of monthly timeseries
        - 2-3 KB   for each file of yearly time-series

        -> thus, 460000 cotrecho require:
            ~ 13.8 Gbytes for monthly + yearly timesries


        -> thus, ~56000 cotrechos require:
            ~ 1.7 Gbytes for monthly + yearly timeseries



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
import funcs_solver
import funcs_gpkg




print("---------------------------------------------------")
print(" Running MGB-BHO Downscaling                       ")
print("---------------------------------------------------")

start=time.time()



#-----------------------------------------------------------------------------
# Main path and general input files
#-----------------------------------------------------------------------------
PATH_MAIN = '../'
PATH_INPUT = PATH_MAIN + 'input/'

# actually, PATH_INPUT gets .bin files... but processing is local with .npy


#dont need this
#FILE_MINI = PATH_INPUT + 'mini.xlsx'
#FILE_TBLE_BHO = PATH_INPUT + 'tble_bho_info.xlsx'




#-----------------------------------------------------------------------------
# Get mgb-sa setup
#-----------------------------------------------------------------------------
version = '1979'
nt, nc, dstart, file_qtudo, file_qcel = funcs_solver.mgbsa_default(version)

file_qtudo_npy = file_qtudo.strip('.MGB') + '.npy'
file_qcel_npy = file_qcel.strip('.MGB') + '.npy'


# list of time intervals
list_t = list(range(nt))   #all time steps
ihotstart = 730             #hotstart
list_t = list_t[ihotstart:]


# cotrechos to export daily time-series
list_to_daily_ts = []       #user-defined -> easier to do after reading dicts.



#-----------------------------------------------------------------------------
# Dump binaries to numpy
#-----------------------------------------------------------------------------
flag_build_npy = False
if flag_build_npy:
    # build qtudo .npy
    filebin = PATH_INPUT + file_qtudo
    fileout = file_qtudo_npy
    _ = funcs_solver.dump_mgb_binary_to_npy(filebin, fileout, nt, nc)

    # build qcel .npy
    filebin = PATH_INPUT + file_qcel
    fileout = file_qcel_npy
    _ = funcs_solver.dump_mgb_binary_to_npy(filebin, fileout, nt, nc)




#-----------------------------------------------------------------------------
# Read MGB and BHO tables
#-----------------------------------------------------------------------------
# DONT NEED THIS!
#df_tble_mini = funcs_io.read_tble_mini(FILE_MINI, set_index='mini')
#df_tble_bho = funcs_io.read_tble_bho(FILE_TBLE_BHO)




#-----------------------------------------------------------------------------
# Read the Downscaling dicts
#-----------------------------------------------------------------------------
the_dicts = funcs_io.read_the_dicts()

# list of available dicts
#list_dicts = list(the_dicts.keys())

# dict of solver (keys are cotrechos available to downscale)
dict_bho_solver = the_dicts['dict_bho_solver']

# dicts of parameters
dict_parameters_t1 = the_dicts['dict_parameters_t1']
dict_parameters_t2 = the_dicts['dict_parameters_t2']
dict_parameters_t3 = the_dicts['dict_parameters_t3']
dict_parameters_t4 = the_dicts['dict_parameters_t4']


# list of available cotrechos to downscale
available_to_downscale = list(dict_bho_solver.keys())



#--------------------------------------------------------------------------
# Prepare switcher for dictionaries of parameters
#--------------------------------------------------------------------------

# pointer to dict_of_parameters
dict_type_params = {
    1: dict_parameters_t1,
    2: dict_parameters_t2,
    3: dict_parameters_t3,
    4: dict_parameters_t4,
    }



#--------------------------------------------------------------------------
# Prepare switcher for solvers and reading .NPY "on the fly"
#--------------------------------------------------------------------------
# identify dict of required 'mini' for each cotrecho (partial process)
dict_bho_ixc = funcs_solver.make_dict_bho_ixc(the_dicts)

# pointer for downscaling solvers
dict_tipo_fsolver = {
    1: funcs_solver.f_downscaling_t1,
    2: funcs_solver.f_downscaling_t2,
    3: funcs_solver.f_downscaling_t3,
    4: funcs_solver.f_downscaling_t4,
    }

# pre-mapping arrays
dict_tipo_mmapfile={
    1: funcs_solver.read_npy_as_mmap(file_qtudo_npy),
    2: funcs_solver.read_npy_as_mmap(file_qtudo_npy),
    3: funcs_solver.read_npy_as_mmap(file_qcel_npy),
    4: funcs_solver.read_npy_as_mmap(file_qtudo_npy),
    }




#--------------------------------------------------------------------------
# Select cotrechos for downscaling (default= all available) and time-series
#--------------------------------------------------------------------------
# select all cotrechos to downscale
if 'list_to_downscale' not in locals():
    list_to_downscale = available_to_downscale.copy()



#NOTE: THIS IS A HARDCODE FILTER!
# select only type 1 and 2.
list_to_downscale = []
for c,tipo in dict_bho_solver.items():
    if tipo==1 or tipo==2:
        list_to_downscale.append(c)





#--------------------------------------------------------------------------
# Main loop block for downscaling
#--------------------------------------------------------------------------
def hydroyear(year,month):
    if month>=10:
        month = month-10+1
        year = year+1
    else:
        month = month+3
        year = year
    return year,month


# loop downscaling of cotrechos
conta=0
nconta = len(list_to_downscale)
hconta = 100./nconta
ttipo=1 #auxiliary
for c in list_to_downscale:

    # get type of solver
    tipo = dict_bho_solver.get(c)     #1,2,3 or 4

    #DEBUG:TESTING RESULTS
    #if tipo!=ttipo:
    #    continue

    # counter
    conta = conta+1
    print(" - downscaling {}/{} - {}%  ".format(conta,nconta,round(conta*hconta,2)))


    # get parameters
    d_params = dict_type_params.get(tipo) ##.get(c)

    # get downscaling function
    func = dict_tipo_fsolver.get(tipo)

    # data mmap (pre-mapped)
    mmapfile = dict_tipo_mmapfile.get(tipo)

    # required mini
    list_c = dict_bho_ixc.get(c)

    # --
    # downscale
    # get time series from memmap of binary
    df_flow = funcs_solver.mmap_to_dataframe(mmapfile, list_t, list_c, dstart)

    # method i - downscale via time-series
    df_qts = pd.DataFrame(func(c,d_params,df_flow),index = df_flow.index) #ts downscale!

    # --
    # hydrologic year
    hyd_month = np.where(df_qts.index.month>=10,df_qts.index.month-10+1,df_qts.index.month+3)
    hyd_year = np.where(df_qts.index.month>=10,df_qts.index.year+1,df_qts.index.year)

    # --
    # annual aggregation from time series
    #calendar year
    df_annual_q95 = df_qts.groupby(df_qts.index.year).quantile(0.05).rename(columns={0:'q95'})
    df_annual_qmlt = df_qts.groupby(df_qts.index.year).mean().rename(columns={0:'qmlt'})

    #hydrological year
    df_hyd_annual_q95 = df_qts.groupby(hyd_year).quantile(0.05).rename(columns={0:'hyd_q95'})
    df_hyd_annual_qmlt = df_qts.groupby(hyd_year).mean().rename(columns={0:'hyd_qmlt'})

    #join annual stats
    df_annual_stats = pd.concat([df_annual_q95,df_annual_qmlt,df_hyd_annual_q95,df_hyd_annual_qmlt],axis=1)
    df_annual_stats.index.rename('year',inplace=True)


    # --
    # monthly aggregation from time series
    #calendar year
    cal_map = {'level_0':'year','level_1':'month'}
    iyymm = [df_qts.index.year,df_qts.index.month]
    df_monthly_q95 = df_qts.groupby(iyymm).quantile(0.05).rename(columns={0:'q95'}).rename(columns=cal_map)
    df_monthly_qmlt = df_qts.groupby(iyymm).mean().rename(columns={0:'qmlt'}).rename(columns=cal_map)

    #hydrological year
    hyd_map = {'level_0':'hyd_year','level_1':'hyd_month'}
    iyymm = [hyd_year,hyd_month]
    df_hyd_monthly_q95 = df_qts.groupby(iyymm).quantile(0.05).rename(columns={0:'hyd_q95'}).rename(columns=hyd_map)
    df_hyd_monthly_qmlt = df_qts.groupby(iyymm).mean().rename(columns={0:'hyd_qmlt'}).rename(columns=hyd_map)

    #join monthly stats
    df_monthly_cal = pd.concat([df_monthly_q95,df_monthly_qmlt],axis=1).reset_index().rename(columns=cal_map)
    df_monthly_hyd = pd.concat([df_hyd_monthly_q95,df_hyd_monthly_qmlt],axis=1).reset_index().rename(columns=hyd_map)
    df_monthly_stats = pd.concat([df_monthly_cal,df_monthly_hyd],axis=1)
    df_monthly_stats.index.rename('index',inplace=True)


    # --
    # export time-series to xlsx
    df_qts = df_qts.rename(columns = {0:c} )    # column '0' -> 'cotrecho'

    #file_ts = "./timeseries/mgbbhods_cotrecho_{}.xlsx".format(c)
    #df_qts.to_excel(file_ts)

    # --
    # export daily time-series as csv
    if c in list_to_daily_ts: # bad implementation cause we know a priori.
        file_ts = "./timeseries/mgbbhods_cotrecho_{}_daily.csv".format(c)
        df_qts.to_csv(file_ts,sep=';', float_format='%6.6f')

    # --
    # export annual aggregation
    file_ts = "./timeseries/mgbbhods_cotrecho_{}_yearly.csv".format(c)
    df_annual_stats.to_csv(file_ts, sep=';', float_format='%6.6f')

    # --
    # export annual aggregation
    file_ts = "./timeseries/mgbbhods_cotrecho_{}_monthly.csv".format(c)
    df_monthly_stats.to_csv(file_ts, sep=';', float_format='%6.6f')

    print(" - saving time-series of cotrecho {}".format(c) )


finish=time.time()







