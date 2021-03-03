# -*- coding: utf-8 -*-
"""
Main functions for OPerations
  for the preprocessing of topologies and parameters
  of the MGB-BHO Downscaling

@author: Mino Sorribas

@todo:
    - describe required columns from input datasets
    - associate_domain using bbox OR pre-processed midpoints (reduce memory)

@info:
    - the @block_print decorator cane be used to enable-disable printing.


"""
import sys
import pickle
import time
from collections import defaultdict
import warnings
import itertools

import numpy as np
import pandas as pd
import geopandas as gpd

from funcs_decorators import *



def associate_bho_mini_domain(gdf_tble_bho,
                              gdf_mgb_catchments,
                              node_pos = 0.5,
                              mgb_version = 'MGB-AS',
                              pts_to_gpkg = None,
                              to_pickle = True,
                              ):

    """
    Associates BHO drainage (cotrecho) with MGB catchments (mini)
        using (mid)points (from BHO drainage) in polygons (MGB catchments)
        thus, it defines the background domain for the MGB-BHO Downscaling
        and returns as dict_bho_mini = {cotrecho:mini,...}

    Args:
        gdf_tble_bho (gpd.GeoDataFrame) :: BHO drainage (polyline)

        gdf_mgb_catchments (gpd.GeoDataFrame) :: MGB catchments (polygon)

        node_pos (int) :: position along the BHO feature for inpolygon

        mgb_version (str) :: required to identify 'mini' column

        pts_to_gpkg (str) :: (optional) filename .gpkg to export midpoints

    Returns:
        dict_bho_mini(dict) :: mapping of the domain between BHO and MGB
                                cotrecho as key, mini as value
                                e.g. {cotrecho:mini,...}
                               also called "dict_bho_domain"

    Notes:
        - mgb_version must be declared as key of variable mini_cols,
        which handles different versions of MGB shapefile columns (attr table)

    TODO:
        - check equality of CRS
        - work with projected CRS for larger acccuracy
        (complicated for large areas, better to make new script!)
        - if no memory available:
            try processing by mini -> like "gpd.read_file(points,bbox=mini[i])"
            using a pre-processed bho points.
        - pathout

    """
    warnings.filterwarnings('ignore')

    # setup for versions of mgb
    mini_cols_target = {
        'MGB-AS': 'Mini',
        'MGB-QGIS': 'Mini_ID',
        }

    # make parser for mini header
    str_mini = mini_cols_target[mgb_version]   #'Mini' or 'Mini_ID'

    # select MGB catchments polygons and rename header to 'mini'
    cols = [str_mini, 'geometry']
    pols = gdf_mgb_catchments[cols]    #drop everything
    pols = pols.rename(columns = {str_mini:'mini'} )

    # make geodataframe with midpoint of bho drainage features
    midpts = gdf_tble_bho.interpolate(node_pos, normalized=True)
    points = gpd.GeoDataFrame(gdf_tble_bho['cotrecho'], geometry = midpts, crs="EPSG:4674")


    # spatial join - points within pols
    #TODO: i think this is making a copy! >> not good idea for many points/pols
    indexed_pols = pols.set_index('mini')
    indexed_pts  = points.set_index('cotrecho')
    point_in_pols = gpd.tools.sjoin(indexed_pts, indexed_pols, how='left', op='within')

    # table points and mini (index_right)
    tble_bho_mini = point_in_pols[point_in_pols['index_right'].notna()]

    # save points in disk
    if pts_to_gpkg:
        tble_bho_mini.to_file(pts_to_gpkg,driver='GPKG')


    # make dictionary {cotrecho:mini,...}
    dict_bho_mini = tble_bho_mini['index_right'].to_dict()

    # adjust dtypes -> int
    dict_bho_mini = {int(k):int(v) for k,v in dict_bho_mini.items()}


    # drop to pickle
    if to_pickle:
        with open('dict_bho_domain.pickle','wb') as f:
            pickle.dump(dict_bho_mini,f)


    warnings.filterwarnings('always')
    return dict_bho_mini



def make_tble_t0(df_tble_mini, df_tble_bho, file_bho_inter):
    """
    Make initial table (type 0) like the MGB x BHO domain and
        save as "table_t0.xlsx"

    Args:
        df_tble_mini (pd.DataFrame) :: table of mini.gtp (.xlsx)
        df_tble_bho (pd.DataFrame) :: table of BHO drainage
        fileout_bho_inter (str) :: pathfile to BHO points intersected with MGB

    Returns:
        df_pts (pd.DataFrame) :: initial table of BHO x MGB for domain

    Notes:
         - file_bho_inter can be made with 'pts_to_gpkg'
         function funcs_op.associate_bho_mini_domain

    """

    # get coordinates from bho points (intersected with mgb)
    gdf_pts = gpd.read_file(file_bho_inter)
    gdf_pts['xp'] = gdf_pts.geometry.apply(lambda p: p.x)
    gdf_pts['yp'] = gdf_pts.geometry.apply(lambda p: p.y)

    # drop geometry and adjust header for 'mini'
    #df_pts = gdf_pts.drop('geometry',axis=1)
    df_pts = gdf_pts
    df_pts = df_pts.rename(columns = {'index_right':'mini'})

    # merge with mini
    sel_mini = ['mini','aream_km2','xcen','ycen'] #mgb coordinates
    df_aux = df_tble_mini[sel_mini]
    df_pts = pd.merge(df_pts,df_aux)

    # merge with bho
    #sel_bho = ['cotrecho','cobacia','nuareamont'] #bho coordinates
    #df_aux = df_tble_bho[sel_bho]
    df_pts = pd.merge(df_pts,df_tble_bho,on='cotrecho')

    # rename according to .read_tble_t0
    hmap = {'xcen':'xc','ycen':'yc'}
    df_pts = df_pts.rename(columns=hmap)

    # save as excel table
    df_xls = df_pts.drop('geometry',axis=1)
    df_xls.to_excel('table_t0.xlsx',index=False)

    # save as gpkg
    #df_pts.to_file('table_t0.gpkg',driver='GPKG') #some dtype error here

    return df_xls





