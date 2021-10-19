
import os
import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd



# get files of timeseries
files_ts = os.listdir('./timeseries/')


#
file_topo = '../input/tabela_cotrecho_info.xlsx'


# read bho
df_tble_bho = pd.read_excel(file_topo)

#
compacum = 0.
results=[]
cotrecho = 399645
cotrecho_end = 78346
desce = True
while desce:

    coatual = cotrecho
    iatual = df_tble_bho['cotrecho']==coatual
    comptrec = df_tble_bho.loc[iatual,'nucomptrec'].values[0]  #comprimento
    cotrecho = df_tble_bho.loc[iatual,'nutrjus'].values[0]   #cod jusante

    compacum = compacum + comptrec

    print(cotrecho)

    # search for monthly timeseries in files
    try:
        codint = int(cotrecho)

        #read as dataframe
        file = './timeseries/mgbbhods_cotrecho_{}_monthly.csv'.format(codint)
        df = pd.read_csv(file,sep=';')
        #include some info in the table
        df.at['compacum',:] = compacum
        df.at['cotrecho',:] = codint

        #store current in list of results
        results.append(df)

    except:

        pass


    if cotrecho==78346:
        desce=False


# time series at hydrological year
dw = pd.concat([df['hyd_qmlt'] for df in results],axis=1)
# -> atencao ultima linha contem cotrecho.

#rename columns to cotrechos
dw.columns = [int(i) for i in dw.loc['cotrecho'].tolist()]

#make profiles
dw_profiles = dw.T
dw_profiles = dw_profiles.set_index('compacum')