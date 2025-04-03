import pandas as pd
import geopandas as gpd
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import folium_static

# Função para carregar o GeoDataFrame com cache
@st.cache_data
def load_geodata():
    return gpd.read_file('assets/BR_UF_2020_filtrado.geojson')

# Função para carregar o DataFrame de dados de seguros com cache
@st.cache_data
def load_data():
    file_path = 'assets/dados_test.parquet'
    return pd.read_parquet(file_path)

# Carregar os dados
gdf = load_geodata()
df = load_data()

# Adicionar a logo na barra lateral
with st.sidebar:
    st.image('assets/logo laboratório.png', width=210)

# Limpar dados numéricos convertendo para float
cols = ['NR_AREA_TOTAL', 'VL_PREMIO_LIQUIDO']
df[cols] = df[cols].replace(',', '.', regex=True).astype(float)

# Agrupar os dados por estado
df_estado = df.groupby('SG_UF_PROPRIEDADE').agg(
    area_total=('NR_AREA_TOTAL', 'sum'),
    valor_total=('VL_PREMIO_LIQUIDO', 'sum'),
    numero_seguros=('NR_APOLICE', 'nunique')
).reset_index()

# Unir os dados geográficos com os dados de seguros
gdf_merged = gdf.merge(df_estado, left_on='SIGLA_UF', right_on='SG_UF_PROPRIEDADE', how='left')

# Agrupar os dados por razão social
df_razao_social = df.groupby('NM_RAZAO_SOCIAL').agg(
    numero_seguros=('NR_APOLICE', 'nunique'),
    area_total=('NR_AREA_TOTAL', 'sum'),
    valor_total=('VL_PREMIO_LIQUIDO', 'sum'),
    estados=('SG_UF_PROPRIEDADE', 'unique')
).reset_index()

df_razao_social['contagem_estados'] = df_razao_social['estados'].apply(len)

df_razao_social_estado = df.groupby(['NM_RAZAO_SOCIAL', 'SG_UF_PROPRIEDADE']).agg(
    numero_seguros=('NR_APOLICE', 'nunique'),
    area_total=('NR_AREA_TOTAL', 'sum'),
    valor_total=('VL_PREMIO_LIQUIDO', 'sum')
).reset_index()

# Selecionar colunas para correlação
correlation_columns = [
    'NR_AREA_TOTAL', 'VL_PREMIO_LIQUIDO', 'VL_LIMITE_GARANTIA',
    'NR_PRODUTIVIDADE_ESTIMADA', 'NR_PRODUTIVIDADE_SEGURADA', 'VL_SUBVENCAO_FEDERAL'
]

for col in correlation_columns:
    if col in df.columns:
        df[col] = df[col].replace(',', '.', regex=True).astype(float)

correlation_matrix = df[correlation_columns].corr().round(2)

# Definir o título e descrição do sistema
st.title("Análise de Seguros Agrícolas - SISSER")
st.markdown('''**Sistema de Subvenção Econômica ao Prêmio do Seguro Rural**  
*Dados atualizados em 2023* ''')

st.divider()

# Mapa interativo Plotly (versão modificada)
try:
    hover_col = 'NM_UF' if 'NM_UF' in gdf_merged.columns else 'SIGLA_UF'
    
    fig_map = px.choropleth(gdf_merged, 
                           geojson=gdf_merged.geometry,
                           locations=gdf_merged.index,
                           color='numero_seguros',
                           hover_name=hover_col,
                           hover_data=['area_total', 'valor_total'],
                           color_continuous_scale="Blues",
                           projection="mercator",
                           title="Distribuição Geográfica de Apólices por Estado")
    
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    
    fig_map.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>"
                     "Apólices: %{z}<br>"
                     "Área: %{customdata[0]:,.2f} ha<br>"
                     "Valor: R$ %{customdata[1]:,.2f}"
    )
    
    st.plotly_chart(fig_map, use_container_width=True)
    
except Exception as e:
    st.error(f"Erro ao gerar o mapa: {str(e)}")
    st.write("Dados disponíveis para mapeamento:", gdf_merged.columns.tolist())

st.divider()

# Menu lateral para o tipo de análise
with st.sidebar:
    st.subheader('''SISSER - Sistema de Subvenção Econômica ao Prêmio do Seguro Rural. Fonte: [SISSER](https://dados.google.com/view/sss?id=0&id=1)''')
    analise_tipo = st.selectbox("Selecione o tipo de análise", ["Razão Social", "Estado"])
   
if analise_tipo == "Razão Social":
    st.header("Análise por Razão Social")

