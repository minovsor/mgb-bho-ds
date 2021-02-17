# -*- coding: utf-8 -*-
"""

Auxiliary functions to choose candidates for type 1 association

@author: Mino Sorribas (python)
         Joao Fialho/Vinicius Siqueira (original version matlab)


TODO: translate to us-en
"""

import sys
import numpy as np
import pandas as pd
import geopandas as gpd


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




def read_matlab_input(file_mini, file_bho_inter):
    """
    Read mini.gtp (.xlsx format) and BHO points (inside MGB polygon)

    Args:
        file_mini (str) :: pathfile to mini.xlsx
        file_bho_inter (str) :: pathfile to .shp of intersection from qgis

    Returns:
        df_tble_mini (pd.DataFrame) :: table of mini.gtp
        df_tble_bho (pd.DataFrame) :: table of BHO points x MGB
    """

    # MINI.gtp
    hmap = {'Mini':'mini',
            'AreaM_(km2)':'aream_km2',
            'MiniJus': 'minijus',
            'Ordem': 'ordem',
            'Xcen':'xc',
            'Ycen':'yc',
            }
    df_tble_mini = pd.read_excel(file_mini)
    df_tble_mini = df_tble_mini.rename(columns = hmap)
    df_tble_mini = df_tble_mini.set_index('mini',drop=False) #index from 1 to nc
    df_tble_mini = df_tble_mini.sort_index()


    # BHO Intersect
    # identifica extensao do arquivo
    ext = file_bho_inter.split('.')[-1]
    if ext == 'shp' or ext =='gpkg':
        hmap = {'Mini':'mini',
                'AreaM__km2':'aream_km2',
                'Area__km2_':'area_km2',
                'Sub':'sub',
                'X':'xp',  #bho coordinate
                'Y':'yp',  #bho coordinate
                }
        df_tble_bho = gpd.read_file(file_bho_inter)
        df_tble_bho = df_tble_bho.drop('geometry',axis=1) #drop geometry
        df_tble_bho = df_tble_bho.rename(columns = hmap)

    elif ext == 'xlsx' or ext == 'xls':
        hmap = {'Mini':'mini',
                'mini_areamont':'aream_km2',
                'X':'xp',  #bho coordinate
                'Y':'yp',  #bho coordinate
                }
        df_tble_bho = gpd.read_excel(file_bho_inter)
        df_tble_bho = df_tble_bho.rename(columns = hmap)

    #ajusta dtypes
    hmap = {k:v for k,v in bho_dtypes.items() if k in df_tble_bho.columns}
    df_tble_bho = df_tble_bho.astype(hmap)

    return df_tble_mini, df_tble_bho



