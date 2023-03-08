# -*- coding: utf-8 -*-
"""
Prepara a base para publicacao

#TODO: ATUALIZAR NOME DO ARQUIVO COM DATA?!

@author: Mino Sorribas
"""
import numpy as np
from datetime import datetime
import pandas as pd
import geopandas as gpd


gdf = gpd.read_file('base_mgbbhods_20211013.gpkg')



#novas colunas
newcols = {
    'q95_ol':'Q95_OL',
    'qmlt_ol':'QM_OL',
    'q95e_ol':'Q95_sp_OL',
    'qmlte_ol':'QM_sp_OL',

    'q95_m02':'Q95_lower',
    'qmlt_m02':'QM_lower',
    'q95e_m02':'Q95_sp_lower',
    'qmlte_m02':'QM_sp_lower',

    'q95_m25':'Q95_median',
    'qmlt_m25':'QM_median',
    'q95e_m25':'Q95_sp_median',
    'qmlte_m25':'QM_sp_median',

    'q95_m48':'Q95_upper',
    'qmlt_m48':'QM_upper',
    'q95e_m48':'Q95_sp_upper',
    'qmlte_m48':'QM_sp_upper',
    }

gdf = gdf.rename(columns=newcols)


# inclui uma medida da largura da incerteza
gdf['QM_mvar'] = gdf.apply(lambda x: (x.QM_upper-x.QM_lower)/x.QM_median if x.QM_lower>0. else np.nan,axis=1)
gdf['Q95_mvar'] = gdf.apply(lambda x: (x.Q95_upper-x.Q95_lower)/x.Q95_median if x.Q95_lower>0. else np.nan,axis=1)


# atualiza versao pelo momento dessa rodada
ts = datetime.now().strftime('%Y-%b-%dT%H')


# incluir coluna descritiva de versao
gdf['versao'] = f'compativel com geoft_bho_2017_5k_trecho_drenagem em {ts}'

newfile = 'Base_Vazoes_Referencia_Modelagem_5K_20211013'

# exporta gpkg e excel
gdf.to_file(newfile + '.gpkg', driver='GPKG')
gdf.drop('geometry',axis=1).to_excel(newfile + '.xlsx')


# salva descricao em planilha
file_desc = 'Dicionario_' + newfile + '.xlsx'


hash_desc = {'cotrecho': 'Código do cotrecho BHO20175K',
          'cobacia':'Código da cobacia BHO20175K',
          'nuareacont':  'Área de contribuição do trecho',
          'nuareamont': 'Área de contribuição a montante',
          'nutrjus': 'Código do cotrecho a jusante BHO20175K',

          'mini_t1': 'Código da minibacia MGB-AS utilizado em downscaling tipo 1',
          'mini_t2': 'Código da minibacia MGB-AS utilizado em downscaling tipo 2',
          'mini_t3': 'Código da minibacia MGB-AS utilizado em downscaling tipo 3',
          'solver':  'Tipo de solução adotada no dowscaling',

          'Q95_OL': 'Vazão Q95 em m³/s pelo MGB-AS sem assimilação de dados',
          'QM_OL':  'Vazão média em m³/s pelo MGB-AS sem assimilação de dados',
          'Q95_sp_OL': 'Vazão Q95 específica em m³/s/km² pelo MGB-AS sem assimilação de dados',
          'QM_sp_OL': 'Vazão média específica em m³/s/km² pelo MGB-AS sem assimilação de dados',

          'Q95_lower': 'Limite inferior da vazão Q95 em m³/s pelo MGB-AS com assimilação de dados',
          'QM_lower': 'Limite inferior da vazão média em m³/s pelo MGB-AS com assimilação de dados',
          'Q95_sp_lower': 'Limite inferior da vazão Q95 específica em m³/s/km² pelo MGB-AS com assimilação de dados',
          'QM_sp_lower': 'Limite inferior da vazão média específica em m³/s/km² pelo MGB-AS com assimilação de dados',

          'Q95_median': 'Vazão Q95 em m³/s pelo MGB-AS com assimilação de dados',
          'QM_median': 'Vazão média em m³/s pelo MGB-AS com assimilação de dados',
          'Q95_sp_median': 'Vazão Q95 específica em m³/s/km² pelo MGB-AS com assimilação de dados',
          'QM_sp_median': 'Vazão média específica em m³/s/km² pelo MGB-AS com assimilação de dados',

          'Q95_upper': 'Limite superior da vazão Q95 em m³/s pelo MGB-AS com assimilação de dados',
          'QM_upper': 'Limite superior da vazão média em m³/s pelo MGB-AS com assimilação de dados',
          'Q95_sp_upper': 'Limite superior da vazão Q95 específica em m³/s/km² pelo MGB-AS com assimilação de dados',
          'QM_sp_upper': 'Limite superior da vazão média específica em m³/s/km² pelo MGB-AS com assimilação de dados',

          'QM_mvar': ' (QM_upper - QM_lower)/QM_median',
          'Q95_mvar': ' (Q95_upper - Q95_lower)/Q95_median',

          'versao': 'informacoes de versão'
          }


df_desc = pd.DataFrame.from_dict(hash_desc,orient='index',columns=['descricao'])
df_desc.index.name = 'atributo'
df_desc.to_excel(file_desc)

print('FIM DO PROGRAMA')