def associate_bho_mini_t3(dict_bho_mini):
    """
    Associates BHO drainage (cotrecho) with MGB catchments (mini)
        for type 3 features
        and returns as dict_bho_mini = {cotrecho:mini,...}

    Args:
        dict_bho_mini(dict) :: mapped domain betwenn BHO and MGB
                                cotrecho as key, mini as value
                                e.g. {cotrecho:mini,...}

    Returns:
        dict_bho_mini_t3(dict) :: mapping between BHO and MGB for type 3
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}
    """

    # "background" association for type 3 equals to the domain
    dict_bho_mini_t3 = dict_bho_mini.copy()

    return dict_bho_mini_t3



@block_print   #imported from funcs_decorators.
def define_parameters_t3(dict_bho_mini_t3, df_tble_mini, df_tble_bho):
    """
    Defines parameters for type 3 features

    Args:
        dict_bho_mini_t3(dict) :: mapping between BHO and MGB for type 3
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}

        df_tble_mini(pd.DataFrame) :: MGB topology table

        df_tble_bho(pd.DataFrame) :: BHO drainage table

    Returns:
        dict_parameters_t3( defaultdict(dict) ) ::
            parameters (values,dict) for each cotrecho (key)
            e.g. {cotrecho:{parameters},...}

    """
    dict_parameters_t3 = defaultdict(dict)

    conta = 0

    itot = len(dict_bho_mini_t3)
    tot = float(itot)
    hh = 100./tot

    for cotrecho, mini in dict_bho_mini_t3.items():
        conta = conta+1
        print("  extracting type 3 parameters: {}%".format(round(hh*conta,2)))
        # mgb related parameters
        imini = df_tble_mini['mini'] == mini
        area_km2 = df_tble_mini.loc[imini,'area_km2'].values[0]
        aream_km2 = df_tble_mini.loc[imini,'aream_km2'].values[0]

        # bho related parameters
        ibho = df_tble_bho['cotrecho'] == cotrecho
        nuareamont = df_tble_bho.loc[ibho,'nuareamont'].values[0]

        # fix digits
        nuareamont = round(nuareamont,6)
        cint = int(cotrecho)
        parameters = {
            'mini':[mini],            #mgb reference
            'area_km2':[area_km2],       #local drainage area (mini)
            'aream_km2':[aream_km2],     #total drainage area (mini)
            'nuareamont':[nuareamont],   #total drainage area (cotrecho)
            # useful for list and serialization (json)
            'cotrecho':[cint],
            }

        dict_parameters_t3[cint] = parameters

    return dict_parameters_t3



def associate_bho_mini_t1(df_tble_t1):
    """
    Associates BHO drainage (cotrecho) with MGB catchments (mini)
        for type 1 features
        and returns as dict_bho_mini = {cotrecho:mini,...}

    Args:
        df_tble_t1(pd.DataFrame) :: table type 1

    Returns:
        dict_bho_mini_t1(dict) :: mapping between BHO and MGB for type 1
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}

    Notes:
        - df_tble_t1 must be compatible to funcs_io.read_tble_t1()

    TODO:
        - implement algorithm from matlab

    """

    # build dictionary for type 1 association {cotrecho:mini...}
    tmap = {'bho_cotrecho':int, 'mini':int, 'area_ratio':float}
    sel_t1 = ['bho_cotrecho', 'mini', 'area_ratio']
    df_aux_t1 = df_tble_t1[sel_t1].astype(tmap).set_index('bho_cotrecho')
    dict_bho_mini_t1 = df_aux_t1.to_dict()['mini']

    return dict_bho_mini_t1



def define_parameters_t1(df_tble_t1):
    """
    Defines parameters for type 1 feature

    Args:
        df_tble_t1 (gpd.DataFrame) :: table type 1

    Returns:
        dict_parameters_t1( defaultdict(dict) ) ::
            parameters (values,dict) for each cotrecho (key)
            e.g. {cotrecho:{parameters},...}

    Notes:
        - this functions mirrors 'def associate_bho_mini_t1()' and
        includes additional line to extract parameters from the table.


    """

    # build dictionary for type 1 association {cotrecho:mini...}
    tmap = {'bho_cotrecho':int, 'mini':int, 'area_ratio':float,'bho_nuareamont':float}
    sel_t1 = ['bho_cotrecho', 'mini', 'area_ratio','bho_nuareamont']
    df_aux_t1 = df_tble_t1[sel_t1].astype(tmap).set_index('bho_cotrecho')

    df_aux_t1 = df_aux_t1.rename(columns={'bho_nuareamont':'nuareamont'})


    # build dictionary with parameters for type 1 {cotrecho: {parameters} ...}
    # {cotrecho:{'mini':,'area_ratio':,},...}
    dict_parameters_t1 = df_aux_t1.to_dict('index')

    return dict_parameters_t1