# Selecionar métricas
metric_options = {
    'Número de Seguros': 'numero_seguros',
    'Contagem de Estados': 'contagem_estados',
    'Área Total': 'area_total'
}

# Calcular os estados com maiores valores
top_estado_num_apolices = df_estado.loc[df_estado['numero_seguros'].idxmax()]
top_estado_area_total = df_estado.loc[df_estado['area_total'].idxmax()]
top_estado_valor_total = df_estado.loc[df_estado['valor_total'].idxmax()]

# Exibir informações na barra lateral
with st.sidebar:
    st.markdown(
        f"**Estado com maior número de apólices:** {top_estado_num_apolices['SG_UF_PROPRIEDADE']} "
        f"com {top_estado_num_apolices['numero_seguros']} apólices.\n\n"
        f"**Estado com maior área total assegurada:** {top_estado_area_total['SG_UF_PROPRIEDADE']} "
        f"com {top_estado_area_total['area_total']:.2f} ha.\n\n"
        f"**Estado com maior valor total assegurado:** {top_estado_valor_total['SG_UF_PROPRIEDADE']} "
        f"com R$ {top_estado_valor_total['valor_total']:.2f}."
    )

# Menu dropdown para selecionar métrica
selected_metric = st.selectbox("Selecione a Métrica", options=list(metric_options.keys()))
metric_column = metric_options[selected_metric]

df_sorted = df_razao_social.sort_values(by=metric_column, ascending=False)

# Criar gráfico
fig_bar = px.bar(
    df_sorted, x='NM_RAZAO_SOCIAL', y=metric_column,
    title=f'{selected_metric} por Razão Social',
    labels={'NM_RAZAO_SOCIAL': 'Razão Social', metric_column: selected_metric}
)

st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# Cálculo das métricas para os cartões
max_num_seguros = df_razao_social['numero_seguros'].max()
mean_num_seguros = df_razao_social['numero_seguros'].mean()
var_num_seguros = ((max_num_seguros - mean_num_seguros) / mean_num_seguros) * 100
top_razao_num_seguros = df_razao_social[df_razao_social['numero_seguros'] == max_num_seguros]['NM_RAZAO_SOCIAL'].values[0]

max_count_estados = df_razao_social['contagem_estados'].max()
mean_count_estados = df_razao_social['contagem_estados'].mean()
var_count_estados = ((max_count_estados - mean_count_estados) / mean_count_estados) * 100
top_razao_count_estados = df_razao_social[df_razao_social['contagem_estados'] == max_count_estados]['NM_RAZAO_SOCIAL'].values[0]

max_area_total = df_razao_social['area_total'].max()
mean_area_total = df_razao_social['area_total'].mean()
var_area_total = ((max_area_total - mean_area_total) / mean_area_total) * 100
top_razao_area_total = df_razao_social[df_razao_social['area_total'] == max_area_total]['NM_RAZAO_SOCIAL'].values[0]

# Exibir os cartões com as métricas calculadas
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.metric(
            label=f"Máximo Número de Seguros - {top_razao_num_seguros}", 
            value=f"{max_num_seguros:.0f}", 
            delta=f"{var_num_seguros:.2f}% em relação à média"
        )

with col2:
    with st.container(border=True):
        st.metric(
            label=f"Máximo Contagem de Estados - {top_razao_count_estados}", 
            value=f"{max_count_estados:.0f}", 
            delta=f"{var_count_estados:.2f}% em relação à média"
        )

with col3:
    with st.container(border=True):
        st.metric(
            label=f"Máximo Área Total (ha) - {top_razao_area_total}", 
            value=f"{max_area_total:.2f}", 
            delta=f"{var_area_total:.2f}% em relação à média"
        )

st.divider()

# Exibir o gráfico de correlação de parâmetros
st.subheader("Correlação entre Parâmetros")
fig_heatmap = px.imshow(correlation_matrix, text_auto=True, color_continuous_scale="Blues",
                        title="Correlação entre Parâmetros", width=400, height=800)
st.plotly_chart(fig_heatmap, use_container_width=True)

# Exibir o gráfico de pizza do valor total por razão social
st.subheader("Distribuição do Valor Total por Razão Social")
fig_pie_valor = px.pie(
    df_razao_social,
    names='NM_RAZAO_SOCIAL',
    values='valor_total',
    title='Distribuição do Valor Total Assegurado por Razão Social'
)

# Configurar a legenda para aparecer em duas colunas com fonte menor
fig_pie_valor.update_layout(
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,
        xanchor="center",
        x=0.5,
        font=dict(size=10)
    )  # Fecha o dict()
)  # Fecha o update_layout()

st.plotly_chart(fig_pie_valor, use_container_width=True)

st.divider()

