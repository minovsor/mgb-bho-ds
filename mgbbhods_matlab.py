# -*- coding: utf-8 -*-
"""
Main script to calculate table for type 1 candidates
  (based on matlab)

Read 'table_t0.xlsx' and Save 'table_t1_py.xlsx'

@authors:
    Mino Sorribas (adapted to python)
    Vinicius Siqueira/Joao Fialho Breada (original matlab)


@todo:
    - translate comments and code
    - do a HUGE function for th whole process
    - MAYBE break the whole process in separate functions.

    - this script could be a function
    def funcs_matlab.make_table_t1(df_tble_mini,
                      df_tble_bho,
                      area_threshold,
                      area_limite_minijus=10000.,
                      dmax=0.5):
        return df_tble_t1

"""

# standard python
import sys

# plotting, numpy, dataframes and spatial
import numpy as np
import pandas as pd
import geopandas as gpd
import numexpr

# downscaling functions
import funcs_io
import funcs_matlab



print("-------------------------------------------------------")
print(" 'Matlab' Pre-processing for the MGB-BHO Downscaling   ")
print("-------------------------------------------------------")


#-----------------------------------------------------------------------------
# Importing functions
#-----------------------------------------------------------------------------

f_test_area = funcs_io.f_test_area
ottobacia_a_jusante = funcs_matlab.ottobacia_a_jusante
busca_conectividade = funcs_matlab.busca_conectividade
bho_dtypes = funcs_matlab.bho_dtypes



#-----------------------------------------------------------------------------
# Input files
#-----------------------------------------------------------------------------
PATH = '../input/'

FILE_MINI = PATH + 'mini.xlsx'

#original matlab
FILE_BHO_INTER = PATH + 'BHO5k_points_mini_intersect_2.shp'

#python made
#FILE_BHO_INTER = PATH + 'table_t0.xlsx'



#-----------------------------------------------------------------------------
# Read table and pre-processed shapefile (as required for MATLAB version)
#-----------------------------------------------------------------------------
df_tble_mini, df_tble_bho = funcs_matlab.read_matlab_input(FILE_MINI, FILE_BHO_INTER)


#note: tabela bho deve incluir mini, xc e yc
# get results from funcs_op.associate_bho_mini_domain()
#df_tble_mini, df_tble_bho = .make_intersect_table(df_tble_bho,mid_pts)

#-----------------------------------------------------------------------------
# Parametros
#-----------------------------------------------------------------------------

# Area thredhols para definir o rio principal (versus nao-principal)
area_threshold = 800.

# Área limite para checar trechos na mini de jusante
area_limite_minijus = 10000.
##area_limite_minijus = df_tble_mini['aream_km2'].min() ??

# Distancia maxima de busca
dmax = 0.5

#-----------------------------------------------------------------------------
# Filtragem da tabela
#-----------------------------------------------------------------------------

# Filtro para obter o rio principal
df_bho_filt = df_tble_bho[df_tble_bho['nuareamont']>area_threshold]
df_bho_filt = df_bho_filt.reset_index()
#df_bho_filt = df_bho_filt.set_index(df_bho_filt.index+1)



#-----------------------------------------------------------------------------
# Inicializa vetores
#-----------------------------------------------------------------------------

# Dimensiona vetores (+1, pois vamos ignorar 0, no caso das minibacias)
nmini = len(df_tble_mini) + 1
nbho_filt = len(df_bho_filt) # + 1


# Candidatos por trecho BHO (0 a nbho_filt-1)
cand = np.zeros((nbho_filt,1))

# Candidatos por mini MGB (0 a nmini, sendo 0 dummy)
# colunas: 0 - cotrecho, 1 - diferenca de area, 2 - posicao no vetor
cand2 = np.zeros((nmini,3))
cand2_otto = np.nan*np.ones((nmini,1))

# Indica se ponto esta dentro ou fora da minibacia
flag = np.zeros((nmini,1))


#-----------------------------------------------------------------------------
# Funcoes adicionais
#-----------------------------------------------------------------------------
is_empty = lambda x: True if len(x)==0 else False


