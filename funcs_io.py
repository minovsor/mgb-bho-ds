# -*- coding: utf-8 -*-
"""

Main functions for processing input/output of tables, files, etc.

@author: Mino Sorribas


"""
import os
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import pickle
import json


#-----------------------------------------------------------------------------
# FUNCTIONS TO READ MGB TOPOLOGY
#-----------------------------------------------------------------------------
def read_tble_mini(file_mini, mgb_version = 'MGB-AS', set_index = None):
    """
    Read mini.xlsx, adjust headers and return as dataframe

    Args:
        file_mini(str)  :: pathfile to 'mini.xlsx' (mini.gtp in MSExcel format)
        mgb_version(str) :: version of table for header mapping
        set_index(str,optional) :: column name to use as index

    Returns:
        df_tble_mini(pd.DataFrame) :: table mini with proper headers

    Notes:
        - mgb_version must be a a key of version_map (dict), which handles
        different versions of MGB columns.

    """
    # read mini.xlsx
    df_tble_mini = pd.read_excel(file_mini)

    # adjust 'mini' column name by version
    version_map = {
        'MGB-AS':{'Mini':'mini'},
        'MGB-QGIS':{'Mini_ID':'mini'},
        }

    # adjust 'mini' reference by version
    df_tble_mini = df_tble_mini.rename(columns = version_map[mgb_version])


    # adjust headers (make lowercase)
    func_str = lambda s: s.lower().replace("/","_").replace("(","").replace(")","")
    header_lower = {v:func_str(v) for v in df_tble_mini.columns}
    df_tble_mini = df_tble_mini.rename(columns = header_lower)


    # optional: column 'mini' as dataframe index
    if set_index == 'mini':
        df_tble_mini = df_tble_mini.set_index('mini',drop=False)

    return df_tble_mini




#-----------------------------------------------------------------------------
# FUNCTIONS TO READ AND FILTER TABLE TYPE 1
#-----------------------------------------------------------------------------
def f_test_area(a_diff_perc, area_to_test):
    """
    Function to test if error in area is acceptable for type 1 association
        based on table below
       ad hoc criteria by Vinicius Siqueira
       area_lb area_ub  max_error
            0     1500  30
         1500     3000  25
         3000     5000  20
         5000    10000  15
        10000    20000  10
        20000    50000   7
        50000   200000   5
       200000   500000   3
       500000  1000000   2
      1000000  6000000   1.5

    Args:
        a_diff_perc (float) :: relative error in area
        area_to_test (float) :: drainage area [km2]

    Returns:
        accept (bool):: True(False) for accepted (or not)

    """

    # sets table - based on MATLAB algorithm for type 1
    tble_area_min = [0., 1500., 3000., 5000., 10000., 20000., 50000., 200000., 500000., 1000000.]
    tble_area_max = [1500., 3000., 5000., 10000., 20000., 50000., 200000., 500000., 1000000., 6000000.]
    tble_area_tol = [30., 25., 20., 15., 10., 7., 5., 3., 2., 1.5]

    # begin table search
    accept = False
    npts = len(tble_area_tol)
    for j in range(npts):
        # find position in table
        if (area_to_test >= tble_area_min[j]) & (area_to_test < tble_area_max[j]):
            # test if is acceptable
            a_thre = tble_area_tol[j]
            accept = a_diff_perc < a_thre
            break
    return accept


def f_area_acceptable_t1(row, iostat=False):
    """
    Row-based function to test area errors as in criteria for type 1 association

    Usage:
        iaccept = df_tble_t1.apply(f_area_acceptable_t1,axis=1)

    Args:
        row (pd.Series)  :: row of df_tble_t1
        iostat (bool)    :: true/false to print on screen

    Returns:
        accept (pd.DataFrame) :: True/False for each row (same index as dataframe)

    """

    # get row values from df_tble_t1
    area_to_test = row['bho_nuareamont']
    a_diff_perc = np.abs(row['diffp_areamont'])

    # function to test area
    accept = f_test_area(a_diff_perc, area_to_test)

    if iostat == True:
        if accept:
            print(" area {} km² - error {} % < {} %: accepted".format(area_to_test,a_diff_perc, a_thre))
        else:
            print(" area {} km² - error {} % < {} %: rejected".format(area_to_test,a_diff_perc, a_thre))

    return accept




