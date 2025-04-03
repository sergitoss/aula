import pandas as pd
import os  # Para garantir que o diretório "assets" exista
import geopandas as gpd

def load_data():
    """
    Carrega os dados do CSV a partir de uma URL.
    """
    url = 'https://dados.agricultura.gov.br/dataset/baefdc68-9bad-4204-83e8-f2888b79ab48/resource/ac7e4351-974f-4958-9294-627c5cbf289a/download/psr-2024c.csv'
    df = pd.read_csv(url, encoding='latin1', sep=';', low_memory=False)
    return df

# Carrega os dados
df = load_data()

# Remove colunas desnecessárias
df.drop(columns=[
    'CD_PROCESSO_SUSEP', 'NR_PROPOSTA', 'ID_PROPOSTA',
    'DT_PROPOSTA', 'DT_INICIO_VIGENCIA', 'DT_FIM_VIGENCIA',
    'NM_SEGURADO', 'NR_DOCUMENTO_SEGURADO',
    'LATITUDE', 'NR_GRAU_LAT', 'NR_MIN_LAT', 'NR_SEG_LAT',
    'LONGITUDE', 'NR_GRAU_LONG', 'NR_MIN_LONG', 'NR_SEG_LONG',
    'NR_DECIMAL_LATITUDE', 'NR_DECIMAL_LONGITUDE',
    'NivelDeCobertura', 'DT_APOLICE',
    'ANO_APOLICE', 'CD_GEOCMU'
], inplace=True)

# Cria o diretório "assets" se ele não existir
os.makedirs('assets', exist_ok=True)

# Salva o DataFrame em um arquivo Parquet
df.to_parquet('assets/dados_test.parquet', engine='fastparquet')

def load_geodata():
    """
    Carrega o shapefile com os estados do Brasil.
    """
    return gpd.read_file('datasets/BR_UF_2020.shp')

# Carregar os dados geográficos
gdf = load_geodata()

# Verifica as colunas disponíveis no GeoDataFrame
print("Colunas disponíveis no GeoDataFrame:")
print(gdf.columns)

# Define a tolerância para a simplificação (ajuste o valor conforme necessário)
tolerancia = 0.01  # Unidade é geralmente em graus, ajuste conforme a precisão desejada

# Aplica a simplificação mantendo a topologia
gdf['geometry'] = gdf['geometry'].simplify(tolerance=tolerancia, preserve_topology=True)

# Remove colunas desnecessárias (ajuste a lista conforme as colunas disponíveis)
colunas_para_remover = ['CD_UF', 'NM_UF', 'NM_REGIAO']  # Remova 'AREA_KM2' se não existir
gdf.drop(columns=colunas_para_remover, inplace=True)

# Salva o GeoDataFrame simplificado em GeoJSON
gdf.to_file('assets/BR_UF_2020_filtrado.geojson', driver='GeoJSON')



#LEGENDAS E BOTOES 

st.dataframe(df)

lista = list(df.columns)

botao = st.sidebar.selectbox('Selecione a variével', options=lista)
lista = list(df.columns)

valor_slider = st.slider('Defina o valor', min_value=50, max_value=100, step=1)

# Supondo que 'df' seja um DataFrame já carregado
valor = str(df['VL_LIMITE_GARANTIA'].max())

# Criando três colunas
col1, col2, col3 = st.columns(3)

# Adicionando um contêiner com uma métrica na primeira coluna
with col1:
    with st.container(border=True):
        st.metric('Tem', df[botao].max())

with col2:
    with st.container(border=True):
        st.metric('pH', 20)

with col3:
    with st.container(border=True):
        st.metric('OX', 50)