def define_bho_target_t12(df_tble_bho, area_threshold_t12):
    """
    Define the target bho drainage for types 1 and 2 based on area threshold
      (selected to be similar to the MGB drainage network)

    Args:
        df_tble_bho (pd.DataFrame) :: BHO drainage table

        area_threshold_t12 (float) :: threshold for 'main drainage network'

    Returns:
        list_bho_target_t12(list) :: values of 'cotrecho' for the target t12

    Notes:
        - area_threshold_t12 => min(aream_km2) from mini
          -> drainage network' similar to the MGB drainage
        - area_threshold_t12 => 0
          -> all type 3 (headwaters) will be type 4
        - area_threshold_t12 => +inf
          -> all type 4 in main stream?!


    """
    idx = df_tble_bho['nuareamont']>=area_threshold_t12
    df_target = df_tble_bho.loc[idx,'cotrecho']

    group_bho_target_t12 = set(list(df_target))
    return group_bho_target_t12




def merge_topologies_t1(df_tble_t1, df_tble_mini, df_tble_bho):
    """
    Merge topology (both MGB and BHO) at table type 1
        which is required for type 2 connectivity analyses

    Args:
        df_tble_t1(pd.DataFrame) :: table type 1

        df_tble_mini(pd.DataFrame) :: MGB topology table

        df_tble_bho(pd.DataFrame) :: BHO drainage table

    Returns:
        df_tble_topo_t1(pd.DataFrame) :: merged topologies on type 1 table.

    """

    # merge mgb topology into table type 1
    sel_t1 = ['mini','bho_cotrecho']
    sel_mgb = ['mini','minijus','ordem']
    df_merged = pd.merge(left = df_tble_t1[sel_t1],
                       right = df_tble_mini[sel_mgb],
                       on = 'mini',
                       how = 'inner',
                       )

    # adjust header related to bho, before next merging
    df_merged = df_merged.rename(columns={'bho_cotrecho':'cotrecho'})


    # merge bho topology into table type 1
    sel_bho = ['cotrecho', 'nutrjus','cobacia','nuareacont','nuareamont']
    df_merged  = pd.merge(left = df_merged,
                         right = df_tble_bho[sel_bho],
                         on = 'cotrecho',
                         how = 'inner'
                         )

    # adjust some of the dypes
    # note: useful for exporting
    df_tble_topo_t1 = df_merged.astype({'cotrecho':int,'mini':int,'minijus':int})

    return df_tble_topo_t1


@block_print
def check_route_t2(codafl, codexu, df_tble_bho):
    """
    Check the connectivity between codafl and codexu (both cotrechos of BHO)
        and returns the route (values) downstream until codexu

    Args:
        codafl (int) :: cotrecho of the starting "inlet" feature
        codexu (int) :: cotrecho of the target "outlet" feature
        df_tble_bho (pd.DataFrame) :: BHO-drainage (trecho) table

    Returns:

        routes (dict) :: codafl as key, the value is a list of downstream
                         cotrechos until codexu (included in last position)
                         the list won't contain the starting postition 'codafl'
                         e.g. {codafl:[cotrecho,...,codexu]}


        status (int)  :: success (1) or error flags (10,20,...)
                        {1: route is good
                         0: route didn't find further features downstream
                         >1: route with more than 1 feature downstream (not expected)
                         20: route reaches the coastal line
                         30: route is long enough to assume an error (>30 steps)
                         40: route drainage area > target area
                         }


    """

    # initialize dictionary for the route that begins at codafl
    routes = {}
    routes[codafl] = []          #-> dict compatible with global routes.

    # total drainage area at the reference 'codexu'
    iref = df_tble_bho['cotrecho'].isin([codexu])
    arearef = df_tble_bho.loc[iref,'nuareamont'].values[0]

    # tolerance and counter for downstream steps without finding codexu
    tol = 30
    conta = 1


    # loop for downstream walk (at bho) from codafl towards codexu
    desce = True
    codigo = codafl   #starting cotrecho
    print(" > walking route from {}".format(codafl) )
    while desce:

        # find index of current cotrecho
        iatual = df_tble_bho['cotrecho'].isin([codigo])

        # downstream cotrecho
        codjus = df_tble_bho.loc[iatual,'nutrjus']  # <- pd.Series

        # print on screen
        ##print(" - current: {}".format(codigo) )

        # sets process status based on the downstream connection (if available)
        status = len(codjus)

        if status == 1:
            # found a valid feature downstream -> append to the route
            codjus = codjus.values[0]       #get value from pd.Series
            routes[codafl].append(codjus)

            # test if is the end position
            if codjus == codexu:
                print(" - done: cotrecho {} walked to {} in {} steps".format(codafl,codexu,conta))
                desce = False
                continue
                #note: codexu is also stored in the list

            # updates cotrecho for the next step -> make the downstream walk!
            codigo = codjus

        elif status == 0:
            # end of line -> fails and drop current route
            print(" - fail: cotrecho {} without nutrjus".format(codigo))
            desce = False
            routes.pop(codafl)        # remove current route
            continue

        # hard tests -> results in end of program
        elif status > 1:
            # more than one drainage downstream -> unexpected case! check!
            print(" -issue: cotrecho {} drains to more than one {}".format(codigo,codjus))
            sys.exit(" UNEXPECTED ERROR - funcs_op.check_route_type2")
            break

        else:
            # unexpected conditions
            print(" -issue: cotrecho {} unexpected condition ".format(codigo))
            sys.exit(" UNEXPECTED ERROR - funcs_op.check_route_type2")
            break


        # soft tests -> ensures a lost walk don't last for too long.

        # test for coastline (dedominial = 'Linha de Costa')
        dedom = df_tble_bho.loc[iatual,'dedominial'].values[0]
        if dedom == 'Linha de Costa':
            status = 20
            desce = False
            routes.pop(codafl)      # remove current route
            continue

        # test for long routes
        conta = conta + 1
        if conta > tol:
            status = 30
            desce = False
            routes.pop(codafl)      # remove current route
            continue

        # test for drainage area incoherence (e.g. larger than current)
        areacum = df_tble_bho.loc[iatual,'nuareamont'].values[0]
        if areacum > arearef:
            status = 40
            desce = False
            routes.pop(codafl)      # remove current route
            continue

    return routes, status



