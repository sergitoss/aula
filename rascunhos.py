import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import folium
from streamlit_folium import folium_static

# Função para carregar o GeoDataFrame com cache
@st.cache_data
def load_geodata():
    return gpd.read_file('assets/BR_UF_2020_filtrado.geojson')

# Função para carregar os dados de qualidade da água
@st.cache_data
def load_water_data():
    # Substitua isso pelo carregamento da sua planilha de Excel online ou arquivo local
    # Exemplo: pd.read_excel('URL_DA_PLANILHA')
    return pd.read_csv('assets/dados_agua.csv')  # Exemplo com um arquivo CSV

# Carregar os dados
gdf = load_geodata()
df = load_water_data()

# Verificar se as colunas necessárias estão presentes
required_columns = ['Data', 'pH', 'Condutividade', 'Turbidez', 'Temperatura', 'Estado']
if not all(column in df.columns for column in required_columns):
    st.error(f"A planilha deve conter as seguintes colunas: {', '.join(required_columns)}")
    st.stop()

# Converter a coluna de data para o formato adequado
df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')

# Adicionar a logo na barra lateral
with st.sidebar:
    st.image('assets/logo laboratório.png', width=210)

# Título e descrição
st.title('LAGEOS - Monitoramento da Qualidade da Água')
st.markdown('''Laboratório de Geoprocessamento e Sensoriamento Remoto''')

# Menu lateral para o tipo de análise
with st.sidebar:
    st.subheader('''Plataforma de monitoramento ambiental: uma abordagem arduino para qualidade da água.''')
    analise_tipo = st.selectbox("Selecione o tipo de análise", ["Temperatura", "pH", "Condutividade", "Turbidez"])

# Agrupar os dados por estado
df_estado = df.groupby('Estado').agg(
    pH_medio=('pH', 'mean'),
    condutividade_media=('Condutividade', 'mean'),
    turbidez_media=('Turbidez', 'mean'),
    temperatura_media=('Temperatura', 'mean')
).reset_index()

# Unir os dados geográficos com os dados de qualidade da água
gdf = gdf.merge(df_estado, left_on='SIGLA_UF', right_on='Estado', how='left')

# Selecionar a métrica com base no tipo de análise
metric_options = {
    'Temperatura': 'temperatura_media',
    'pH': 'pH_medio',
    'Condutividade': 'condutividade_media',
    'Turbidez': 'turbidez_media'
}
selected_metric = metric_options[analise_tipo]

# Exibir informações na barra lateral
with st.sidebar:
    estado_max = df_estado.loc[df_estado[selected_metric].idxmax()]['Estado']
    valor_max = df_estado[selected_metric].max()
    st.markdown(
        f"**Estado com maior {analise_tipo.lower()}:** {estado_max} "
        f"com {valor_max:.2f}.\n\n"
    )

# Criar gráfico de barras por estado
fig_bar = px.bar(
    df_estado, x='Estado', y=selected_metric,
    title=f'{analise_tipo} Médio por Estado',
    labels={'Estado': 'Estado', selected_metric: f'{analise_tipo} Médio'}
)
st.plotly_chart(fig_bar, use_container_width=True)

# Exibir o mapa de calor por estado
st.subheader(f"Mapa de {analise_tipo} Médio por Estado")
m = folium.Map(location=[-15.78, -47.93], zoom_start=3)
gdf.explore(
    m=m,
    column=selected_metric,
    cmap='BuPu',
    scheme='Quantiles',
    style_kwds=dict(color="black", weight=2, opacity=0.4),
    k=4,
    legend=True,
    legend_kwds=dict(colorbar=False, caption=f'{analise_tipo} Médio')
)
folium_static(m, width=800, height=600)

# Exibir gráfico de linha temporal
st.subheader(f"Variação de {analise_tipo} ao Longo do Tempo")
df['Ano'] = df['Data'].dt.year
df_ano = df.groupby('Ano')[analise_tipo].mean().reset_index()
fig_line = px.line(df_ano, x='Ano', y=analise_tipo, title=f'Variação de {analise_tipo} ao Longo dos Anos')
st.plotly_chart(fig_line, use_container_width=True)

# Exibir os dados brutos
st.subheader("Dados Brutos")
st.write(df)










import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

## Função para carregar dados simulados - substituir por dados reais
@st.cache_data
def carregar_dados_agua():
    # Gera dados simulados para demonstração
    datas = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    num_registros = len(datas)
    
    dados = {
        'data': datas,
        'temperatura': np.random.normal(25, 5, num_registros),
        'ph': np.random.normal(7, 1.5, num_registros),
        'condutividade': np.random.normal(500, 200, num_registros),
        'turbidez': np.random.normal(10, 5, num_registros),
        'localizacao': np.random.choice(['Ponto 1', 'Ponto 2', 'Ponto 3'], num_registros)
    }
    
    return pd.DataFrame(dados)

# Carregar dados
df = carregar_dados_agua()

## Configuração da barra lateral
with st.sidebar:
    st.image('assets/logo laboratório.png', width=250)
    st.subheader('Plataforma de monitoramento ambiental')
    st.markdown('''Sistema de monitoramento da qualidade da água usando sensores Arduino''')

## Título e descrição
st.title('LAGEOS - Monitoramento da Qualidade da Água')
st.markdown('''**Laboratório de Geoprocessamento e Sensoriamento Remoto**  
            Sistema de monitoramento em tempo real dos parâmetros de qualidade da água.''')