#-----------------------------------------------------------------------------
# Primeiro round
#-----------------------------------------------------------------------------
for irow in df_tble_mini.itertuples():

    # #ms: informacoes de minibacia
    i = irow.mini
    aream_km2 = irow.aream_km2
    minijus = irow.minijus

    print("1st round: mini {}".format(i))

    # Encontra se tem trechos da BHO na minibacia
    ind = df_bho_filt['mini'] == i   #bool
    df = df_bho_filt.loc[ind]        #dados (df)
    d = df.index.to_list()           #indices

    '''
    if i<19538:
        continue
    if i==19538:
        sys.exit()
        continue
    '''


    if (is_empty(d)) and (aream_km2 < area_limite_minijus):
        # Se não tem, identifica os pontos na mini de jusante
        ind = df_bho_filt['mini'] == minijus
        df = df_bho_filt.loc[ind]
        d = df.index.to_list()

        if is_empty(d):
            #Se não identifica nada, segue para a próxima mini (do loop)
            continue

        # Testa os pontos na mini de jusante
        # diferenca entre areas de drenagem da BHO com o MGB
        diff = abs(df_bho_filt.loc[d,'nuareamont'] - aream_km2) #pd.Series

        # Seleciona o ponto com a menor diferença de área de drenagem
        x = diff.sort_values().head(1)
        c = x.index[0]

        # ms: candidatos em mini
        cand2[i,0] = df_bho_filt.loc[c,'cotrecho']   #1 - cotrecho
        cand2[i,1] = x.to_list()[0]                  #2 - diferenca area
        cand2[i,2] = c                               #3 - posicao no vetor (bho)
        # ms: candidatos em bho
        cand[c] = i                                  #minibacia
        #Armazena o codigo Otto
        cand2_otto[i] = df_bho_filt.loc[c,'cobacia']


        #Segue para a próxima mini
        continue

    else:

        #Se tiver identificado trechos BHO dentro da mini
        #E for area menor do que limiar maximo para identificar trechos a jusante
        if (not is_empty(d)) and (aream_km2 < area_limite_minijus):

            # seleciona também os trechos da BHO da mini jusante
            ind = df_bho_filt['mini'] == minijus
            df = df_bho_filt.loc[ind]
            d2 = df.index.to_list()

            #Se encontrar pontos na mini de jusante
            if len(d2)>0:

                #Primeiramente vamos excluir os pontos da mini de jusante que não
                #tiverem conectividade com a BHO de montante
                ncand = len(d2)+len(d)
                exclude_BHO = np.zeros((ncand)).astype(bool)  #nao exclui nada por padrao

                #Seleciona o codigo otto dos candidatos na mini de jusante
                cobacias_jus = df_bho_filt.loc[d2,'cobacia'].to_list()

                #Para cada BHO na mini de jusante (d2)
                #testa se está a jusante de algum dos trechos na mini mont
                cobacias_mon = df_bho_filt.loc[d,'cobacia'].to_list()
                for j in range(len(d2)):
                    otto_test = []
                    cobacia_j = cobacias_jus[j]
                    for cobacia_m in cobacias_mon:
                        a_jusante = ottobacia_a_jusante(cobacia_j,cobacia_m, accept_same=False)
                        otto_test.append(a_jusante)

                    #Se há alguma conectividade, não exclui a BHO de jusante
                    if any(otto_test):
                        exclude_BHO[j] = False
                    else:
                        #caso contrário, exclui a BHO de jusante
                        exclude_BHO[j] = True

                # junta os trechos BHO na mini de jusante com as de montante
                d3 = d2 + d   #ms: a ordem é importante devido a exclude_BHO que é np.array

                #Acha a diferença absoluta dentre todos os candidatos
                diff = abs(df_bho_filt.loc[d3,'nuareamont'] - aream_km2) #pd.Series

                #Coloca uma diferença de área infinita para os pontos sem conectividade
                exclude_BHO = exclude_BHO.astype(bool)
                diff = diff.where(~exclude_BHO,999999999.) #np usa mask invertida!
            else:
                #Se não encontrar, fica só com os pontos de montante;
                d3 = d.copy()
                #Acha a diferença absoluta dentre todos os candidatos
                diff = abs(df_bho_filt.loc[d3,'nuareamont'] - aream_km2)


            # pega o que der menor diferença
            x = diff.sort_values().head(1)
            c = x.index[0]

            # ms: candidato em mini
            cand2[i,0] = df_bho_filt.loc[c,'cotrecho']    #1 - cotrecho
            cand2[i,1] = x.to_list()[0]                  #2 - diferenca area
            cand2[i,2] = c                               #3 - posicao no vetor (bho)
            # ms: candidato em bho
            cand[c] = i                                  #minibacia
            # armazena o codigo Otto
            cand2_otto[i] = df_bho_filt.loc[c,'cobacia']

            #TODO: verificar matlab> python :::   c == d3[c]?!
            #print(d3)
            #print(x)
            #print(c)

            # flag
            if df_bho_filt.loc[c,'mini']==i:
                flag[i] = 1


        elif (not is_empty(d)) and (aream_km2 > area_limite_minijus):
            #Nesse caso , área é maior que o limiar maximo para identificar trechos a jusante
            #Acha a menor diferença absoluta dentre todos os candidatos
            diff = abs(df_bho_filt.loc[d,'nuareamont'] - aream_km2)

            # pega o que der menor diferença
            x = diff.sort_values().head(1)
            c = x.index[0]                     #indice na tabela bho

            # ms: candidato em mini
            cand2[i,0] = df_bho_filt.loc[c,'cotrecho']   #1 - cotrecho
            cand2[i,1] = x.to_list()[0]                  #2 - diferenca area
            cand2[i,2] = c                               #3 - posicao no vetor (bho)
            # ms: candidato em bho
            cand[c] = i                                  #minibacia
            # armazena o codigo Otto
            cand2_otto[i] = df_bho_filt.loc[c,'cobacia']

            flag[i] = 1                                  #flag[minibacia]=1

        elif is_empty(d) and (aream_km2 > area_limite_minijus):
            #Para áreas superiores ao limite e que não achou pontos
            #Não faz nada, segue para próxima mini
            continue

