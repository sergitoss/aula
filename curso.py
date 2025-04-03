# Importação de bibliotecas
import pandas as pd  # Para manipulação de dados tabulares (DataFrames)
import geopandas as gpd  # Para trabalhar com dados geoespaciais (mapas vetoriais)
import streamlit as st  # Framework para criar aplicações web interativas
import plotly.express as px  # Para criação de gráficos interativos e visualizações
import folium  # Biblioteca para criação de mapas interativos (não usado diretamente aqui)
from streamlit_folium import folium_static  # Para exibir mapas do Folium no Streamlit (não usado aqui)

# ==============================================
# 1. FUNÇÕES DE CARREGAMENTO DE DADOS
# ==============================================

# Decorador que armazena os dados em cache para melhor performance
@st.cache_data
def load_geodata():
    """Carrega o arquivo GeoJSON com os polígonos dos estados brasileiros"""
    return gpd.read_file('assets/BR_UF_2020_filtrado.geojson')  # Retorna um GeoDataFrame

@st.cache_data
def load_data():
    """Carrega os dados de seguros no formato Parquet (otimizado para leitura)"""
    return pd.read_parquet('assets/dados_test.parquet')  # Retorna um DataFrame

# ==============================================
# 2. CARREGAMENTO E PREPARAÇÃO DOS DADOS
# ==============================================

# Carrega os datasets chamando as funções definidas acima
gdf = load_geodata()  # GeoDataFrame com geometrias dos estados
df = load_data()      # DataFrame com dados de seguros agrícolas

# Lista de colunas numéricas que precisam de tratamento
cols_numericas = ['NR_AREA_TOTAL', 'VL_PREMIO_LIQUIDO']

# Converte vírgula para ponto (padrão BR) e transforma em float (para cálculos)
df[cols_numericas] = df[cols_numericas].replace(',', '.', regex=True).astype(float)

# ==============================================
# 3. PROCESSAMENTO E AGREGAÇÃO DOS DADOS
# ==============================================

# Agrupa os dados por estado (SG_UF_PROPRIEDADE) e calcula métricas agregadas
df_estado = df.groupby('SG_UF_PROPRIEDADE').agg(
    area_total=('NR_AREA_TOTAL', 'sum'),  # Soma a área total por estado
    valor_total=('VL_PREMIO_LIQUIDO', 'sum'),  # Soma o valor total por estado
    numero_seguros=('NR_APOLICE', 'nunique')  # Conta apólices únicas por estado
).reset_index()  # Transforma o índice em coluna novamente

# Combina os dados geográficos com os dados agregados por estado
gdf_merged = gdf.merge(
    df_estado, 
    left_on='SIGLA_UF',  # Coluna do GeoDataFrame
    right_on='SG_UF_PROPRIEDADE',  # Coluna do DataFrame
    how='left'  # Mantém todos os estados mesmo sem dados
)

# Agrupa os dados por razão social (nome da empresa)
df_razao_social = df.groupby('NM_RAZAO_SOCIAL').agg(
    numero_seguros=('NR_APOLICE', 'nunique'),  # Conta apólices únicas
    area_total=('NR_AREA_TOTAL', 'sum'),  # Soma a área total
    valor_total=('VL_PREMIO_LIQUIDO', 'sum'),  # Soma o valor total
    estados=('SG_UF_PROPRIEDADE', 'unique')  # Lista de estados onde atua
).reset_index()

# Adiciona coluna com contagem de estados por empresa
df_razao_social['contagem_estados'] = df_razao_social['estados'].apply(len)

# Agrupa por razão social E estado (cruzamento)
df_razao_social_estado = df.groupby(['NM_RAZAO_SOCIAL', 'SG_UF_PROPRIEDADE']).agg(
    numero_seguros=('NR_APOLICE', 'nunique'),
    area_total=('NR_AREA_TOTAL', 'sum'),
    valor_total=('VL_PREMIO_LIQUIDO', 'sum')
).reset_index()

# Lista de colunas para análise de correlação
cols_correlacao = [
    'NR_AREA_TOTAL', 
    'VL_PREMIO_LIQUIDO', 
    'VL_LIMITE_GARANTIA',
    'NR_PRODUTIVIDADE_ESTIMADA', 
    'NR_PRODUTIVIDADE_SEGURADA', 
    'VL_SUBVENCAO_FEDERAL'
]