@block_print
def screening_candidates_t2(df_tble_topo_t1, df_tble_mini, df_tble_bho):
    """
    Screening candidates routes for type 2 association
        which are located "inside a mgb catchment" between upstream inlets
        and the downstream outlets, both associated as type 1

      For each mini/cotrecho (row in table type 1)
        - check if all upstream mgb catchments have a cotrecho associated (type 1)
            - check if the associated cotrecho flows downstream into cotrecho

    Args:
        df_tble_topo_t1(pd.DataFrame) :: merged topologies on type 1 table.
        df_tble_mini(pd.DataFrame) :: MGB topology table
        df_tble_bho(pd.DataFrame) :: BHO drainage table

    Returns:
        dict_routes_t2 (dict) :: codafl as key, the value is a list of downstream
                                 cotrechos until codexu (included in last position)
                                 e.g.{codafl:[cotrecho,...],...}

        dict_mini_afl_t2 (dict) :: mini as key, starting cotrecho of a route as value.
                                e.g.{ mini:[cotrecho_afl1,cotrecho_afl2,...],...}

    Notes:
        - the last value in dict_routes_t2 contains the type 1 outlet
            e.g {codafl:[cotrecho_, ... , type1_cotrecho],...}
            which is used for calculating the local area factor later

    Dependencies:
        - requires function 'def check_route_t2()'



    """

    # "progress bar"
    tot = float(len(df_tble_topo_t1))
    hh = 100./tot

    # begin timer and iteration counter
    start = time.time()
    conta = 0

    # main dictionaries for results
    dict_routes_t2 = {}
    dict_mini_afl_t2 = {}

    # additional (if wants to check errors/conditions)
    dict_t1_headwater = {}
    dict_t1_miss = {}
    dict_t1_broken = {}

    # loop over table 1 targets
    for row in df_tble_topo_t1.itertuples():

        conta = conta+1
        print(" screening: {}%".format(round(hh*conta,4)))

        # current row
        mini = row.mini
        ordem = row.ordem
        codexu  = row.cotrecho   # table 1 outlet
        cobacia = row.cobacia

        print("  - mini: {} cotrecho: {} cobacia: {} ".format(mini,codexu,cobacia))

        # ignore if cant find type 1 association
        if np.isnan(codexu):
            print(' -- Couldnt find {} ( funcs_op.screening_candidates_2 )--'.format(cotrecho))
            break
            #_ = input()
            #continue

        # save mgb headwaters
        if ordem == 1:
            dict_t1_headwater[codexu] = mini

        # neighbour upstream mgb catchments (in reference to full topology)
        jmon = df_tble_mini['minijus'].isin([mini])
        minimon = df_tble_mini.loc[jmon,'mini']

        # search for minimon in tble_topo_t1 (to see if upstream is also in type 1)
        iaflu = df_tble_topo_t1['minijus'].isin([mini])
        afl_mini = df_tble_topo_t1.loc[iaflu,'mini']
        afl_cotrecho = df_tble_topo_t1.loc[iaflu,'cotrecho']


        # check if upstream mgb neighbour is missing in type 1 ("not associated")
        missmon = set(minimon).symmetric_difference(set(afl_mini))

        # if it fails... it considers an incomplete pathway for type 2
        if len(missmon)>0:
            dict_t1_miss[codexu] = mini
            continue


        # check if all upstream neighbours the flows downstream the BHO to codexu!
        local_routes = {}
        fail = False
        for codafl in afl_cotrecho:

            # call function to check the current route
            route,status = check_route_t2(codafl,codexu,df_tble_bho)

            # evaluate resulting status
            if status == 1:

                # additional test:
                # cotrechos in route can't "overpass" any cotrecho in tble t1 (outlet)
                list_route = route.get(codafl)
                if len(list_route)>1:
                    codinside = list_route[:-1]
                    runover = df_tble_topo_t1[df_tble_topo_t1['cotrecho'].isin(codinside)]
                    if len(runover)>0:
                        status = 50
                        fail = True
                        print(" - status 50 (funcs_op.screening_candidates_2)")
                        continue
                        #TODO: could just break in 1st fail, but wont record


                # accept route
                local_routes.update(route)
            else:
                fail = True
                #dict_mini_problemas[mini].append(codafl)
                ##break #TODO: could just break in 1st fail, but wont record


        # updates dictionary with type 2 fail.
        if fail:
            dict_t1_broken[codexu] = mini
            continue


        # --
        # SO FAR, SO GOOD!
        # this catchment has all internal routes accepted for type 2.
        # --

        # note: it may contain "fake type 2"
        # -> flows direct into another type 1
        # -> we keep for multiple affluents


        # update global container of "cotrechos in the each route (dict)"
        # {cotrecho_afl:[cotrecho1,cotrecho2,...codexu],...}
        dict_routes_t2.update(local_routes)

        # update global container of "list of cotrechos affluent to each mini'
        # {mini:[cotrecho_afl1 ,cotrecho_afl2, ...]}
        dict_mini_afl_t2[mini] = list(local_routes.keys())


    finish = time.time()
    print("  ... took {} seconds".format(round(finish-start,1)) )
    return dict_routes_t2, dict_mini_afl_t2