print("End of 1st round")


dict_1a = {
    'cand':cand.copy(),
    'cand2':cand2.copy(),
    'cand2_otto':cand2_otto.copy(),
    }

#print(cand2[19538])
#sys.exit()


#-----------------------------------------------------------------------------
# Segundo Round
#-----------------------------------------------------------------------------
## 2a rodada #VAS
# Analisa minibacias que recebem mais de um afluente
# Checa se os trechos BHO dos afluentes estão convergindo para o BHO da minibacia receptora
for irow in df_tble_mini.itertuples():

    # #ms: informacoes de minibacia
    i = irow.mini

    #if i>12088:
    #    sys.exit()

    # #ms: afluente
    ind = df_tble_mini['minijus'] == i
    df = df_tble_mini.loc[ind]
    d = df.index.to_list()

    print("2nd round: mini {}".format(i))

    if i == 12088:
        print("teste 12088")



    #Somente se a bacia tem mais de um afluente
    if len(d)>1:

        #Seleciona os códigos otto das BHO de minis afluentes
        cand_minimont_otto = cand2_otto[d]

        #Seleciona o código otto e o cotrecho da BHO da mini que recebe
        cand_minijus_otto = cand2_otto[i]
        cand_minijus = cand2[i,0]

        if i == 12088:
            print("cand montante",cand_minimont_otto)
            print("cand jusante",cand_minijus)

        #Somente resolve se há um candidato BHO para mini de jusante
        if not np.isnan(cand_minijus_otto):

            #Testa a conectividade dos trechos candidatos de montante usando a codificação de Otto
            #ms: nao necessaramente estao na mesma minibacia!
            otto_test = []
            otto_igual = []
            cobacia_j = cand_minijus_otto.copy()

            for cobacia_m in cand_minimont_otto:
                a_jusante = ottobacia_a_jusante(cobacia_j,cobacia_m, accept_same=False)
                otto_test.append(a_jusante)
                #armazena codigos iguais
                if cobacia_j==cobacia_m:
                    otto_igual.append(True)
                else:
                    otto_igual.append(False)

            #Identifica se há trechos sem conectividade com o de jusante
            sem_conectiv =[]
            for j,isjus in enumerate(otto_test):
                if isjus == False and otto_igual[j]==False: #conectados, mas diferente
                    sem_conectiv.append(j)
            #sem_conectiv = [j for j,v in enumerate(otto_test) if v==False]
            n_sem_conectiv= len(sem_conectiv)

            if i == 12088:
                print("otto test",otto_test)
                print("otto igual",otto_igual)
                print("sem conectiv",sem_conectiv)

            #Se o trecho de jusante for igual a algum de montante, ignora; passa para o próximo ponto
            if any(otto_igual):
                continue

            else:
                #(máx 5 descidas de rio)
                max_iter = 5

                #Se há um BHO afluente sem conectividade com o de jusante
                if n_sem_conectiv > 0:

                    #Identifica a nova BHO de jusante
                    cobacias_m = cand_minimont_otto[sem_conectiv].flatten().tolist()
                    new_cand_minijus, pos_table = busca_conectividade(
                        cobacias_m,
                        cand_minijus,
                        df_bho_filt,
                        max_iter)

                    if i == 12088:
                        print("new_cand,pos_table",new_cand_minijus,pos_table)


                    #Atualiza informações caso encontrou uma nova mini
                    if not np.isnan(new_cand_minijus):

                        #Atualiza informações
                        cand2[i,0] = new_cand_minijus

                        #Atualiza diferença absoluta de área
                        diff = abs(df_bho_filt.loc[c,'nuareamont'] - aream_km2)

                        cand2[i,1] = diff
                        cand2[i,2] = pos_table

                        #Atualiza informações na tabela de BHO
                        # desconecta a minibacia do trecho alocado antes
                        d = cand==i
                        cand[d] = 0
                        #Conecta a minibacia ao novo trecho
                        cand[pos_table] = i



