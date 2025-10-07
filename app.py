import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path
import warnings
from typing import List, Dict, Tuple
from mplsoccer import Pitch
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURACIÓN Y CACHÉ OPTIMIZADO
# ============================================================================

@st.cache_data(ttl=3600, show_spinner=True, max_entries=2)  # Reducir a 2 entradas máximo
def cargar_eventos_optimizado(ruta: str, columnas_necesarias: List[str] = None):
    """
    Carga eventos de forma optimizada para grandes datasets
    """
    try:
        if columnas_necesarias:
            df = pd.read_parquet(ruta, columns=columnas_necesarias)
        else:
            df = pd.read_parquet(ruta)
        
        # Optimizar tipos de datos
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = df[col].astype('float32')
        
        for col in df.select_dtypes(include=['int64']).columns:
            if df[col].max() < 32767 and df[col].min() > -32768:
                df[col] = df[col].astype('int16')
        
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_lista_jugadores(df: pd.DataFrame) -> List[str]:
    """Obtiene lista única de jugadores de forma eficiente"""
    return sorted(df['player_name'].dropna().unique().tolist())

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_lista_equipos(df: pd.DataFrame) -> List[str]:
    """Obtiene lista única de equipos"""
    return sorted(df['team_name'].dropna().unique().tolist())

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_lista_partidos(df: pd.DataFrame) -> Dict[str, str]:
    """Obtiene lista de partidos con información legible"""
    partidos = {}
    for match_id in df['match_id'].unique():
        match_data = df[df['match_id'] == match_id].iloc[0]
        label = f"{match_data.get('competition', 'Unknown')} - {match_data.get('date', 'Unknown')}"
        partidos[label] = match_id
    return partidos

# ============================================================================
# FUNCIONES DE VISUALIZACIÓN
# ============================================================================

def visualizar_eventos_campo_optimizado(eventos_df: pd.DataFrame, titulo: str, 
                                        max_eventos: int = 300):  # Reducido a 300
    """
    Visualiza eventos en el campo con límite para performance
    """
    from mplsoccer import Pitch
    import matplotlib.pyplot as plt
    
    # Limitar número de eventos para performance
    if len(eventos_df) > max_eventos:
        st.warning(f"⚠️ Mostrando {max_eventos} de {len(eventos_df)} eventos para mejor rendimiento")
        eventos_df = eventos_df.sample(n=max_eventos, random_state=42)
    
    pitch = Pitch(pitch_type='opta', pitch_color='#22312b', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(10, 7))  # Reducido el tamaño
    
    # Filtrar eventos válidos
    eventos_validos = eventos_df[eventos_df['x'].notna() & eventos_df['y'].notna()].copy()
    
    if len(eventos_validos) == 0:
        ax.text(50, 50, 'No hay eventos con coordenadas', 
                ha='center', va='center', fontsize=14, color='white')
        plt.title(titulo, color='white', fontsize=14, pad=20)
        return fig
    
    # Colores por outcome
    color_map = {1: '#00ff85', 0: '#ff4444'}
    colors = [color_map.get(outcome, '#888888') for outcome in eventos_validos['outcome']]
    
    # Plotear eventos
    pitch.scatter(
        eventos_validos['x'], 
        eventos_validos['y'],
        s=80,  # Reducido el tamaño de los puntos
        c=colors,
        edgecolors='white',
        linewidth=0.5,
        alpha=0.7,
        ax=ax,
        zorder=2
    )
    
    plt.title(titulo, color='white', fontsize=12, pad=15)
    
    # Leyenda
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#00ff85', label='Éxito'),
        Patch(facecolor='#ff4444', label='Fallo'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', facecolor='#22312b', 
             edgecolor='white', labelcolor='white', fontsize=9)
    
    plt.tight_layout()
    return fig

# ============================================================================
# PÁGINAS DE LA APLICACIÓN
# ============================================================================