## Seleção do tipo de análise
parametro_analise = st.sidebar.selectbox(
    "Selecione o parâmetro para análise",
    ["Temperatura", "pH", "Condutividade", "Turbidez"]
)

## Seletor de período de análise
periodo = st.sidebar.date_input(
    "Selecione o período de análise",
    [df['data'].min(), df['data'].max()],
    min_value=df['data'].min(),
    max_value=df['data'].max()
)

## Filtrar dados conforme período selecionado
if len(periodo) == 2:
    filtro = (df['data'] >= pd.to_datetime(periodo[0])) & (df['data'] <= pd.to_datetime(periodo[1]))
    df_filtrado = df.loc[filtro]
else:
    df_filtrado = df

## Mapeamento de unidades para cada parâmetro
unidades = {
    "Temperatura": "°C",
    "pH": "",
    "Condutividade": "µS/cm",
    "Turbidez": "NTU"
}

## Visualização principal
st.header(f"Análise de {parametro_analise}")

## Gráfico de série temporal
fig_temporal = px.line(
    df_filtrado,
    x='data',
    y=parametro_analise.lower(),
    color='localizacao',
    title=f"Variação de {parametro_analise} ao longo do tempo",
    labels={parametro_analise.lower(): f"{parametro_analise} ({unidades[parametro_analise]})"}
)
st.plotly_chart(fig_temporal, use_container_width=True)

## Cartões com estatísticas
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        label="Média",
        value=f"{df_filtrado[parametro_analise.lower()].mean():.2f} {unidades[parametro_analise]}"
    )
with col2:
    st.metric(
        label="Máximo",
        value=f"{df_filtrado[parametro_analise.lower()].max():.2f} {unidades[parametro_analise]}"
    )
with col3:
    st.metric(
        label="Mínimo",
        value=f"{df_filtrado[parametro_analise.lower()].min():.2f} {unidades[parametro_analise]}"
    )
with col4:
    st.metric(
        label="Desvio Padrão",
        value=f"{df_filtrado[parametro_analise.lower()].std():.2f} {unidades[parametro_analise]}"
    )

## Distribuição por ponto de coleta
st.subheader(f"Distribuição de {parametro_analise} por ponto de coleta")
fig_boxplot = px.box(
    df_filtrado,
    x='localizacao',
    y=parametro_analise.lower(),
    color='localizacao',
    title=f"Distribuição de {parametro_analise} por localização",
    labels={parametro_analise.lower(): f"{parametro_analise} ({unidades[parametro_analise]})"}
)
st.plotly_chart(fig_boxplot, use_container_width=True)

## Análise de correlação
st.subheader("Correlação entre parâmetros")
matriz_correlacao = df_filtrado[['temperatura', 'ph', 'condutividade', 'turbidez']].corr()
fig_correlacao = px.imshow(
    matriz_correlacao,
    text_auto=True,
    color_continuous_scale="Blues",
    title="Matriz de correlação entre parâmetros"
)
st.plotly_chart(fig_correlacao, use_container_width=True)

## Cálculo do Índice de Qualidade da Água (simplificado)
st.subheader("Índice de Qualidade da Água (IQA simplificado)")
# Cálculo simplificado - substituir por fórmula oficial do IQA
df_filtrado['iqa'] = (
    # Temperatura (0-30°C) - 15% do IQA
    (df_filtrado['temperatura'].clip(0, 30) / 30 * 0.15) +
    
    # pH (6-9) - 25% do IQA
    ((df_filtrado['ph'].clip(6, 9) - 6) / 3 * 0.25) +
    
    # Condutividade (0-1000 µS/cm) - 30% do IQA
    ((1 - (df_filtrado['condutividade'].clip(0, 1000) / 1000)) * 0.30) +
    
    # Turbidez (0-50 NTU) - 30% do IQA
    ((1 - (df_filtrado['turbidez'].clip(0, 50) / 50)) * 0.30)
) * 100  # Converte para escala 0-100

fig_iqa = px.line(
    df_filtrado,
    x='data',
    y='iqa',
    color='localizacao',
    title="Índice de Qualidade da Água ao longo do tempo",
    labels={'iqa': 'IQA (0-100)'},
    range_y=[0, 100]
)
st.plotly_chart(fig_iqa, use_container_width=True)

## Sistema de alertas
st.subheader("Alertas de Qualidade da Água")
limites = {
    "Temperatura": {"min": 10, "max": 30},
    "pH": {"min": 6.5, "max": 8.5},
    "Condutividade": {"max": 1000},
    "Turbidez": {"max": 5}
}

if parametro_analise in limites:
    limite = limites[parametro_analise]
    alertas = []
    
    if "min" in limite:
        alerta_min = df_filtrado[df_filtrado[parametro_analise.lower()] < limite["min"]]
        if not alerta_min.empty:
            alertas.append(f"Valores abaixo do mínimo ({limite['min']} {unidades[parametro_analise]})")
    
    if "max" in limite:
        alerta_max = df_filtrado[df_filtrado[parametro_analise.lower()] > limite["max"]]
        if not alerta_max.empty:
            alertas.append(f"Valores acima do máximo ({limite['max']} {unidades[parametro_analise]})")
    
    if alertas:
        for alerta in alertas:
            st.warning(alerta)
    else:
        st.success(f"Todos os valores de {parametro_analise} dentro dos limites recomendados")
else:
    st.info("Limites não definidos para este parâmetro")