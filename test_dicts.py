# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 11:14:59 2021

@author: Avell
"""


import funcs_io
import funcs_solver


# read dicts
the_dicts = funcs_io.read_the_dicts()



# dicts of parameters
dict_parameters_t1 = the_dicts['dict_parameters_t1']
dict_parameters_t2 = the_dicts['dict_parameters_t2']
dict_parameters_t3 = the_dicts['dict_parameters_t3']
dict_parameters_t4 = the_dicts['dict_parameters_t4']


# pointer to dict_of_parameters
dict_type_params = {
    1: dict_parameters_t1,
    2: dict_parameters_t2,
    3: dict_parameters_t3,
    4: dict_parameters_t4,
    }


# identify dict of required 'mini' for each cotrecho (partial process)
dict_bho_ixc = funcs_solver.make_dict_bho_ixc(the_dicts)



# list of available cotrechos to downscale
available_to_downscale = list(dict_bho_solver.keys())