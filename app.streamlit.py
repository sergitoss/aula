import pandas as pd
import streamlit as st
import plotly.express as px
import geopandas as gpd
import json
from datetime import datetime
import numpy as np
import folium
from streamlit_folium import st_folium
from uuid import uuid4
import copy

# ============================================
# FUNÇÕES E CONFIGURAÇÕES INICIAIS
# ============================================

@st.cache_data
def carregar_dados_agua():
    datas = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    num_registros = len(datas)
    dados = {
        'data': datas,
        'temperatura': np.random.normal(25, 5, num_registros),
        'ph': np.random.normal(7, 1.5, num_registros),
        'condutividade': np.random.normal(500, 200, num_registros),
        'turbidez': np.random.normal(10, 5, num_registros),
        'localizacao': np.random.choice(['Ponto 1', 'Ponto 2', 'Ponto 3'], num_registros),
        'latitude': np.random.uniform(-15.7, -15.9, num_registros),
        'longitude': np.random.uniform(-47.8, -48.0, num_registros)
    }
    return pd.DataFrame(dados)

parametros = {
    "Temperatura": "temperatura",
    "pH": "ph",
    "Condutividade": "condutividade",
    "Turbidez": "turbidez"
}

unidades = {
    "Temperatura": "°C",
    "pH": "",
    "Condutividade": "µS/cm",
    "Turbidez": "NTU"
}