@block_print
def associate_bho_mini_t2(dict_mini_afl_t2, dict_routes_t2, df_tble_mini):
    """
    Associates type 2 BHO drainage (cotrecho) with MGB catchments (mini)
        based on pre-screened routes

        for each mini with candidates to type 2
            loop over each upstream inlets in dict_mini_afl_t2[mini]:
             1. get the downstream route (dict_routes_t2)
             2. associates each cotrecho in routes with mini

    Args:
        dict_mini_afl_t2 (dict) :: mini as key, starting cotrecho of a route as value.
                                  e.g.{ mini:[cotrecho_afl1,cotrecho_afl2,...],...}

        dict_routes_t2 (dict) :: codafl as key, the value is a list of downstream
                                 cotrechos until codexu (included in last position)
                                 e.g. {cotrecho_afl1:[cotrecho,...],...}

        df_tble_mini(pd.DataFrame) :: MGB topology table

    Returns:
        dict_bho_mini_t2 (dict):: mapping betwenn BHO and MGB for type 2
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}
                                      (see notes!)

        dict_mini_coddum_t2 (defaultdict(dict)) :: mini with "dummy type 2"
                                                   {mini:cod_afl}

    Notes:
        - dict_bho_mini_t2 contains cotrechos from inner routes
            AND all type 1 outlets (end of routes)
        - mini with "dummy type 2" don't have an inner route, a unique type 1
            inlet has a direct connection to a type 1 outlet.

    """

    # initialize
    dict_bho_mini_t2 = {}

    # stores dummy type 2
    dict_mini_coddum_t2 = defaultdict(list) # armazena as conexoes diretas


    # loop each mini with type 2 routes
    hh = 100./float(len(dict_mini_afl_t2))
    conta = 0
    for k,v in dict_mini_afl_t2.items():

        mini, afluentes = k, v   #current  mini & starting points of each route

        conta = conta+1
        print(" associating type 2: {}%".format(round(hh*conta,4)))


        # check dummy route
        nafl = len(afluentes)
        if nafl==1:
            codafl = afluentes[0]
            if len(dict_routes_t2[codafl])==1: # test unique step in route
                codigo = dict_routes_t2[codafl][0]        # last cotrecho
                dict_mini_coddum_t2[mini].append(codigo)  # save

                #TODO: "hard test" -> compares codigo with type 1
                # require df_tble_topo_t1 and actually shouldnt happen at this point
                continue

        # merge lists of cotrechos of all routes
        cotrechos_in_routes = [dict_routes_t2[afl] for afl in afluentes]
        #[[1,2],[1,2,3],...]->[1,2,3,1,2,3,...]
        list_merged = list(itertools.chain.from_iterable(cotrechos_in_routes))
        #[1,2,3,1,2,3,...]->[1,2,3]
        list_unique = list(set(list_merged))

        # stores cotrechos of routes into main dictionary of type 2
        # note: it also contains the last cotrecho (which is type 1)
        for codigo in list_unique:
            dict_bho_mini_t2[codigo] = mini

    # could extract downscaling parameters here...
    # but better keep it separated

    # ensures dtypes as integer
    dict_bho_mini_t2 = {int(k):int(v) for k,v in dict_bho_mini_t2.items()}

    return dict_bho_mini_t2, dict_mini_coddum_t2



