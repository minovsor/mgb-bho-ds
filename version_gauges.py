# -*- coding: utf-8 -*-
"""
Link hidroreference (gauges at bho) to MGB downscale results.

SAVE
 - base_mgbbhods_postos_20211013.xlsx'

@author: Mino Sorribas
"""


import pickle
import pandas as pd


file_cotrecho_posto = 'dict_cotrecho_posto_sem_ons_benchmark_sem_climadj.pickle'

file_base_mgbbho = 'base_mgbbhods_20211013.xlsx'  #vazoes downscaled

# read hidroref pickle
with open(file_cotrecho_posto,'rb') as f:
    dict_cotrecho_posto = pickle.load(f)


# read mgb downscale results
df = pd.read_excel(file_base_mgbbho,index_col=0)


# make columns for gauges
df['posto'] = df['cotrecho'].map(dict_cotrecho_posto).explode() #map dict and explode list


dfe = df[df.posto.notna()] #keep trecho with gauges

dfe.to_excel('base_mgbbhods_postos_20211013.xlsx')