dict_2a = {
    'cand':cand.copy(),
    'cand2':cand2.copy(),
    'cand2_otto':cand2_otto.copy(),
    }

#sys.exit()

#-----------------------------------------------------------------------------
# Terceiro Round
#-----------------------------------------------------------------------------

areas = df_tble_mini['aream_km2'].to_numpy()
erro_p = np.nan*np.ones_like(cand2[:,1])
erro_p[1:,] = 100.*np.divide(cand2[1:,1],areas)   #minibacias a partir de 1

# setando para 0 para poder refazer (limpando mbs com mto erro)

# digo que não eh candidato aqueles com erros altos ou em mb repetidas.
# do jeito q o cod estah escrito, a bho pode ser candidata de duas
# minibacias

# o loop é feito invertido, para zerar primeiro as de jusante
for irow in df_tble_mini.sort_index(ascending=False).itertuples():

    # #ms: informacoes de minibacia
    i = irow.mini
    aream_km2 = irow.aream_km2

    print("3rd round: mini {}".format(i))

    # se jah nao tiver candidato, continua
    if cand2[i,0]==0:
        continue

    # usar o teste de area aceitavel
    a_diff_perc = erro_p[i]
    accept = f_test_area(a_diff_perc, aream_km2);
    if not accept:
        cand2[i,:] = 0
        cand[cand==i] = 0
        flag[i] = 0
        continue


    # ver se tem duas minibacias apontando pra mesma bho
    ind = cand2[:,0] == cand2[i,0]
    g = np.flatnonzero(ind)

    # se não tem duas minibacias pra mesma bho, continue
    if len(g)<=1:
        # caso tivesse marcado com uma outra minibacia mais a jusante
        # que foi zerada agora, relaciona a bho a minibacia de montante
        if len(g)==1:
            pos = int(cand2[i,2])   #posicao no vetor bho
            cand[pos] = i           #minibacia
        continue

    # se tiver bho para mais de uma minibacia, prioriza a mais de jusante
    elif g[-1]>i:
        cand2[i,:] = 0
        flag[i] = 0

        ## cand(cand==i)=0; % nao precisa pq provavelmente cand jah tah
        ## associado a mais de jusante, ou seja
        ## cand==i é vazio, pois cand=g(end)

    else:
        ## essa eh a minibacia mais de jusante, entao
        ## caso tivesse marcado com uma outra minibacia mais a jusante
        ## relaciona a bho a essa minibacia
        pos = int(cand2[i,2])
        cand[pos] = i