def read_tble_t1(file_tble_t1, sheet_name='Data', tol_t1 = True, tol_diffp = None):
    """
    Read and pre-processing of 'tabela_tipo_1.xlsx'
        and returns as dataframe

    Args:
        file_tble_t1 (str)  :: pathfile to (table_t1.xlsx) with table 1 data
        sheet_name (str)    :: sheet_name with data in file_tble_t1
        tol_t1 (bool)       :: True  - apply f_area_acceptable
        tol_diffp (float)   :: None (default), else apply filter by absolute
                               error in area <= tol_diffp

    Returns:
        df_tble_t1(pd.DataFrame) :: table type 1

    Notes:
        Pre-processing includes
        - it adjust headers
        - it calculates abs relative error in drainage area
        - it removes duplicated 'cotrecho' (priorizes smaller erros)
        - it removes rows with above tolerance (tol_diffp)
        - check variable header_xls for required column names
        TODO: talk to JB/VS to change standard header in file_tble_t1(.xls)


    Equivalent of older versions
        - funcs_io.read_tble_t1(FILE_TBLE_T1, tol_t1 = False)
        - funcs_io.read_tble_t1(FILE_TBLE_T1, tol_t1 = False, tol_diffp = tol_diffp) #old

    """

    try: #table from matlab
        # required columns
        header_xls = ['Mini','cotrecho','codigo_otto','AreaM_BHO','AreaM_MGB',
                      'Diff(%)','Lat','Lon','Flag_mini_in']

        # mapping new headers
        header_map = {
            'Mini':'mini',
            'cotrecho':'bho_cotrecho',
            'AreaM_BHO':'bho_nuareamont',
            'AreaM_MGB':'mini_areamont',
            'Diff(%)':'diffp_areamont',
            'Lat':'latitude',
            'Lon':'longitude',
            'codigo_otto':'codigo_otto',
            'Flag_mini_in':'flag_mini_in'
            }

        # read file and adjust headers
        df_tble_t1 = pd.read_excel(file_tble_t1,sheet_name=sheet_name)
        df_tble_t1 = df_tble_t1[header_xls]
        df_tble_t1 = df_tble_t1.rename(columns=header_map)
        print(" -- table 1 from matlab")

    except: #table made in python
        # required columns
        header_xls = ['mini', 'bho_cotrecho', 'codigo_otto', 'bho_nuareamont',
       'mini_areamont', 'diffp_areamont', 'latitude', 'longitude',
       'flag_mini_in']

        df_tble_t1 = pd.read_excel(file_tble_t1)
        df_tble_t1 = df_tble_t1[header_xls]
        print(" -- table 1 from python")



    # calculate relative error in drainage area
    # reference to bho (#ms)
    #df_tble_t1['abs_diffp2'] = abs(100.*(df_tble_t1['mini_areamont']/df_tble_t1['bho_nuareamont']-1.))
    # reference to mgb (like table t1)
    df_tble_t1['abs_diffp'] = abs(100.*(df_tble_t1['bho_nuareamont']/df_tble_t1['mini_areamont']-1.))

    # remove nulls and duplicates (keep smaller error)
    df_tble_t1 = df_tble_t1[df_tble_t1['bho_cotrecho'].notna()]
    df_tble_t1 = df_tble_t1.sort_values('abs_diffp').drop_duplicates('bho_cotrecho',keep='first')


    # calculate bho/mgb area ratio
    df_tble_t1['area_ratio'] = df_tble_t1['bho_nuareamont']/df_tble_t1['mini_areamont']

    # filter based on table 1 criteria
    if tol_t1:
        iaccept = df_tble_t1.apply(f_area_acceptable_t1,axis=1)
        df_tble_t1 = df_tble_t1[iaccept]

    # optional: remove rows by tol_diffp
    if tol_diffp:
        df_tble_t1 = df_tble_t1[df_tble_t1['abs_diffp'] <= tol_diffp]


    return df_tble_t1