limites = {
    "Temperatura": {"min": 10, "max": 30},
    "pH": {"min": 6.5, "max": 8.5},
    "Condutividade": {"max": 1000},
    "Turbidez": {"max": 5}
}

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        st.image('assets/ufma.png', width=110)
    with col2:
        st.image('assets/lageos.png', width=110)

    st.markdown("""
    <div style='text-align:center; margin-top:10px'>
        <p style='font-size:16px; margin-bottom:5px'><strong>UFMA • LAGEOS</strong></p>
        <h4 style='margin-top:0; margin-bottom:10px'>Plataforma de monitoramento ambiental</h4>
        <p style='font-size:14px; margin-top:0'>Sistema de monitoramento da qualidade da água usando sensores Arduino</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Gerenciamento de Pontos de Coleta")
    uploaded_file = st.file_uploader("Carregar GeoJSON com pontos", type=['geojson'])

    with st.expander("Adicionar Ponto Manualmente"):
        nome_ponto = st.text_input("Nome do ponto")
        lat = st.number_input("Latitude", value=-15.8)
        lon = st.number_input("Longitude", value=-47.9)
        if st.button("Adicionar Ponto"):
            novo_ponto = {
                "type": "Feature",
                "properties": {"name": nome_ponto},
                "geometry": {"type": "Point", "coordinates": [lon, lat]}
            }
            if 'pontos_geojson' not in st.session_state:
                st.session_state['pontos_geojson'] = {"type": "FeatureCollection", "features": []}
            features = st.session_state['pontos_geojson']['features']
            features.append(novo_ponto)
            st.session_state['pontos_geojson'] = {
                "type": "FeatureCollection",
                "features": features
            }
            st.success(f"Ponto {nome_ponto} adicionado!")
            st.rerun()

    if st.button("Baixar pontos GeoJSON"):
        geojson_str = json.dumps(st.session_state['pontos_geojson'])
        st.download_button("Download GeoJSON", geojson_str, file_name="pontos.geojson", mime="application/json")

# ============================================
# DADOS
# ============================================

df = carregar_dados_agua()

if uploaded_file is not None:
    try:
        geojson_data = json.load(uploaded_file)
        st.session_state['pontos_geojson'] = copy.deepcopy(geojson_data)
        st.success("GeoJSON carregado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {e}")

if 'pontos_geojson' not in st.session_state:
    st.session_state['pontos_geojson'] = {"type": "FeatureCollection", "features": []}

# ============================================
# INTERFACE PRINCIPAL
# ============================================

st.title('LAGEOS - Monitoramento da Qualidade da Água')
st.markdown('**Laboratório de Geoprocessamento e Sensoriamento Remoto**')

st.header("Mapa de Pontos de Coleta")
m = folium.Map(location=[-15.8, -47.9], zoom_start=11)

if st.session_state['pontos_geojson']['features']:
    for feature in st.session_state['pontos_geojson']['features']:
        nome = feature['properties']['name']
        coords = feature['geometry']['coordinates']
        folium.Marker(
            location=[coords[1], coords[0]],
            popup=nome,
            tooltip=f"Ponto: {nome}",
            icon=folium.Icon(color='blue', icon='tint')
        ).add_to(m)

map_key = str(uuid4())
st_folium(m, width=700, height=500, key=map_key)

# ============================================
# ANÁLISE
# ============================================

parametro_analise = st.sidebar.selectbox("Selecione o parâmetro para análise", list(parametros.keys()))
coluna = parametros[parametro_analise]

periodo = st.sidebar.date_input("Selecione o período de análise", [df['data'].min(), df['data'].max()])
if len(periodo) == 2:
    filtro = (df['data'] >= pd.to_datetime(periodo[0])) & (df['data'] <= pd.to_datetime(periodo[1]))
    df_filtrado = df.loc[filtro].copy()
else:
    st.warning("Selecione um intervalo de datas válido.")
    df_filtrado = df.copy()

st.header(f"Análise de {parametro_analise}")

fig_temporal = px.line(
    df_filtrado,
    x='data',
    y=coluna,
    color='localizacao',
    title=f"Variação de {parametro_analise} ao longo do tempo",
    labels={coluna: f"{parametro_analise} ({unidades[parametro_analise]})"},
    color_discrete_sequence=px.colors.qualitative.Plotly
)
st.plotly_chart(fig_temporal, use_container_width=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Média", f"{df_filtrado[coluna].mean():.2f} {unidades[parametro_analise]}")
with col2:
    st.metric("Máximo", f"{df_filtrado[coluna].max():.2f} {unidades[parametro_analise]}")
with col3:
    st.metric("Mínimo", f"{df_filtrado[coluna].min():.2f} {unidades[parametro_analise]}")
with col4:
    st.metric("Desvio Padrão", f"{df_filtrado[coluna].std():.2f} {unidades[parametro_analise]}")

st.subheader(f"Distribuição de {parametro_analise} por ponto de coleta")
fig_boxplot = px.box(
    df_filtrado,
    x='localizacao',
    y=coluna,
    color='localizacao',
    labels={coluna: f"{parametro_analise} ({unidades[parametro_analise]})"}
)
st.plotly_chart(fig_boxplot, use_container_width=True)

st.subheader("📊 Comparativo por Local")
fig_box = px.box(df, x='localizacao', y=param, color='localizacao', points='all')
st.plotly_chart(fig_box, use_container_width=True)


st.subheader("Correlação entre parâmetros")
matriz_correlacao = df_filtrado[['temperatura', 'ph', 'condutividade', 'turbidez']].corr()
fig_correlacao = px.imshow(matriz_correlacao, text_auto=True, color_continuous_scale="Blues")
st.plotly_chart(fig_correlacao, use_container_width=True)

st.subheader("Índice de Qualidade da Água (IQA simplificado)")
df_filtrado['iqa'] = (
    (df_filtrado['temperatura'].clip(0, 30) / 30 * 0.15) +
    ((df_filtrado['ph'].clip(6, 9) - 6) / 3 * 0.25) +
    ((1 - (df_filtrado['condutividade'].clip(0, 1000) / 1000)) * 0.30) +
    ((1 - (df_filtrado['turbidez'].clip(0, 50) / 50)) * 0.30)
) * 100
fig_iqa = px.line(df_filtrado, x='data', y='iqa', color='localizacao', labels={'iqa': 'IQA (0-100)'}, range_y=[0, 100])
st.plotly_chart(fig_iqa, use_container_width=True)

st.subheader("Alertas de Qualidade da Água")
if parametro_analise in limites:
    limite = limites[parametro_analise]
    alertas = []
    if "min" in limite:
        alerta_min = df_filtrado[df_filtrado[coluna] < limite["min"]]
        if not alerta_min.empty:
            alertas.append(f"Valores abaixo do mínimo ({limite['min']} {unidades[parametro_analise]})")
    if "max" in limite:
        alerta_max = df_filtrado[df_filtrado[coluna] > limite["max"]]
        if not alerta_max.empty:
            alertas.append(f"Valores acima do máximo ({limite['max']} {unidades[parametro_analise]})")
    if alertas:
        for alerta in alertas:
            st.warning(alerta)
    else:
        st.success("Todos os valores dentro dos limites recomendados")
else:
    st.info("Limites não definidos para este parâmetro")

# Sobre o projeto
with st.expander("👑 Sobre o Projeto "):
    st.markdown("""
    Este painel foi desenvolvido para o **Plataforma de monitoramento Abiental**, focado no monitoramento ambiental de corpos d'água
    utilizando sensores conectados (Arduino), com análise de qualidade da água (IQA), visualização geográfica
    e gráficos interativos para facilitar a tomada de decisão. 💧💻🌍

    """)