dict_3a = {
    'cand':cand.copy(),
    'cand2':cand2.copy(),
    'cand2_otto':cand2_otto.copy(),
    }



#-----------------------------------------------------------------------------
# (?!) Quarto Round
#-----------------------------------------------------------------------------


# criando topologia com o codigo da ottobacia
bho_nunivotto_area = 10.**df_bho_filt['nunivotto'].to_numpy()
bho_cobacia_filt = df_bho_filt['cobacia'].astype(float).to_numpy()
bho_topo_filt = bho_cobacia_filt/bho_nunivotto_area

# retirando das opcoes os trechos que jah sao candidatos
bho_mini_filt = df_bho_filt['mini'].to_numpy()
bho_mini_filt2 = bho_mini_filt.copy()  # vetor com tamanho == bho_filt
bho_mini_filt2[cand.flatten()>0] = 0

bho_lat_filt = df_bho_filt['yp'].to_numpy()
bho_lon_filt = df_bho_filt['xp'].to_numpy()


bho_cotrecho_filt = df_bho_filt['cotrecho'].to_numpy()

# segunda rodada de fato considerando as minibacias vizinhas
# na segunda rodada nós vamos:
# 1: se a ordem for 1 ou nao tiver minibacia de montante com trechos bho,
# considerar a de jusante e pegar ponto não repetido;
# 2: se tiver pontos a montante e jusante, verificar a
# proximidade espacial (0.5o) e a topologia

