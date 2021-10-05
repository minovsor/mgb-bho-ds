# -*- coding: utf-8 -*-
"""
Main script to runs the downscaling of MGB results into BHO drainage

@author: Mino Sorribas

@todo:
    - export specific discharge m3/s.km2
    - export timeseries
        df.to_csv('test.csv',sep =' ',mode='a',header=False) #
        np.savetxt('test.txt',df.reset_index(),fmt='%d')

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

suffix = 'flows_1979'
suffix = 'flows_enkf'



#-----------------------------------------------------------------------------
# Main path and general input files
#-----------------------------------------------------------------------------
PATH_MAIN = './'
PATH_INPUT = PATH_MAIN + 'input/'

FILE_GDF_BHO = PATH_INPUT + 'geoft_bho_2017_5k_trecho_drenagem.gpkg'

#... read only at the end for join

#dont need this
#FILE_MINI = PATH_INPUT + 'mini.xlsx'
#FILE_TBLE_BHO = PATH_INPUT + 'tble_bho_info.xlsx'




#-----------------------------------------------------------------------------
# Get mgb-sa setup
#-----------------------------------------------------------------------------
version = '1979'
version = 'enkf_1979'
nt, nc, dstart, file_qtudo, file_qcel = funcs_solver.mgbsa_default(version)

file_qtudo_npy = file_qtudo.strip('.MGB') + '.npy'
file_qcel_npy = file_qcel.strip('.MGB') + '.npy'


# list of time intervals
list_t = list(range(nt))   #all time steps
ihotstart = 730             #hotstart
list_t = list_t[ihotstart:]

# export time series
flags_export_ts = [-9999] # disable timeseries to xlsx
#flags_export_ts = [1,2] # select drainage types 1 and 2 to timeseries xlsx


#-----------------------------------------------------------------------------
# Dump binaries to numpy
#-----------------------------------------------------------------------------
flag_build_npy = True
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
# TODO: this block could be defined in funcs_solver.

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
# select cotrechos to downscale stats
if 'list_to_downscale' not in locals():
    list_to_downscale = available_to_downscale.copy()





#--------------------------------------------------------------------------
# Main loop block for downscaling
#--------------------------------------------------------------------------

# dicts for results
D_Q95 = {}
D_QMLT = {}
D_Q95_ts = {}
D_QMLT_ts = {}


D_Q95e = {}
D_QMLTe = {}
D_Q95e_ts = {}
D_QMLTe_ts = {}



# loop downscaling of cotrechos
conta=0
hconta = 100./len(list_to_downscale)
ttipo=1 #auxiliary
for c in list_to_downscale:

    # get type of solver
    tipo = dict_bho_solver.get(c)     #1,2,3 or 4

    #DEBUG:TESTING RESULTS
    #if tipo!=ttipo:
    #    continue

    # counter
    conta = conta+1
    print(" - downscaling {} - {}% ".format(conta,round(conta*hconta,2)))


    # get parameters
    d_params = dict_type_params.get(tipo) ##.get(c)

    # get downscaling function
    func = dict_tipo_fsolver.get(tipo)

    # data mmap (pre-mapped)
    mmapfile = dict_tipo_mmapfile.get(tipo)

    # required mini
    list_c = dict_bho_ixc.get(c)


    # calculate stats and downscale
    # get time series from memmap of binary
    df_flow = funcs_solver.mmap_to_dataframe(mmapfile, list_t, list_c, dstart)

    # method i - downscale via time-series
    df_qts = pd.DataFrame(func(c,d_params,df_flow),index = df_flow.index) #ts downscale!
    q95_ts = df_qts.quantile(0.05).values[0] # calculate stats from ts
    qmlt_ts = df_qts.mean().values[0]        # calculate stats from ts

    #export time-series
    #if tipo in flags_export_ts:
    #    file_ts = "./timeseries/mgbbhods_cotrecho_{}.xlsx".format(c)
    #    print(" - saving {} to xlsx".format(c) )
    #    df_qts.to_excel(file_ts)


    # method ii - downscale via stats (q95,qmlt)
    df_q95  = pd.DataFrame(df_flow.quantile(0.05)).transpose()
    df_qmlt = pd.DataFrame(df_flow.mean()).transpose()

    q95 = func(c, d_params, df_q95)    # downscale stats
    qmlt = func(c, d_params, df_qmlt)  # downscale stats


    # annual aggregation from time series
    df_annual_q95 = df_qts.groupby(df_qts.index.year).quantile(0.05)
    df_annual_qmlt = df_qts.groupby(df_qts.index.year).mean()


    # store results (m3/s)
    D_Q95[c] = round(q95,6)
    D_QMLT[c] = round(qmlt,6)

    D_Q95_ts[c] = round(q95_ts,6)
    D_QMLT_ts[c] = round(qmlt_ts,6)



    #if tipo == 3:
    #    print(df_qts)
    #    break


    #specific discharge (m3/s.km2)
    nuareamont = d_params.get(c).get('nuareamont')
    if isinstance(nuareamont,list):
        nuareamont = nuareamont[0]
    D_Q95e[c] = round(q95/nuareamont,12)
    D_QMLTe[c] = round(qmlt/nuareamont,12)

    D_Q95e_ts[c] = round(q95_ts/nuareamont,12)
    D_QMLTe_ts[c] = round(qmlt_ts/nuareamont,12)


    '''
    if tipo==ttipo:
        print(ttipo)
        print(df_q95.values,q95,type(q95))
        print(df_qmlt.values,qmlt,type(qmlt))
        ttipo=ttipo+1
    '''


#--------------------------------------------------------------------------
# Export downscaled values to pickle
#--------------------------------------------------------------------------
flag_to_pickle = False

if flag_to_pickle:

    with open('D_Q95.pickle','wb') as f:
        pickle.dump(D_Q95,f)

    with open('D_QMLT.pickle','wb') as f:
        pickle.dump(D_QMLT_ts,f)

    with open('D_Q95_ts.pickle','wb') as f:
        pickle.dump(D_Q95_ts,f)

    with open('D_QMLT_ts.pickle','wb') as f:
        pickle.dump(D_QMLT_ts,f)



    with open('D_Q95e.pickle','wb') as f:
        pickle.dump(D_Q95e,f)

    with open('D_QMLTe.pickle','wb') as f:
        pickle.dump(D_QMLTe_ts,f)

    with open('D_Q95e_ts.pickle','wb') as f:
        pickle.dump(D_Q95e_ts,f)

    with open('D_QMLTe_ts.pickle','wb') as f:
        pickle.dump(D_QMLTe_ts,f)


#--------------------------------------------------------------------------
# Export downscaled values, solver and catchments association as gpkg/xlsx
#--------------------------------------------------------------------------
##df_tble_solver = pd.DataFrame.from_dict(dict_bho_solver, orient='index', columns=['solver'])


# get bho-mini association for types 1, 2 and 3
dict_bho_mini_t1 = the_dicts['dict_bho_mini_t1_post']
dict_bho_mini_t2 = the_dicts['dict_bho_mini_t2_post']
dict_bho_mini_t3 = the_dicts['dict_bho_mini_t3_post']


# read BHO geodataframe
gdf_tble_bho = gpd.read_file(FILE_GDF_BHO)

# dicts for new columns
#label = ('D_Q95','D_QMLT','D_Q95_ts','D_QMLT_ts','mini_t1','mini_t2','mini_t3','solver')
#kvs = (D_Q95,D_QMLT,D_Q95_ts,D_QMLT_ts,dict_bho_mini_t1,dict_bho_mini_t2,dict_bho_mini_t3,dict_bho_solver)
#D = dict(zip(label,kvs))


# dicts for new columns
label = ('D_Q95','D_QMLT','D_Q95_ts','D_QMLT_ts',
         'D_Q95e','D_QMLTe','D_Q95e_ts','D_QMLTe_ts',
         'mini_t1','mini_t2','mini_t3','solver')
kvs = (D_Q95,D_QMLT,D_Q95_ts,D_QMLT_ts,
       D_Q95e,D_QMLTe,D_Q95e_ts,D_QMLTe_ts,
       dict_bho_mini_t1,dict_bho_mini_t2,dict_bho_mini_t3,dict_bho_solver)
D = dict(zip(label,kvs))


# pass dicts to dataframe and export
G = funcs_gpkg.f_dicts_to_bho_gpkg(gdf_tble_bho, D, suffix='flows_1979')

del gdf_tble_bho




'''

#--
# Export stats

# export as xlsx
df_tble_q95 = pd.DataFrame.from_dict(D_Q95, orient='index', columns=['q95'])
df_tble_qmlt = pd.DataFrame.from_dict(D_QMLT, orient='index', columns=['qmlt'])

df_tble_q95_ts = pd.DataFrame.from_dict(D_Q95_ts, orient='index', columns=['q95_ts'])
df_tble_qmlt_ts = pd.DataFrame.from_dict(D_QMLT_ts, orient='index', columns=['qmlt_ts'])

#join tables
df_stats = pd.concat([df_tble_q95, df_tble_qmlt, df_tble_q95_ts, df_tble_qmlt_ts],axis=1)
df_stats.to_excel('table_qstats.xlsx')


'''


finish=time.time()


#TODO: salvar em dataframe ao inves de dicionarios?!
# ou uma lista com stats em dicionario unico