# Padroniza formato numérico para as colunas de correlação
for col in cols_correlacao:
    if col in df.columns:  # Verifica se a coluna existe
        df[col] = df[col].replace(',', '.', regex=True).astype(float)

# Calcula a matriz de correlação com 2 casas decimais
correlation_matrix = df[cols_correlacao].corr().round(2)

# ==============================================
# 4. CONFIGURAÇÃO DA INTERFACE DO DASHBOARD
# ==============================================

# Configuração da barra lateral
with st.sidebar:  # Tudo aqui dentro vai na sidebar
    st.image('assets/logo laboratório.png', width=210)  # Exibe logo
    st.subheader('SISSER - Sistema de Subvenção Econômica')  # Título
    
    # Dropdown para selecionar tipo de análise
    analise_tipo = st.selectbox(
        "Selecione o tipo de análise", 
        ["Razão Social", "Estado"]
    )
    
    # Encontra os estados com maiores valores para mostrar na sidebar
    top_estado_num = df_estado.loc[df_estado['numero_seguros'].idxmax()]
    top_estado_area = df_estado.loc[df_estado['area_total'].idxmax()]
    top_estado_valor = df_estado.loc[df_estado['valor_total'].idxmax()]
    
    # Exibe os destaques formatados
    st.markdown(f"""
    **Destaques por Estado:**
    - 🏆 Maior nº apólices: {top_estado_num['SG_UF_PROPRIEDADE']} ({top_estado_num['numero_seguros']})
    - 📏 Maior área: {top_estado_area['SG_UF_PROPRIEDADE']} ({top_estado_area['area_total']:,.2f} ha)
    - 💰 Maior valor: {top_estado_valor['SG_UF_PROPRIEDADE']} (R$ {top_estado_valor['valor_total']:,.2f})
    """)

# Título principal do dashboard
st.title("Análise de Seguros Agrícolas - SISSER")

# Subtítulo com markdown
st.markdown("""
**Sistema de Subvenção Econômica ao Prêmio do Seguro Rural**  
*Dados atualizados em 2023*
""")

# Linha divisória
st.divider()

# ==============================================
# 5. VISUALIZAÇÕES PRINCIPAIS
# ==============================================

# --------------------------
# 5.1 MAPA INTERATIVO
# --------------------------
st.header("Distribuição Geográfica")

# Bloco try-except para tratamento elegante de erros
try:
    # Define qual coluna usar no hover (tooltip)
    hover_col = 'NM_UF' if 'NM_UF' in gdf_merged.columns else 'SIGLA_UF'
    
    # Cria mapa coroplético com Plotly Express
    fig_map = px.choropleth(
        gdf_merged,  # Dados
        geojson=gdf_merged.geometry,  # Geometrias dos polígonos
        locations=gdf_merged.index,  # Índice como referência
        color='numero_seguros',  # Variável para coloração
        hover_name=hover_col,  # Dado mostrado em destaque
        hover_data=['area_total', 'valor_total'],  # Dados adicionais no tooltip
        color_continuous_scale="Blues",  # Escala de cores
        projection="mercator",  # Projeção cartográfica
        title="Número de Apólices por Estado"
    )
    
    # Ajustes de visualização do mapa
    fig_map.update_geos(
        fitbounds="locations",  # Ajusta zoom para caber todos os estados
        visible=False  # Oculta linhas de grade/contorno
    )
    
    # Remove margens para melhor aproveitamento de espaço
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    
    # Personaliza o texto do tooltip
    fig_map.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>"  # Nome do estado em negrito
                     "Apólices: %{z}<br>"  # Número de apólices
                     "Área: %{customdata[0]:,.2f} ha<br>"  # Área formatada
                     "Valor: R$ %{customdata[1]:,.2f}"  # Valor formatado
    )
    
    # Exibe o mapa no dashboard
    st.plotly_chart(fig_map, use_container_width=True)  # Ocupa toda largura
    
except Exception as e:
    # Se ocorrer erro, mostra mensagem e informações para debug
    st.error(f"Erro ao gerar o mapa: {str(e)}")
    st.write("Dados disponíveis para mapeamento:", gdf_merged.columns.tolist())

# Linha divisória
st.divider()