@block_print
def define_parameters_t2(dict_bho_mini_t2,
                         dict_mini_afl_t2,
                         dict_routes_t2,
                         dict_bho_mini_t1,
                         df_tble_bho):
    """
    Defines parameters for type 2 features

    Args:
        dict_bho_mini_t2 (dict) :: mapping between BHO and MGB for type 2
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}

        dict_mini_afl_t2 (dict) :: mini as key, starting cotrecho of a route as value.
                                  e.g.{ mini:[cotrecho_afl1,cotrecho_afl2,...],...}

        dict_routes_t2 (dict) :: codafl as key, the value is a list of downstream
                                 cotrechos until codexu (included in last position)
                                 e.g. {cotrecho_afl1:[cotrecho,...],...}

        df_tble_bho(pd.DataFrame) :: BHO drainage table

        dict_bho_mini_t1(dict) :: mapping between BHO and MGB for type 1
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}

    Returns:
        dict_parameters_t2( defaultdict(dict) ) ::
            parameters (values,dict) for each cotrecho (key)
            e.g. {cotrecho:{parameters},...}

        dict_bho_parameters_t2[c] = {
            'cotrecho':[c],                  # codigo cotrecho -> para busca
            'mini_ref':[mini],                 # mini referencia
            'fracao_area':[interno_acum[c]] ,    # % area acumulada local (bho)
            'mini_mon':[interno_minimon[c]],     # minibacias afluentes ao trecho
            }

    Notes:
         - returns dictionary, as it facilitate use in python
         - stores values in list, so it can be serializable in json
         - repeats 'cotrecho', so it is easier to serialize parameters.

    #TODO: INCLUIR MINI AFLUENTE

   """


    dict_bho_parameters_t2 = defaultdict(dict)


    # identify catchments (mini) with type 2 routes
    miniaux = list(dict_bho_mini_t2.values())
    miniref = list(set(miniaux))

    # loop each catchment
    hh = 100./float(len(miniref))
    conta = 0
    for mini in miniref:

        conta = conta+1
        print("  extracting type 2 parameters: {}%".format(round(hh*conta,2)))

        # initialize dicts to map relative positions
        #  - such as for each inner cotrecho (key)
        #    a) makes a list of "catchments upstream of cotrecho"
        #    b) makes a list of "inlet cotrechos upstream of cotrecho"
        #  - which are used to extract parameters such as local area factor
        d_interno_minimon = defaultdict(list)    #{cotrecho_interno:[minimon]}
        d_interno_afl     = defaultdict(list)    #{cotrecho_interno:[cotrecho_afl]}

        # loops over 'inlet cotrechos' of current mini
        for codafl in dict_mini_afl_t2[mini]:

            # identify upstream mini (must be in type 1 dict!)
            miniafl = dict_bho_mini_t1.get(codafl,None)
            if miniafl is None:
                # error: didnt find upstream mini in dict_bho_mini_t1
                print(" - issue: cotrecho {} (.define_parameters_t2)".format(cotrecho))
                break

            # get cotrechos in this route
            cotrechos_in_route = dict_routes_t2[codafl]

            # check dummy route
            #assert len(cotrechos_in_route)>1,"erro!"

            # get partial info in route
            ##testing
            ##codexu_n1 = cotrechos_in_route[-1]              #only outlet (t1)
            ##codigo_ini_ao_fim = [afl] + cotrechos_in_route  #include inlet
            ##codigos_work = cotrechos_in_route[:-1]          #except outlet
            cotrechos_work = cotrechos_in_route[:]            #whole route

            for c in cotrechos_work:
                d_interno_minimon[c].append(miniafl)  #include tag "upstream mini"
                d_interno_afl[c].append(codafl)       #include tag "upstream codafl"


        # store list of all mini upstream of current mini
        list_minimonall = d_interno_minimon.values()
        list_minimonall = set(list(itertools.chain.from_iterable(list_minimonall)))
        list_minimonall = list(list_minimonall)


        # we tagged the relative position for each cotrecho
        # so we know which cotrecho is downstream of upstream mini/codafl
        # ...

        #---------------------------------------------------------
        # calculate local cumulative drainage area (based on BHO)
        #---------------------------------------------------------
        # list of cotrechos to be processed
        internos = list(d_interno_afl.keys())

        # (1) each feature starts with its total drainage area
        interno_acum = {}
        for c in internos:
            ic = df_tble_bho['cotrecho'] == c
            areap = df_tble_bho.loc[ic,'nuareamont'].to_numpy()   #at point
            interno_acum[c] = areap                   # np.array for calcs

        # (2) removes "upstream inlets drainage area" of each feature
        for c in internos:
            for codafl in d_interno_afl[c]:
                ia = df_tble_bho['cotrecho'] == codafl
                amont = df_tble_bho.loc[ia,'nuareamont'].to_numpy()
                if amont.size == 0:
                    print('erro ao buscar area drenagem')
                interno_acum[c] = interno_acum[c] - amont   #km2

        #... now we have the "local total drainage area"

        # (3) scale by the local area
        acum_scale = sum(interno_acum.values())
        for c in internos:
            interno_acum[c] = interno_acum[c]/acum_scale  #<--

        #print("  local drain area {} km2".format(acum_norm[0]))
        #for c in internos:
        #    print("   cotrecho {}: {} %".format(c,interno_acum[c]))


        # Update dictionary with parameters
        for c in internos:

            # get total drainage area
            ia = df_tble_bho['cotrecho']==c
            atot = df_tble_bho.loc[ia,'nuareamont'].to_numpy()

            # cotrecho ->int
            codint = int(c)

            # parameters
            dict_bho_parameters_t2[codint] = {
                'cotrecho': [codint],
                'miniref': [mini],                       # mini of reference
                'nuareamont': atot.tolist(),             # drainage area
                'fracarea': interno_acum[c].tolist(),    # % of total local area (bho)
                'minimon': d_interno_minimon[c],         # list of upstream neighbour catchments (mini) relative to bho
                'minimonall': list_minimonall,              # list of all upstream neigh catchments of miniref
                }

    return dict_bho_parameters_t2