def pagina_metricas_jugadores():
    """Página de métricas de jugadores - OPTIMIZADA"""
    st.title("📈 Métricas de Jugadores")
    st.markdown("---")
    
    # CRÍTICO: Solo cargar cuando el usuario hace clic
    if 'datos_jugadores_cargados' not in st.session_state:
        st.session_state.datos_jugadores_cargados = False
    
    if not st.session_state.datos_jugadores_cargados:
        st.info("👋 Esta sección analiza el rendimiento individual de jugadores")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Haz clic en el botón para cargar los datos y comenzar el análisis")
        with col2:
            if st.button("🔄 Cargar Datos", type="primary", use_container_width=True):
                st.session_state.datos_jugadores_cargados = True
                st.rerun()
        return
    
    # Ahora sí, cargar datos
    with st.spinner("⏳ Cargando datos..."):
        columnas_metricas = [
            'player_id', 'player_name', 'team_name', 'match_id', 
            'type_name', 'outcome', 'x', 'y', 'competition', 'date'
        ]
        df = cargar_eventos_optimizado("data/processed/opta_events.parquet", columnas_metricas)
    
    if df is None:
        st.error("❌ No se pudieron cargar los datos")
        if st.button("⬅️ Volver"):
            st.session_state.datos_jugadores_cargados = False
            st.rerun()
        return
    
    st.success(f"✅ Datos cargados: {len(df):,} eventos de {df['player_name'].nunique():,} jugadores")
    
    # Botón para recargar
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Reiniciar", use_container_width=True):
            st.session_state.datos_jugadores_cargados = False
            st.cache_data.clear()
            st.rerun()
    
    # Filtros en sidebar
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de competición
    competiciones = ['Todas'] + sorted(df['competition'].unique().tolist())
    competicion_sel = st.sidebar.selectbox(
        "Competición:",
        options=competiciones,
        index=0,
        key='comp_metricas'
    )
    
    if competicion_sel != 'Todas':
        df = df[df['competition'] == competicion_sel].copy()
    
    # Filtro de equipo
    equipos = ['Todos'] + obtener_lista_equipos(df)
    equipo_sel = st.sidebar.selectbox(
        "Equipo:",
        options=equipos,
        index=0,
        key='equipo_metricas'
    )
    
    if equipo_sel != 'Todos':
        df = df[df['team_name'] == equipo_sel].copy()
    
    # Selector de jugador
    jugadores = obtener_lista_jugadores(df)
    
    if not jugadores:
        st.warning("⚠️ No hay jugadores disponibles con los filtros seleccionados")
        return
    
    jugador_sel = st.selectbox(
        "Selecciona un jugador:",
        options=jugadores,
        index=0,
        key='jugador_sel_metricas'
    )
    
    # Filtrar eventos del jugador
    df_jugador = df[df['player_name'] == jugador_sel].copy()
    
    if len(df_jugador) == 0:
        st.warning(f"⚠️ No hay eventos para {jugador_sel}")
        return
    
    # Mostrar métricas
    st.markdown("---")
    st.subheader(f"📊 Estadísticas de {jugador_sel}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Partidos", df_jugador['match_id'].nunique())
    
    with col2:
        st.metric("Total Eventos", len(df_jugador))
    
    with col3:
        eventos_con_outcome = df_jugador['outcome'].notna().sum()
        if eventos_con_outcome > 0:
            tasa_exito = (df_jugador['outcome'] == 1).sum() / eventos_con_outcome * 100
            st.metric("Tasa de Éxito", f"{tasa_exito:.1f}%")
        else:
            st.metric("Tasa de Éxito", "N/A")
    
    with col4:
        eventos_por_partido = len(df_jugador) / df_jugador['match_id'].nunique()
        st.metric("Eventos/Partido", f"{eventos_por_partido:.1f}")
    
    # Distribución de eventos
    st.markdown("---")
    st.subheader("📊 Distribución de Eventos")
    
    event_counts = df_jugador['type_name'].value_counts()
    
    fig = go.Figure(data=[
        go.Bar(
            x=event_counts.values,
            y=event_counts.index,
            orientation='h',
            marker_color='steelblue'
        )
    ])
    
    fig.update_layout(
        title="Tipos de Eventos",
        xaxis_title="Cantidad",
        yaxis_title="Tipo de Evento",
        height=400,
        template='plotly_dark'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mapa de eventos
    st.markdown("---")
    st.subheader("🗺️ Mapa de Eventos")
    
    tipo_evento_filtro = st.selectbox(
        "Filtrar por tipo de evento:",
        options=['Todos'] + sorted(df_jugador['type_name'].unique().tolist()),
        index=0,
        key='tipo_evento_mapa'
    )
    
    if tipo_evento_filtro != 'Todos':
        df_visualizar = df_jugador[df_jugador['type_name'] == tipo_evento_filtro].copy()
    else:
        df_visualizar = df_jugador.copy()
    
    if len(df_visualizar) > 0:
        fig_campo = visualizar_eventos_campo_optimizado(
            df_visualizar,
            f"{jugador_sel} - {tipo_evento_filtro}"
        )
        st.pyplot(fig_campo)
        plt.close()
    else:
        st.info("No hay eventos para visualizar con el filtro seleccionado")


def pagina_analisis_eventos():
    """Página de análisis de eventos - OPTIMIZADA"""
    st.title("🎯 Análisis de Eventos")
    st.markdown("---")
    
    # CRÍTICO: Solo cargar cuando el usuario hace clic
    if 'datos_eventos_cargados' not in st.session_state:
        st.session_state.datos_eventos_cargados = False
    
    if not st.session_state.datos_eventos_cargados:
        st.info("👋 Esta sección permite analizar eventos de partidos completos")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Haz clic en el botón para cargar los datos y comenzar el análisis")
        with col2:
            if st.button("🔄 Cargar Datos", type="primary", use_container_width=True, key='btn_eventos'):
                st.session_state.datos_eventos_cargados = True
                st.rerun()
        return
    
    with st.spinner("⏳ Cargando datos..."):
        columnas_eventos = [
            'match_id', 'competition', 'date', 'period_id',
            'type_name', 'player_name', 'team_name', 'x', 'y', 'outcome'
        ]
        df = cargar_eventos_optimizado("data/processed/opta_events.parquet", columnas_eventos)
    
    if df is None:
        st.error("❌ No se pudieron cargar los datos")
        if st.button("⬅️ Volver"):
            st.session_state.datos_eventos_cargados = False
            st.rerun()
        return
    
    st.success(f"✅ Datos cargados: {len(df):,} eventos")
    
    # Botón para reiniciar
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Reiniciar", use_container_width=True, key='reiniciar_eventos'):
            st.session_state.datos_eventos_cargados = False
            st.cache_data.clear()
            st.rerun()
    
    # Selector de partido
    st.subheader("1️⃣ Seleccionar Partido")
    
    partidos = obtener_lista_partidos(df)
    
    if not partidos:
        st.warning("⚠️ No hay partidos disponibles")
        return
    
    partido_sel = st.selectbox(
        "Selecciona un partido:",
        options=list(partidos.keys()),
        index=0,
        key='partido_analisis'
    )
    
    match_id = partidos[partido_sel]
    df_partido = df[df['match_id'] == match_id].copy()
    
    # Información del partido
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Eventos", len(df_partido))
    
    with col2:
        st.metric("Jugadores", df_partido['player_name'].nunique())
    
    with col3:
        st.metric("Equipos", df_partido['team_name'].nunique())
    
    # Análisis por equipo
    st.markdown("---")
    st.subheader("📊 Análisis por Equipo")
    
    equipos = df_partido['team_name'].unique()
    
    if len(equipos) >= 2:
        col1, col2 = st.columns(2)
        
        for i, equipo in enumerate(equipos[:2]):
            df_equipo = df_partido[df_partido['team_name'] == equipo]
            
            with col1 if i == 0 else col2:
                st.markdown(f"### {equipo}")
                
                event_counts = df_equipo['type_name'].value_counts().head(10)
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=event_counts.values,
                        y=event_counts.index,
                        orientation='h',
                        marker_color='coral' if i == 0 else 'steelblue'
                    )
                ])
                
                fig.update_layout(
                    title=f"Top 10 Eventos - {equipo}",
                    xaxis_title="Cantidad",
                    height=400,
                    template='plotly_dark'
                )
                
                st.plotly_chart(fig, use_container_width=True)


