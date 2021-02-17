# -*- coding: utf-8 -*-
"""

@author: Mino Sorribas
"""

import pandas as pd
import geopandas as gpd



#-----------------------------------------------------------------------------
# FUNCTIONS TO INSERT NEW COLUMNS IN BHO TABLE AND EXPORT AS GEOPACKAGE
#-----------------------------------------------------------------------------

def f_dicts_to_bho_gpkg(
        gdf_tble_bho,
        dict_bho_targets,
        tkey = 'cotrecho',
        simplify = True,
        to_gpkg = True,
        to_xlsx = True,
        prefix = 'base',
        suffix = '',
        ):
    """
    Maps dictionary values into new columns of gdf_tble_bho
        then, optional, export .GPKG and/or .XLSX
        - each key of dict_bho_targets makes a new column
        - each new column (pd.Series) has values mapped (.map) from the
            inner target dictionaries {tkey:values}
                where 'tkey is the target column name for the mapping

    Args:
        gdf_tble_bho (gpd.DataFrame) :: drainage table from BHO

        dict_bho_targets(dict) :: dictionary of target dicionaries (see Usage)

        tkey (string) :: column of gdf_tble_column used to map keys

        simplify (bool) :: True to select some columns
                           'cotrecho','cobacia',
                           'nucomptrec','nuareacont','nuareamont',
                           'nutrjus','dedominial','nustrahler',
                           'nuordemcda','cocursodag','cocdadesag','nudistbact'

        to_gpkg (bool) :: True to export geopackage

        to_xlsx (bool) :: True to export table in xlsx format

        prefix (str) :: <prefix>_mgbbhods_<suffix>.[xlsx/gpkg]
                        default = 'base'

        suffix (str) :: <prefix>_mgbbhods_<suffix>.[xlsx/gpkg]
                        default = ''


    Returns:
        gdw (pd.DataFrame) :: gdf_tble_bho with new columns

    Notes:
        - it won't export .gpkg if there is 'no geometry' (only pd.DataFrame)

    Usage:
        example:

        >> df_tble_bho_new = f_map_dicts_to_bho(df_tble_bho,dict_bho_targets)

        where:

        dict_bho_targets = {
            'mini_t1': {cotrecho: value_mini_1,...,cotrecho_n:value_mini_n},
            'mini_t2': {cotrecho: value_mini_1,...,cotrecho_n:value_mini_n},
            'mini_t3': {cotrecho: value_mini_1,...,cotrecho_n:value_mini_n},
            'q95': {cotrecho: value_q95_1,...cotrecho_n:value_q95_n}
            'tipo': {cotrecho: value_tipo_1,...cotrecho_n:value_tipo_n,}
            ...}

        OR
        dict_bho_targets = {'mini_t1': dict_bho_mini_t1,
                            'mini_t2': dict_bho_mini_t2,
                            ...
                            'tipo': dict_bho_solver,
                            'q95': dict_bho_q95,
                            ...
                            }

    """

    print(" Updating dataframe and exporting... ")

    # make a "working" copy
    #gdw = gdf_tble_bho.copy(deep=True)
    gdw = gdf_tble_bho

    # insert data from dictionaries into dataframe (use)
    for k,v in dict_bho_targets.items():
        target, dict_bho_target = k,v
        print (" - make column {}".format(k),end='')
        gdw[target] = gdw[tkey].map(dict_bho_target)
        print (" done.")

        #TODO: check .loc for caveats/slices


    # filenames
    file_xlsx = "{}_mgbbhods_{}.xlsx".format(prefix,suffix)
    file_gpkg = "{}_mgbbhods_{}.gpkg".format(prefix,suffix)


    # check geometry
    if 'geometry' in gdw.columns:
        flag_geom = True
    else:
        flag_geom = False


    # simplify columns
    allcols = list(gdw.columns)
    newcols = list(dict_bho_targets.keys())
    sel = allcols[:]


    if simplify:
        sel = ['cotrecho','cobacia',
               'nucomptrec','nuareacont','nuareamont',
               'nutrjus','dedominial','nustrahler',
               'nuordemcda','cocursodag','cocdadesag','nudistbact'
               ]
        sel = sel + ['geometry'] if flag_geom else sel

        sel = sel + newcols

    # selected columns
    gdw = gdw[sel]

    # export xlsx
    if to_xlsx:
        print(" - saving {}...".format(file_xlsx),end='')
        if flag_geom:
            gdw_xls = gdw.drop('geometry',axis=1)
            gdw_xls.to_excel(file_xlsx)
        else:
            gdw.to_excel(file_xlsx)
        print(" done.")



    # export gpkg
    if to_gpkg:
        print(" - saving {}...".format(file_gpkg),end='')
        if flag_geom:
            gdw.to_file(file_gpkg,driver='GPKG')
            print(" done.")

        else:
            print(" fail: missing geometry.")

    return gdw