def validate_t123(df_tble_bho,
                  dict_bho_domain,
                  area_threshold_t12,
                  dict_bho_mini_t1,
                  dict_bho_mini_t2,
                  dict_bho_mini_t3,
                  ):
    """
    Validates groups of features of type 1, 2 and 3 in the domain
        and make candidates for type 4.

    Args:
        df_tble_bho(pd.DataFrame) :: table of BHO drainage

        dict_bho_domain(dict) :: mapping of the domain between BHO and MGB
                                cotrecho as key, mini as value
                                e.g. {cotrecho:mini,...}
                                also called "dict_bho_mini"

        area_threshold_t12 (float) :: threshold for 'main drainage network'
                                    i.e. typically minimun value of MGB

        dict_bho_mini_t1(dict) :: mapping between BHO and MGB for type 1
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}

        dict_bho_mini_t2(dict) :: mapping between BHO and MGB for type 2
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}

        dict_bho_mini_t3(dict) :: mapping between BHO and MGB for type 3
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}


    Returns:
        groups_t123 (tuple) :: contains three items, each one contains the set
                               of cotrechos for the respective group 1,2,3
                               i.e. (group_t1_post, group_t2_post, group_t3_post)

        dicts_t123 (tuple) :: contains three items, each one contains a dict
                              of bho-mgb association {cotrecho:mini} for the
                              the respective groups 1,2,3
                              i.e. dicts_t123 (tuple)

        group_t4_candidates (set) :: list of cotrechos in the domain to be
                                     candidates of type 4

    Usage:
        groups_t123, dicts_t124, group4_candidates = .validate_t123(...)

    """

    # --
    # sets for drainages in bho and mgb domain
    ##group_bho = set(list(df_tble_bho['cotrecho'].values))  # cotrechos in bho
    group_domain = set(dict_bho_domain.keys())              # bho in mgb domain


    # --
    # a priori sets - "theorical target" for drainage (cotrecho)
    # - type 1 OR 2 (based on area threshold -> influences qty of type 3 or 4)
    ##group_bho_t12 = funcs_op.define_bho_target_t12(df_tble_bho, area_threshold_t12)
    group_bho_t12 = define_bho_target_t12(df_tble_bho, area_threshold_t12)

    # - type 1 OR 2 subset in mgb domain
    group_target_t12 = set([v for v in group_bho_t12 if v in group_domain])

    # - type 3 subset in mgb domain
    group_target_t3 = group_domain.difference(group_target_t12)


    # --
    # available sets for type 1 and 2
    group_t1 = set(dict_bho_mini_t1.keys())   # same as in df_tble_t1
    group_t2 = set(dict_bho_mini_t2.keys())   # same as in checked routes
                                              # careful: still include type 1 at
                                              #   found at the end of each route

    # --
    # post-processing sets
    # type 1 - keeps only those inside of MGB domain
    group_t1_post = set([v for v in group_t1 if v in group_domain])

    # type 2 - remove features at the end of routes (type 1 outlets), thus
    #   keeping only inner features
    group_t2_post = set([v for v in group_t2 if v in group_domain]).difference(group_t1_post)

    # actual types 1 OR 2 in the domain
    g12 = group_t1_post.union(group_t2_post)

    # --
    # type 3 - remove "actual" type 1 and 2 from the initial target
    group_t3_post = group_target_t3.difference(g12)

    # type 4 - lost cases from type 1 and 2.
    group_t4_candidates = group_target_t12.difference(g12)

    # --
    # verification - total count = domain count
    counts = list(map(len,[group_t1_post,group_t2_post,group_t3_post,group_t4_candidates]))
    print(" - group count: {}".format(counts))
    print(" - total count: {} of {} in domain".format(sum(counts),len(group_domain)))

    #TODO: IF THIS VERIFICATION GETS BAD!
    # -> CONSIDER PASSING THE 'A PRIORI' DOMAIN TO BEFORE TYPE 1 ASSOCIATION
    #    THEN PRE-FILTER df_tble_t1 (AND dict_bho_mini_t1) ALSO BASED ON THE DOMAIN

    #TODO:
    # - IDENTIFY WHICH FEATURES IN TYPE 4 ARE UPSTREAM OF MGB HEADWATERS
    #   BECAUSE THESE ARE NOT 'BAD CASES' AND THIS IS A NICE INFORMATION
    #   note: maybe do this afterwards


    # --

    # post-processed dictionaries for types 1, 2 and 3
    dict_bho_mini_t1_post = {k:v for k,v in dict_bho_mini_t1.items() if k in group_t1_post}
    dict_bho_mini_t2_post = {k:v for k,v in dict_bho_mini_t2.items() if k in group_t2_post}
    dict_bho_mini_t3_post = {k:v for k,v in dict_bho_mini_t3.items() if k in group_t3_post}


    # pack results
    groups_t123 = (group_t1_post, group_t2_post, group_t3_post)
    dicts_t123 = (dict_bho_mini_t1_post, dict_bho_mini_t2_post, dict_bho_mini_t3_post)

    #TODO: return as dicts?


    return groups_t123, dicts_t123, group_t4_candidates