def pagina_expected_threat():
    """Página placeholder para Expected Threat"""
    st.title("⚡ Expected Threat (xT)")
    st.markdown("---")
    
    st.info("""
    🚧 **Funcionalidad en desarrollo**
    
    Esta sección incluirá:
    - Cálculo de Expected Threat por zona
    - Mapas de calor de xT
    - Análisis de progresión de balón
    - Valoración de pases y conducciones
    """)


def main():
    """Función principal - OPTIMIZADA"""
    
    # Configuración de la página
    st.set_page_config(
        page_title="WyScout Analytics",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="collapsed"  # CAMBIADO: Cerrado por defecto
    )
    
    # CSS personalizado
    st.markdown("""
        <style>
        .main {
            background-color: #0e1117;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding-left: 20px;
            padding-right: 20px;
            background-color: #1e2530;
            border-radius: 5px;
            color: white;
        }
        .stTabs [aria-selected="true"] {
            background-color: #2e3d50;
        }
        div[data-testid="stMetricValue"] {
            font-size: 24px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Título principal
    st.title("⚽ WyScout Analytics Dashboard")
    st.caption("Análisis avanzado de eventos de fútbol")
    st.markdown("---")
    
    # Pestañas
    tab1, tab2, tab3 = st.tabs([
        "📈 Métricas de Jugadores", 
        "🎯 Análisis de Eventos",
        "⚡ Expected Threat (xT)"
    ])
    
    with tab1:
        try:
            pagina_metricas_jugadores()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            if st.button("🔄 Reintentar"):
                st.session_state.datos_jugadores_cargados = False
                st.rerun()
    
    with tab2:
        try:
            pagina_analisis_eventos()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            if st.button("🔄 Reintentar", key='retry_eventos'):
                st.session_state.datos_eventos_cargados = False
                st.rerun()
    
    with tab3:
        pagina_expected_threat()


if __name__ == "__main__":
    main()