def ottobacia_a_jusante(codigo_jusante, codigo_montante, accept_same = True):
    """
    Test if codigo_jusante is downstream of codigo_montante
        based on Otto Pfafstetter codification.

    Args:
        codigo_jusante (str/list/float/np.arr) :: downstream ottocode

        codigo_montante (str/list/float/np.arr) :: upstream ottocode

        accept_same (bool) :: accept

    Returns:
        jusante(bool) :: True if codigo_jusante is downstream of codigo_montante
                         False if codigo_jusante not downstream of ...

    Notes:
        - if args are list/np.array it will use the first item
        - if codigo_jusante or codigo_montante = np.nan, returns False

    """

    try:
        #list->str
        if isinstance(codigo_jusante,list):
            codigo_jusante = str(int(codigo_jusante[0]))

        if isinstance(codigo_montante,list):
            codigo_montante = str(int(codigo_montante[0]))

        #array->str
        if isinstance(codigo_jusante,np.ndarray):
            codigo_jusante = str(int(codigo_jusante[0]))

        if isinstance(codigo_montante,np.ndarray):
            codigo_montante = str(int(codigo_montante[0]))

        # float/int ->str
        if not isinstance(codigo_jusante,str):
            codigo_jusante = str(int(codigo_jusante))

        if not isinstance(codigo_montante,str):
            codigo_montante =str(int(codigo_montante))
    except:
        if np.isnan(codigo_montante) or np.isnan(codigo_jusante):
            return False
        else:
            print(" format error in {}-{}".format(codigo_jusante,codigo_montante))
            sys.exit()
            return None

    # trick para acelerar um pouco: se 1o algarismo é != já ignora
    if codigo_jusante[0]!=codigo_montante[0]:
        return False

    #optional arguments
    #iostat = False

    #print('\n')
    #print('teste:codigo {} esta a jusante de {}?'.format(codigo_montante,codigo_jusante))

    if codigo_jusante == codigo_montante:
        #print(".ottobacia_a_jusante: exut=True, codigo montante=jusante, inclui {}".format(codigo_jusante))
        return accept_same

    #inicia supondo que nao esta a jusante
    jusante = False

    # (i) parte a esquerda em comum,
    nalgarismo = len(codigo_jusante)
    for n in range(nalgarismo+1):
        if (codigo_jusante[:n]==codigo_montante[:n]):
            sleft = codigo_jusante[:n]
            nleft = len(sleft)

    #print('algarismos comuns esquerda:{}'.format(sleft))

    #...e pelo menos um dígito par (pertence a mesma bacia que desagua no oceano)
    is_even = lambda s: int(s)%2==0
    is_odd  = lambda s: int(s)%2!=0
    if (sleft and any( map(is_even,sleft) )):

        #print('criterio 1: ok')

        #(ii) o primeiro dígito da parte direita não comum
        # deve ser menor a jusante do que na de montante
        right_jus=codigo_jusante[nleft:]
        right_mon=codigo_montante[nleft:]


        #print('algarismos a direita (jusante):{}'.format(right_jus))
        #print('algarismos a direita (montante):{}'.format(right_mon))

        #ajuste de codigos para o mesmo tamanho
        nzeros = len(right_jus)-len(right_mon)
        if nzeros>0:
            right_mon = right_mon + '0'*nzeros
        elif nzeros<0:
            right_jus = right_jus + '0'*nzeros

        if int(right_jus[0])<int(right_mon[0]):

            #print('criterio 2: ok')

            #(iii) todos os dígitos da parte direita não comum
            # no ponto de jusante devem ser ímpares
            # (com exceção de zeros de complementação)
            ## TODO: CUIDADO - VERIFICAR SE NÃO REMOVE ZEROS DESEJADOS?!
            ##right_val = [s for s in right_jus if s!='0']

            right_val = right_jus.rstrip("0")
            if len(right_val)==0:
                print("sem valores a direita?!")
                print(sleft)
                print(right_mon)
                print(right_jus)
                raise NameError('Erro!')
            #--

            #if all( map(is_odd,right_val)):

            if all( map(is_odd,right_val)) and len(right_val)>0: #ms
                #print('criterio 3: ok')
                jusante = True
                #if iostat:
                #    print('ok')

    return jusante



def busca_conectividade(cobacias_mon,
                        cotrecho,
                        df_bho_filt,
                        max_iter = 5):
    """
    Search for a cotrecho that is connected to all upstream catchments
    (cobacias_mon) using a downstream walk, starting from cotrecho in the
    BHO drainage

    Args:
        cobacias_mon (list)  :: upstream catchments Otto codes ('cobacia')
        cotrecho (int/float) :: starting cotrecho ('cotrecho')
        df_bho_filt(pd.DataFrame) :: BHO drainage table (filtered)

    Returns:
        cotrecho_jus (int) :: downstream cotrecho connected to all cobacias_mon
                              OR np.nan if not found
        pos_table (int) :: index of df_bho_filt of cotrecho_jus

    Notes:
        - if not found, returns np.nan


    """

    is_empty = lambda x: True if len(x)==0 else False

    # ms: dataframe to array
    #tables = df_bho_filt[['cotrecho','nutrjus','cobacia']].to_numpy()
    #cotrecho_table = tables[:,0]
    #nutrjus_table = tables[:,1]
    #ottobac_table = tables[:,2]

    # begin at cotrecho
    next_down = cotrecho


    # downwalk the drainage trying to find the connectivity
    for _ in range(max_iter):

        # search next cotrecho
        ind = df_bho_filt['cotrecho']==next_down
        df = df_bho_filt.loc[ind]
        d = df.index.to_list()

        # out of drainage bounds
        if is_empty(df):
            break

        # get ottopfafstter code
        next_otto = df_bho_filt.loc[d,'cobacia'].to_list()[0]

        # test conectivity (with each cobacias_mon) using ottocodifiation
        otto_test = []
        for cobacia_m in cobacias_mon:
            a_jusante = ottobacia_a_jusante(next_otto, cobacia_m, accept_same=True)
            otto_test.append(a_jusante)

        # note: matlab accepts same codes (minifound=-1) and ignores nan on test
        #if all(otto_test):  #requires all connected
        if any(otto_test):   #at least one connection
            # success: returns cotrecho and index
            cotrecho_jus = next_down
            pos_table = d[0]
            result = (cotrecho_jus,pos_table)
            #print(result)
            return result


        #Segue para o trecho de jusante
        next_down = df_bho_filt.loc[d,'nutrjus'].to_list()[0]


    # found nothing
    cotrecho_jus = np.nan
    pos_table = np.nan
    result = (cotrecho_jus,pos_table)
    return result