def define_parameters_t4(group_t4_candidates,
                         dict_parameters_t3,
                         df_tble_bho,
                         dict_bho_mini_t1_post,
                         df_tble_mini):

    """
    Defines parameters for type 4 features

    Args:
        dict_bho_mini_t2 (dict) :: mapping between BHO and MGB for type 3
                                  cotrecho as key, mini as value
                                  e.g. {cotrecho:mini,...}

    TODO: DESCRIBE!!! -> "TWO SOLUTIONS"

    """


    # Parameters for type 4!
    dict_parameters_t4 = defaultdict(dict)
    lost_t4 = []

    conta_t4 = []

    for cotrecho in group_t4_candidates:

        # cotrecho as integer
        codint = int(cotrecho)

        # --------------------------------------------------------------------
        # method 4a: search for parameters in background "type 3" domain
        # --------------------------------------------------------------------
        t3_parameters = dict_parameters_t3.get(codint)

        ##if t3_parameters:
        # recover some parameters
        select_params = ['mini','aream_km2']
        params_sel = {k:v for k,v in t3_parameters.items() if k in select_params}

        # new parameters
        ibho = df_tble_bho['cotrecho'] == codint
        nuareamont = df_tble_bho.loc[ibho,'nuareamont'].values[0]
        params_new = {
                  'cotrecho': [codint],
                  'nuareamont': [round(nuareamont,6)],
                  }

        # store in dict_parameters_t4
        params_a = {}
        params_a.update(params_sel)
        params_a.update(params_new)

        dict_parameters_t4[codint] = params_a

        del params_a
        #-- end of method 4a


        # --------------------------------------------------------------------
        # method b: search a valid type 1 downstream
        # --------------------------------------------------------------------
        params_b = {}
        desce = True
        codigo = cotrecho
        while desce:
            # current index
            ibho = df_tble_bho['cotrecho'].isin([codigo])
            # next downstream
            codjus = df_tble_bho.loc[ibho,'nutrjus']
            # initiate status
            try:
                status = len(codjus)
            except:
                status = 0

            if status == 1:
                # downstream walk
                codigo = codjus.values[0]

                # try to get for type 1 solution
                mini_t1 = dict_bho_mini_t1_post.get(codigo,None)
                if mini_t1:

                    # stop walk
                    desce = False

                    # update parameters
                    mini = mini_t1
                    imini = df_tble_mini['mini'] == mini
                    area_km2 = df_tble_mini.loc[imini,'area_km2'].values[0]
                    aream_km2 = df_tble_mini.loc[imini,'aream_km2'].values[0]
                    nuareamont = df_tble_bho.loc[ibho,'nuareamont'].values[0]
                    params_b = {
                        'cotrecho': [codint],
                        't4_cotrecho': [int(codigo)],
                        't4_mini': [mini_t1],
                        't4_aream_km2': [aream_km2],
                        't4_nuareamont': [round(nuareamont,6)],

                        }
                    dict_parameters_t4[codint].update(params_b)

                    # show in screen
                    #print(" cotrecho {} found a type 1 neighbour".format(cotrecho))
            else:
                #end-of-path

                # show in screen
                #print("cotrecho {} didnt find type 1 neighbour".format(cotrecho))
                desce = False
                lost_t4.append(cotrecho)

        del params_b
        #-- end of method 4b

    nlost = len(lost_t4)
    ndone = len(group_t4_candidates) - nlost
    print(" - total of {} ({}) full (partial) type 4 features".format(ndone,nlost))


    # SOME CONSIDERATIONS FOR "LOST T4" DRAINAGE
    #
    # - mostly at edge domain in coastal drainage
    # - large river features without type 1
    #   (e.g. probably midpoint of river was bad choice for type 1)
    #    -> likely easy to fix
    #
    # possible treatments:
    # - cases of features that were expected in target_t12
    #    -> use mgb catchment polygon pre-filtered with area_threshold_t12
    #    -> use line endpoint (dwn node) for "type 3 like" association
    # - other cases
    #    -> likely to be coastal
    # - could be called type 5?!
    #


    """
    # testing: searching for type 1 solution ->could be
    #-> first read bho gdf (or nodes!)
    gdf_lost_t4 = gdf_tble_bho[gdf_tble_bho['cotrecho'].isin(lost_t4)]
    dict_lost_t4 = funcs_op.associate_bho_mini_domain(gdf_lost_t4, gdf_mgb_catchments, node_pos=1.)
    # get parameters
    params_lost_t4 = {}
    errors_lost_t4 = {}
    for k,v in dict_lost_t4.items():
        cotrecho,mini = k,v
        imini = df_tble_mini['mini'].isin([mini])
        ibho = df_tble_bho['cotrecho'].isin([cotrecho])

        area_bho = df_tble_mini.loc[imini,'aream_km2'].values[0]
        area_mini = df_tble_bho.loc[ibho,'nuareamont'].values[0]
        errors_lost_t4[k] = [100.*abs(area_mini/area_bho-1.),min(area_mini/area_bho,area_bho/area_mini)]
        params_lost_t4[k] = {
            't4_lost_cotrecho': [int(cotrecho)],
            't4_mini':[mini],
            't4_aream_km2':[area_mini],
            't4_nuareamont':[area_bho],

            }
    """

    # TODO: meanwhile we keep all candidates for t4 as t4_post
    group_t4_post = group_t4_candidates.copy()

    return group_t4_post, dict_parameters_t4, lost_t4




def make_dict_solver(group_t1_post, group_t2_post, group_t3_post, group_t4_post):
    """

    DESCRIBE
    """

    # solver tags {cotrecho: solver_type,...}
    sol_t1  = {k:1 for k in group_t1_post}
    sol_t2  = {k:2 for k in group_t2_post}
    sol_t3  = {k:3 for k in group_t3_post}
    sol_t4  = {k:4 for k in group_t4_post}

    dict_bho_solver = {}
    dict_bho_solver.update(sol_t1)
    dict_bho_solver.update(sol_t2)
    dict_bho_solver.update(sol_t3)
    dict_bho_solver.update(sol_t4)

    return dict_bho_solver