for irow in df_tble_mini.itertuples():

    #mini
    i = irow.mini
    minijus = irow.minijus
    ordem = irow.ordem
    aream_km2 = irow.aream_km2
    xc = irow.xc
    yc = irow.yc

    print("4th round: mini {}".format(i))

    # se jah tiver ponto relacionado, continua
    if cand2[i,0]>0:
        continue

    # condicao 1
    # #ms: minibacias afluentes
    ind = df_tble_mini['minijus'] == i
    df = df_tble_mini.loc[ind]
    g = df.index.to_list()

    # se a ordem for 1 OU
    # se as mini de montante nao tiver dados OU
    # se nao tiver minibacia de jusante
    if ordem==1 or sum(cand2[g,0])==0 or minijus==-1:
        # encontrar os pontos bho dentro da mb
        d = np.flatnonzero(bho_mini_filt2==i)
        # encontrar os pontos bho dentro da mb de jusante
        if minijus>-1:
            d2 = np.flatnonzero(bho_mini_filt2==minijus)
            d = np.concatenate((d,d2))
        # se nao tiver trecho bho em canto nenhum
        if is_empty(d):
            continue

        #Acha a menor diferença absoluta dentre todos os candidatos
        diff = abs(df_bho_filt.loc[d,'nuareamont'] - aream_km2) #pd.Series

        # Seleciona o ponto com a menor diferença de área de drenagem
        x = diff.sort_values().head(1)
        c = x.index[0]
        # candidatos em mini
        cand2[i,0] = df_bho_filt.loc[c,'cotrecho']   #1 - cotrecho
        cand2[i,1] = x.to_list()[0]                  #2 - diferenca area
        cand2[i,2] = c                               #3 - posicao no vetor (bho)
        # ms: candidatos em bho
        cand[c] = i                                  #minibacia
        if bho_mini_filt[c]==i:
            flag[i] = 1

    # condicao 2
    elif cand2[minijus,0]>0:

        # posicao do vetor das BHO das minis montante
        jmon = cand2[g,2].astype(int)

        # selecionando apenas os trechos com candidatos
        jmon = jmon[jmon>0]

        # menor topologia (mais jusante) entre minibacias de montante % MOD 28/07
        t1, it1 = bho_topo_filt[jmon].min(), bho_topo_filt[jmon].argmin()

        # topologia com ottocodificacao completa % ADD 28/07
        t3 = bho_cobacia_filt[jmon]
        # menor topologia dentre as minis de montante % ADD 28/07
        t3 = t3[it1]

        # posicao da mini de jusante no vetor BHO
        jjus = cand2[minijus,2].astype(int)
        # topologia da minibacia de jusante
        t2 = bho_topo_filt[jjus]

        # candidatos com base na topologia
        cond = (bho_topo_filt > t2) & (bho_topo_filt < t1)
        d = np.flatnonzero(cond)

        # se nao tiver trecho bho em canto nenhum
        if is_empty(d):
            continue
        else:
            lat = yc
            lon = xc
            k2 = []
            din = []
            for k,dk in enumerate(d):
                xd = bho_lat_filt[dk] - lon
                yd = bho_lon_filt[dk] - lat
                dist = np.sqrt(xd**2 + yd**2)
                codjus = bho_cobacia_filt[dk]
                codmon = t3
                jus_true = ottobacia_a_jusante(codjus,codmon,accept_same=False) # ADD 28/07

                if (dist>dmax or cand[dk]>0 or jus_true==False): # MOD 28/07
                    k2.append(k)
                else:
                    din.append(dk) #ms:pts dentro do raio

            #d[k2] = []  #remove pts fora
            d = din      #ms:inclui pts dentro
            if is_empty(d): #nao sobrou candidatos
                continue

        #Acha a menor diferença absoluta (nas areas) dentre todos os candidatos
        diff = abs(df_bho_filt.loc[d,'nuareamont'] - aream_km2)

        # Seleciona o ponto com a menor diferença de área de drenagem
        x = diff.sort_values().head(1)
        c = x.index[0]

        # ms: candidatos em mini
        cand2[i,0] = df_bho_filt.loc[c,'cotrecho']   #1 - cotrecho
        cand2[i,1] = x.to_list()[0]                  #2 - diferenca area
        cand2[i,2] = c                               #3 - posicao no vetor (bho)
        # ms: candidatos em bho
        cand[c] = i                                  #minibacia

        if df_bho_filt.loc[c,'mini']==i:
            flag[i] = 1



dict_4a = {
    'cand':cand.copy(),
    'cand2':cand2.copy(),
    'cand2_otto':cand2_otto.copy(),
    }



#-----------------------------------------------------------------------------
# (*) Prepara tabela final
#-----------------------------------------------------------------------------

# Cria tabela de correspondencia mini x BHO
candidates = np.ones((nmini,9))*np.nan

#ms: float->integer to use as index in np.array and flatten->(1,)
cand = cand.astype(int).flatten()

#Corrige a area do MGB associada aos pontos BHO, dado que alguns foram selecionados a jusante da minibacia
bho_aream_filt = df_bho_filt['nuareamont'].to_numpy()
bho_areamgb_corrected = np.zeros_like(bho_aream_filt)
for irow in df_bho_filt.itertuples():
    j = irow.Index
    mini = cand[j]
    if mini>0:
        bho_areamgb_corrected[j] = df_tble_mini.loc[mini,'aream_km2']


# Calcula diferença percentual de area
area_diff_perc = 100.*(bho_aream_filt/bho_areamgb_corrected-1.)

# Troca valores infinitos para NaN;
area_diff_perc[np.isinf(area_diff_perc)]=np.nan

# pontos tipo 2 com flag se eh candidato ou nao
candidates2 = np.stack((bho_lat_filt,bho_lon_filt),axis=1)