# --------------------------
# 5.2 ANÁLISE POR RAZÃO SOCIAL OU ESTADO
# --------------------------
if analise_tipo == "Razão Social":
    st.header("Análise por Razão Social")
    
    # Dicionário de opções de métricas
    metric_options = {
        'Número de Seguros': 'numero_seguros',
        'Contagem de Estados': 'contagem_estados',
        'Área Total': 'area_total',
        'Valor Total': 'valor_total'
    }
    
    # Dropdown para selecionar métrica
    selected_metric = st.selectbox(
        "Selecione a Métrica", 
        options=list(metric_options.keys())
    )
    
    # Obtém a coluna correspondente à métrica selecionada
    metric_column = metric_options[selected_metric]
    
    # Ordena os dados pela métrica selecionada
    df_sorted = df_razao_social.sort_values(by=metric_column, ascending=False)
    
    # Cria gráfico de barras
    fig_bar = px.bar(
        df_sorted,  # Dados ordenados
        x='NM_RAZAO_SOCIAL',  # Eixo X: razão social
        y=metric_column,  # Eixo Y: métrica selecionada
        title=f'{selected_metric} por Razão Social',  # Título dinâmico
        labels={
            'NM_RAZAO_SOCIAL': 'Razão Social', 
            metric_column: selected_metric
        }  # Rótulos personalizados
    )
    
    # Exibe o gráfico
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Seção de métricas resumidas
    st.subheader("Principais Indicadores")
    
    # Cria 4 colunas para exibir os cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Empresas", len(df_razao_social))
    
    with col2:
        st.metric("Total Apólices", df_razao_social['numero_seguros'].sum())
    
    with col3:
        st.metric("Área Total (ha)", f"{df_razao_social['area_total'].sum():,.2f}")
    
    with col4:
        st.metric("Valor Total (R$)", f"{df_razao_social['valor_total'].sum():,.2f}")
    
    st.divider()

# --------------------------
# 5.3 GRÁFICO DE CORRELAÇÕES
# --------------------------
st.header("Análise de Correlações")

# Cria mapa de calor das correlações
fig_heatmap = px.imshow(
    correlation_matrix,  # Matriz de correlação
    text_auto=True,  # Mostra valores nas células
    color_continuous_scale="Blues",  # Escala de cores
    title="Correlação entre Variáveis",  # Título
    width=800,  # Largura
    height=600  # Altura
)

# Exibe o gráfico
st.plotly_chart(fig_heatmap, use_container_width=True)

# Texto explicativo
st.markdown("""
**Interpretação:**
- Valores próximos a **1** indicam forte correlação positiva
- Valores próximos a **-1** indicam forte correlação negativa
- Valores próximos a **0** indicam pouca ou nenhuma correlação
""")

st.divider()

# --------------------------
# 5.4 DISTRIBUIÇÃO DE VALORES (ABAS)
# --------------------------
st.header("Distribuição de Valores")

# Cria abas para diferentes visualizações
tab1, tab2, tab3 = st.tabs(["Área Total", "Valor Total", "Apólices por Estado"])

with tab1:  # Conteúdo da primeira aba
    fig_area = px.pie(
        df_razao_social,
        names='NM_RAZAO_SOCIAL',  # Nomes das fatias
        values='area_total',  # Valores das fatias
        title='Distribuição da Área Total por Empresa'
    )
    st.plotly_chart(fig_area, use_container_width=True)

with tab2:  # Conteúdo da segunda aba
    fig_valor = px.pie(
        df_razao_social,
        names='NM_RAZAO_SOCIAL',
        values='valor_total',
        title='Distribuição do Valor Total por Empresa'
    )
    st.plotly_chart(fig_valor, use_container_width=True)

with tab3:  # Conteúdo da terceira aba
    fig_estado = px.bar(
        df_estado.sort_values('numero_seguros', ascending=False),
        x='SG_UF_PROPRIEDADE',  # Estados no eixo X
        y='numero_seguros',  # Número de apólices no eixo Y
        title='Número de Apólices por Estado'
    )
    st.plotly_chart(fig_estado, use_container_width=True)

# ==============================================
# 6. RODAPÉ E INFORMAÇÕES ADICIONAIS
# ==============================================
st.divider()

# Informações de rodapé
st.markdown("""
**Fonte dos dados:** [SISSER](https://dados.gov.br/dados/conjuntos-dados/sisser-sistema-de-subvencao-economica-ao-premio-do-seguro-rural)  
**Última atualização:** 2023  
**Desenvolvido por:** Sérgio Serra Silva  
""")