#-----------------------------------------------------------------------------
# FUNCTIONS TO READ BHO GEOPACKAGE OR TABLE
#-----------------------------------------------------------------------------
def read_gdf_bho(file_gdf_bho):
    """
    Read geopackage file with BHO drainage (cotrecho)
        adjust dtypes and returns as geodataframe

    Args:
        file_gdf_bho(str)  :: pathfile to BHO drainage in .gpkg/shp

    Returns:
        gdf_tble_bho (gpd.GeoDataFrame) :: table for BHO drainage (polyline)

    Notes:
        - see required columns in variable 'cols'

    """
    gdf_tble_bho = gpd.GeoDataFrame.from_file(file_gdf_bho)

    # save crs for later
    crs = gdf_tble_bho.crs

    # required cols
    cols = ['cotrecho','cobacia',
           'nucomptrec','nuareacont','nuareamont',
           'nutrjus','dedominial','nustrahler',
           'nuordemcda','cocursodag','cocdadesag','nudistbact',
           'nunivotto',
           'geometry',
           ]

    gdf_tble_bho = gdf_tble_bho[cols]

    # apply dtypes
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
    hmap = {k:v for k,v in bho_dtypes.items() if k in gdf_tble_bho.columns}
    gdf_tble_bho = gdf_tble_bho.astype(hmap)

    #recover crs
    gdf_tble_bho.crs = crs

    #make spatial index
    gdf_tble_bho.sindex

    return gdf_tble_bho



def read_tble_bho(file_tble_bho):
    """
    Read BHO table in MSExcel format
        adjust dtypes and returns as dataframe

    Args:
        file_tble_bho(str)  :: pathfile (in MSExcel format)


    Returns:
        df_tble_bho (pd.DataFrame) :: BHO drainage table

    Notes:
        - see required columns in variable 'cols'

    """
    df_tble_bho = pd.read_excel(file_tble_bho)

    # required cols
    cols = ['cotrecho','cobacia',
           'nucomptrec','nuareacont','nuareamont',
           'nutrjus','dedominial','nustrahler',
           'nuordemcda','cocursodag','cocdadesag','nudistbact',
           'nunivotto',
           ]

    df_tble_bho = df_tble_bho[cols]

    # apply dtypes
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
    hmap = {k:v for k,v in bho_dtypes.items() if k in df_tble_bho.columns}
    df_tble_bho = df_tble_bho.astype(hmap)

    return df_tble_bho




#-----------------------------------------------------------------------------
# FUNCTIONS TO DUMP AND LOAD THE DOWNSCALING PRE-PROCESSING RESULTS (DICTS)
#-----------------------------------------------------------------------------
def dump_the_dicts(
        dict_bho_mini_t1_post,
        dict_bho_mini_t2_post,
        dict_bho_mini_t3_post,
        dict_parameters_t1,
        dict_parameters_t2,
        dict_parameters_t3,
        dict_parameters_t4,
        dict_bho_solver,
        pathout='./',
        ):

    """
    Save main dictionaries to disk
        - cotrecho x mini for type 1, 2 and 3 associations
        - cotrecho x parameters for type 1, 2, 3 and 4
        - cotrecho x solver/type

    Args:
        dict_bho_mini_t1_post (dict) :: {cotrecho:mini}
        dict_bho_mini_t2_post (dict) :: {cotrecho:mini}
        dict_bho_mini_t3_post (dict) :: {cotrecho:mini}
        dict_parameters_t1 (dict) ::  {cotrecho:{parameters}}
        dict_parameters_t2 (dict) ::  {cotrecho:{parameters}}
        dict_parameters_t3 (dict) ::  {cotrecho:{parameters}}
        dict_parameters_t4 (dict) ::  {cotrecho:{parameters}}
        dict_bho_solver (dict)    ::  {cotrecho:solver}
        pathout(str,optional) ::  path (folder) where to save pickle files

    Returns:
        None

    Notes:
        - 'dict_bho_mini_t<type>_post' area generated at
            'def validate_t123'
        - 'dict_parameters_t<type>_post' are generated at
            'def define_parameter_t<type>'

    TODO: declare/adjust path to dump

    """

    #dicts of parameters {cotrecho:{params},...}
    with open(pathout+'dict_parameters_t1.pickle','wb') as f:
        pickle.dump(dict_parameters_t1,f)

    with open(pathout+'dict_parameters_t2.pickle','wb') as f:
        pickle.dump(dict_parameters_t2,f)

    with open(pathout+'dict_parameters_t3.pickle','wb') as f:
        pickle.dump(dict_parameters_t3,f)

    with open(pathout+'dict_parameters_t4.pickle','wb') as f:
        pickle.dump(dict_parameters_t4,f)


    #dicts of association {cotrecho:{mini},...}
    with open(pathout+'dict_bho_mini_t1_post.pickle','wb') as f:
        pickle.dump(dict_bho_mini_t1_post,f)

    with open(pathout+'dict_bho_mini_t2_post.pickle','wb') as f:
        pickle.dump(dict_bho_mini_t2_post,f)   #contains t1 outlets

    with open(pathout+'dict_bho_mini_t3_post.pickle','wb') as f:
        pickle.dump(dict_bho_mini_t3_post,f)

    # type 4 does not have an association with mini
    #with open('dict_bho_mini_t4_post.pickle','wb') as f:
    #    pickle.dump(dict_bho_mini_t4_post,f)

    # solver!
    with open(pathout+'dict_bho_solver.pickle','wb') as f:
        pickle.dump(dict_bho_solver,f)

    print(" - the dicts were successfully saved!")


    return None



