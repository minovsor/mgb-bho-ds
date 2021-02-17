# -*- coding: utf-8 -*-
"""
Some utility functions

@author: Mino Sorribas
"""

import numpy as np
import pandas as pd


bho_dtypes = {
    'fid':pd.Int64Dtype(),
    'drn_pk':int,
    'cotrecho':int,
    'noorigem':int,
    'nodestino':int,
    'cocursodag':str,
    'cobacia':str,
    'nucomptrec':float,
    'nudistbact':float,
    'nudistcdag':float,
    'nuareacont':float,
    'nuareamont':float,
    'nogenerico':str,
    'noligacao':str,
    'noespecif':str,
    'noriocomp':str,
    'nooriginal':str,
    'cocdadesag':str,
    'nutrjus':pd.Int32Dtype(),
    'nudistbacc':float,
    'nuareabacc':float,
    'nuordemcda':pd.Int32Dtype(),
    'nucompcda':float,
    'nunivotto':int,
    'nunivotcda':pd.Int32Dtype(),
    'nustrahler':pd.Int32Dtype(),
    'dedominial':str,
    'dsversao':str,
    'cobacia_50k':str,
    'lat':float,
    'lon':float,
    }