#monta a tabela
for irow in df_tble_mini.itertuples():
    i = irow.mini
    candidates[i,0] = i #mini

    print(" - table t1: mini {}".format(i))

    #Preenche informações para minibacias em que correspondencia foi encontrada
    cotrecho = cand2[i,0]
    if cotrecho>0:
        j = np.nonzero(bho_cotrecho_filt==cotrecho)
        candidates[i,1] = bho_cotrecho_filt[j]
        candidates[i,2] = bho_cobacia_filt[j]
        candidates[i,3] = bho_aream_filt[j]
        candidates[i,4] = bho_areamgb_corrected[j]
        candidates[i,5] = area_diff_perc[j]
        candidates[i,6] = bho_lat_filt[j]
        candidates[i,7] = bho_lon_filt[j]
        # flag
        candidates[i,8] = flag[i]


#-------------------------------------------------------------------------
# Monta dataframe
headers = [
    'mini',
    'bho_cotrecho',
    'codigo_otto',    #todo: utilizar bho_cobacia?!
    'bho_nuareamont',
    'mini_areamont',
    'diffp_areamont',
    'latitude',       #coordenada do midpoint da bho
    'longitude',
    'flag_mini_in',
    ]

df_tble_t1 = pd.DataFrame(candidates,columns = headers)

# remove mini=0 e reajusta indice
df_tble_t1 = df_tble_t1.drop(index=0).reset_index(drop=True)

#-------------------------------------------------------------------------
# Grava Resultados
df_tble_t1.to_excel('table_t1_py.xlsx')



'''
#analise de resultados parciais

#tabelas parciais

cand2_r1 = dict_1a['cand2']
cand2_r2 = dict_2a['cand2']
cand2_r3 = dict_3a['cand2']
cand2_r4 = dict_4a['cand2']

candidates_r1 = np.ones((nmini,2))*np.nan
candidates_r2 = np.ones((nmini,2))*np.nan
candidates_r3 = np.ones((nmini,2))*np.nan
candidates_r4 = np.ones((nmini,2))*np.nan
candidates_seq = np.ones((nmini,4))*np.nan


#monta a tabela
for irow in df_tble_mini.itertuples():

    print(" - table: mini {}".format(i))


    # round 1
    i = irow.mini
    candidates_r1[i,0] = i #mini
    cotrecho = cand2_r1[i,0]
    if cotrecho>0:
        j = np.nonzero(bho_cotrecho_filt==cotrecho)
        candidates_r1[i,1] = bho_cotrecho_filt[j]

    # round 2
    candidates_r2[i,0] = i #mini
    cotrecho = cand2_r2[i,0]
    if cotrecho>0:
        j = np.nonzero(bho_cotrecho_filt==cotrecho)
        candidates_r2[i,1] = bho_cotrecho_filt[j]


    # round 3
    i = irow.mini
    candidates_r3[i,0] = i #mini
    cotrecho = cand2_r3[i,0]
    if cotrecho>0:
        j = np.nonzero(bho_cotrecho_filt==cotrecho)
        candidates_r3[i,1] = bho_cotrecho_filt[j]

    # round 4
    i = irow.mini
    candidates_r4[i,0] = i #mini
    cotrecho = cand2_r4[i,0]
    if cotrecho>0:
        j = np.nonzero(bho_cotrecho_filt==cotrecho)
        candidates_r4[i,1] = bho_cotrecho_filt[j]




headers = ['mini','cotrecho']
df_tble_r1 = pd.DataFrame(candidates_r1,columns = headers)
df_tble_r2 = pd.DataFrame(candidates_r2,columns = headers)
df_tble_r3 = pd.DataFrame(candidates_r3,columns = headers)
df_tble_r4 = pd.DataFrame(candidates_r4,columns = headers)
df_parcial = pd.concat([df_tble_r1,df_tble_r2,df_tble_r3,df_tble_r4],axis=1)
df_parcial.to_excel('table_t1_partial.xlsx')
'''