def read_the_dicts(pathin='./'):
    """
    Read main dictionaries
        - cotrecho x mini for type 1, 2 and 3 associations
        - cotrecho x parameters for type 1, 2, 3 and 4
        - cotrecho x solver/type

    Args:
        pathin (str,optional) :: path (folder) from where to read pickle files

    Returns:
        the_dicts (dict) :: container for the main dictionaries
                            keys = [
                                'dict_bho_mini_t1_post',
                                'dict_bho_mini_t2_post',
                                'dict_bho_mini_t3_post',
                                'dict_parameters_t1',
                                'dict_parameters_t2',
                                'dict_parameters_t3',
                                'dict_parameters_t4',
                                'dict_bho_solver']

    Notes:
        - files '<name_of_dict>.pickle' compatible with 'def dump_dicts()'
        - files '<name_of_dict>.pickle' must be in current path

    TODO: declare/adjust input path
    """

    # load dicts of association {cotrecho:{mini},...} for type 1,2,3
    with open(pathin+'dict_bho_mini_t1_post.pickle','rb') as f:
        dict_bho_mini_t1_post = pickle.load(f)

    with open(pathin+'dict_bho_mini_t2_post.pickle','rb') as f:
        dict_bho_mini_t2_post = pickle.load(f)

    with open(pathin+'dict_bho_mini_t3_post.pickle','rb') as f:
        dict_bho_mini_t3_post = pickle.load(f)

    # load dicts of parameters {cotrecho:{params},...} for type 1,2,3 and 4
    with open(pathin+'dict_parameters_t1.pickle','rb') as f:
        dict_parameters_t1 = pickle.load(f)

    with open(pathin+'dict_parameters_t2.pickle','rb') as f:
        dict_parameters_t2 = pickle.load(f)

    with open(pathin+'dict_parameters_t3.pickle','rb') as f:
        dict_parameters_t3 = pickle.load(f)

    with open(pathin+'dict_parameters_t4.pickle','rb') as f:
        dict_parameters_t4 = pickle.load(f)

    # load dict of solver for types 1,2,3 and 4
    with open(pathin+'dict_bho_solver.pickle','rb') as f:
        dict_bho_solver = pickle.load(f)

    tuple_of_dicts = (
        dict_bho_mini_t1_post,
        dict_bho_mini_t2_post,
        dict_bho_mini_t3_post,
        dict_parameters_t1,
        dict_parameters_t2,
        dict_parameters_t3,
        dict_parameters_t4,
        dict_bho_solver,
        )

    print(" - the dicts successfully loaded")

    labels = [
        'dict_bho_mini_t1_post',
        'dict_bho_mini_t2_post',
        'dict_bho_mini_t3_post',
        'dict_parameters_t1',
        'dict_parameters_t2',
        'dict_parameters_t3',
        'dict_parameters_t4',
        'dict_bho_solver',
        ]

    # convert tuples to dicts
    the_dicts = dict(zip(labels,tuple_of_dicts))

    return the_dicts





#-----------------------------------------------------------------------------
# FUNCTIONS FOR JSON INPUT/OUTPUT
#-----------------------------------------------------------------------------
def dump_json(input_dict, filename):
    """
    Dump dictionary to a json file
    """
    with open(filename,'w') as f:
        json.dump(input_dict,f)