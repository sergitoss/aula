# Bibliotecas para análise de dados geoespaciais e visualização
import geemap  # geemap==0.32.1
import ee  # earthengine-api==0.1.412 (Google Earth Engine)
import folium  # folium==0.18.0
import geopandas as gpd  # geopandas==0.14.4
import pandas as pd  # pandas==2.2.2

# Bibliotecas auxiliares para manipulação de arquivos e dados
from path import Path  # path==16.4.0
import patoolib  # patool==1.12


# Dependências para geoprocessamento
import fiona
import setuptools
import streamlit as st
import geemap
import ee
import json
import os
import pandas as pd
import plotly.express as px

# Definir configuração da página primeiro
st.set_page_config(
    page_title="MapBiomas Coleção 9",
    page_icon="🌎",
    layout="wide"
)

# Inicialização do Earth Engine
try:
    ee.Initialize(project='ee-serginss')
except ee.EEException:
    ee.Authenticate()
    ee.Initialize(project='ee-serginss')

# Título e introdução
st.title('APP ALUNOS LAGEOS 🌱 MAPBIOMAS COLEÇÃO 9 - ANÁLISE DE USO DO SOLO')
st.write("""
    Este aplicativo permite a visualização interativa da classificação
    Coleção 9 do projeto MapBiomas. Com uma série histórica de 1985 a 2023,
    você pode selecionar o ano desejado e visualizar o uso do solo remapeado
    em alta resolução.
    
    **Fonte dos dados**: [MapBiomas](https://mapbiomas.org)
""")

# Processamento das imagens
mapbiomas_image = ee.Image('projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1')

# Códigos originais do MapBiomas (37 classes)
codes = [  
    1, 3, 4, 5, 6, 49,    # Floresta (6)
    10, 11, 12, 32, 29, 50,    # Vegetação Herbácea (6)  
    14, 15, 18, 19, 39, 20, 40, 62, 41, 36, 46, 47, 35, 48, 9, 21,  # Agropecuária (16)
    22, 23, 24, 30, 25,    # Área não Vegetada (5)  
    26, 33, 31,    # Corpo D'água (3)
    27    # Não Observado (1)
]

# Classes remapeadas (37 elementos correspondentes)
new_classes = [
    1, 1, 1, 1, 1, 1,     # Floresta -> classe 1 (6)
    2, 2, 2, 2, 2, 2,     # Vegetação Herbácea -> classe 2 (6)
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,  # Agropecuária -> classe 3 (16)
    4, 4, 4, 4, 4,        # Área não Vegetada -> classe 4 (5)
    5, 5, 5,              # Corpo D'água -> classe 5 (3)
    6                     # Não Observado -> classe 6 (1)
]

# Classes remapeadas e seus nomes oficiais
classes = {
    1: "Formação Florestal",
    2: "Formação Natural não Florestal",
    3: "Agropecuária",
    4: "Área não Vegetada",
    5: "Corpo D'água",
    6: "Não Observado"
}

# Paleta de cores oficial do MapBiomas (em hexadecimal)
palette = [
    '#006400',  # 1. Formação Florestal (verde escuro)
    '#B8AF4F',  # 2. Formação Natural não Florestal (amarelo-esverdeado)
    '#FFD966',  # 3. Agropecuária (amarelo)
    '#E974ED',  # 4. Área não Vegetada (rosa)
    '#0000FF',  # 5. Corpo D'água (azul)
    '#FFFFFF'   # 6. Não Observado (branco)
]

# Lista para armazenar as bandas remapeadas
remapped_bands = []

# Loop através de cada ano (1985 a 2023)
for year in range(1985, 2024):
    original_band = f'classification_{year}'
    # Remapear a banda usando os códigos e novas classes
    remapped_band = mapbiomas_image.select(original_band).remap(codes, new_classes).rename(original_band)
    remapped_bands.append(remapped_band)

# Combinar todas as bandas remapeadas em uma única imagem
remapped_image = ee.Image.cat(remapped_bands)

# Widget para seleção de anos
years = list(range(1985, 2024))
selected_years = st.multiselect('Selecione o(s) ano(s)', years, default=[2023])

# Widget para definição da área de estudo
with st.expander('Defina a área de estudo (opcional)'):
    geometry_input = st.text_area(
        "Insira as coordenadas de área de estudo em formato GeoJSON."
    )

geometry = None
if geometry_input:
    try:
        geometry = ee.Geometry(json.loads(geometry_input)['geometry'])
    except Exception as e:
        st.error(f'Erro no formato de coordenadas. Verifique o GeoJSON inserido. Detalhes: {str(e)}')

# Criação do mapa
m = geemap.Map(center=[-15, -55], zoom=6)

if geometry:
    try:
        study_area = ee.FeatureCollection(ee.Feature(geometry))
        m.centerObject(study_area, zoom=8)
        m.addLayer(
            study_area.style(**{'color': 'red', 'fillColor': '00000000'}),
            {},
            "Área de Estudo"
        )
        remapped_image = remapped_image.clip(geometry)
        st.success("Área de estudo aplicada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao processar a área de estudo: {str(e)}")

# Adicionar camadas ao mapa para cada ano selecionado
for year in selected_years:
    try:
        selected_band = f"classification_{year}"
        if selected_band in remapped_image.bandNames().getInfo():
            m.addLayer(
                remapped_image.select(selected_band),
                {
                    'min': 1,
                    'max': 6,
                    'palette': palette,
                    'bands': selected_band
                },
                f"MapBiomas {year}"
            )
        else:
            st.warning(f"O ano {year} não está disponível nos dados!")
    except Exception as e:
        st.error(f"Erro ao carregar o ano {year}: {str(e)}")

# Exibir o mapa
try:
    m.to_streamlit(
        height=600,
        responsive=True,
        scrolling=False,
        add_layer_control=True
    )
except Exception as e:
    st.error("Erro ao exibir o mapa. Verifique sua conexão e configurações.")
    st.error(f"Detalhes técnicos: {str(e)}")

# Cálculo e visualização de áreas
if geometry:
    st.subheader("Estatísticas de Área por Classe")
    areas = []
    for year in selected_years:
        band = remapped_image.select(f"classification_{year}")
        for class_value in range(1, 7):
            class_area = band.eq(class_value).multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            area_km2 = class_area.get(f"classification_{year}", 0) / 1e6
            areas.append({
                "Ano": year, 
                "Classe": class_value, 
                "Nome da Classe": classes[class_value], 
                "Área (km²)": area_km2
            })
    
    if areas:  # Só continua se houver áreas calculadas
        df_areas = pd.DataFrame(areas)
        
        # Layout de colunas
        col1, col2 = st.columns(2)

        # Exibir DataFrame
        with col1:
            st.dataframe(df_areas)

        # Exibir gráfico se houver mais de um ano
        if len(selected_years) > 1:
            with col2:
                fig = px.area(
                    df_areas,
                    x="Ano",
                    y="Área (km²)",
                    color="Nome da Classe",
                    title="Evolução da Área por Classe",
                    color_discrete_sequence=palette
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Selecione mais de um ano para visualizar o gráfico de evolução temporal.")


