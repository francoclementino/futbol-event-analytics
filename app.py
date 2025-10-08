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
import io
from datetime import datetime, date

# IMPORT CONDICIONAL
try:
    from mplsoccer import Pitch
    import matplotlib.pyplot as plt
    MPLSOCCER_AVAILABLE = True
except ImportError:
    MPLSOCCER_AVAILABLE = False

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURACIÓN Y CACHÉ OPTIMIZADO
# ============================================================================

@st.cache_data(ttl=3600, show_spinner=True, max_entries=2)
def cargar_archivo_subido(archivo_bytes, nombre_archivo: str):
    """Carga archivo parquet desde bytes subidos"""
    try:
        df = pd.read_parquet(io.BytesIO(archivo_bytes))
        
        # Optimizar tipos de datos
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = df[col].astype('float32')
        
        for col in df.select_dtypes(include=['int64']).columns:
            if df[col].max() < 32767 and df[col].min() > -32768:
                df[col] = df[col].astype('int16')
        
        # Convertir match_date a datetime si existe
        if 'match_date' in df.columns:
            df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_lista_jugadores(df: pd.DataFrame) -> List[str]:
    """Obtiene lista única de jugadores"""
    col_player = 'playerName' if 'playerName' in df.columns else 'player_name'
    if col_player not in df.columns:
        return []
    return sorted(df[col_player].dropna().unique().tolist())

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_lista_equipos(df: pd.DataFrame) -> List[str]:
    """Obtiene lista única de equipos"""
    col_team = 'teamName' if 'teamName' in df.columns else 'team_name'
    if col_team not in df.columns:
        return []
    return sorted(df[col_team].dropna().unique().tolist())

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_info_partidos(df: pd.DataFrame) -> Dict[str, dict]:
    """Obtiene información completa de partidos con nombres legibles"""
    partidos = {}
    col_team = 'teamName' if 'teamName' in df.columns else 'team_name'
    
    for match_id in df['match_id'].unique():
        match_data = df[df['match_id'] == match_id]
        
        # Obtener equipos del partido
        equipos = match_data[col_team].unique()
        
        if len(equipos) >= 2:
            partido_nombre = f"{equipos[0]} vs {equipos[1]}"
        elif len(equipos) == 1:
            partido_nombre = f"{equipos[0]}"
        else:
            partido_nombre = f"Partido {match_id}"
        
        # Agregar fecha si está disponible
        fecha_obj = None
        if 'match_date' in match_data.columns:
            fecha = match_data['match_date'].iloc[0]
            if pd.notna(fecha):
                if isinstance(fecha, str):
                    try:
                        fecha_obj = pd.to_datetime(fecha)
                        partido_nombre = f"{fecha_obj.strftime('%Y-%m-%d')} - {partido_nombre}"
                    except:
                        pass
                else:
                    fecha_obj = fecha
                    partido_nombre = f"{fecha_obj.strftime('%Y-%m-%d')} - {partido_nombre}"
        
        # Agregar stage si está disponible
        stage = 'Unknown'
        if 'stage_name' in match_data.columns:
            stage = match_data['stage_name'].iloc[0]
            if pd.notna(stage) and stage != 'Unknown':
                partido_nombre = f"{partido_nombre} ({stage})"
        
        partidos[partido_nombre] = {
            'match_id': match_id,
            'equipos': list(equipos),
            'fecha': fecha_obj,
            'stage': stage
        }
    
    return partidos

# ============================================================================
# FUNCIONES DE VISUALIZACIÓN
# ============================================================================

def visualizar_eventos_campo_optimizado(eventos_df: pd.DataFrame, titulo: str, 
                                        max_eventos: int = 300):
    """Visualiza eventos en el campo con límite para performance"""
    if not MPLSOCCER_AVAILABLE:
        st.warning("⚠️ La visualización de campo requiere mplsoccer. Mostrando datos en tabla:")
        col_type = 'type' if 'type' in eventos_df.columns else 'type_name'
        cols_mostrar = [col_type, 'x', 'y']
        if 'outcome' in eventos_df.columns:
            cols_mostrar.append('outcome')
        st.dataframe(eventos_df[cols_mostrar].head(50))
        return None
    
    from mplsoccer import Pitch
    import matplotlib.pyplot as plt
    
    # Limitar número de eventos para performance
    if len(eventos_df) > max_eventos:
        st.caption(f"⚠️ Mostrando {max_eventos} de {len(eventos_df)} eventos para mejor rendimiento")
        eventos_df = eventos_df.sample(n=max_eventos, random_state=42)
    
    pitch = Pitch(pitch_type='opta', pitch_color='#22312b', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(10, 7))
    
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
        s=80,
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
# PÁGINA DE CARGA DE ARCHIVOS - SIMPLIFICADA
# ============================================================================

def pagina_cargar_archivos():
    """Página para subir archivos parquet - SIMPLIFICADA"""
    st.title("📁 Cargar Archivo de Eventos")
    st.markdown("---")
    
    st.info("""
    ### 📤 Sube un archivo Parquet con datos de eventos
    
    **Formato aceptado:** `.parquet`
    
    Una vez cargado, irás directamente a las visualizaciones.
    """)
    
    # Selector de archivo - SOLO UNO
    uploaded_file = st.file_uploader(
        "Selecciona archivo Parquet:",
        type=['parquet'],
        accept_multiple_files=False,
        key='file_uploader',
        help="Selecciona un archivo .parquet para analizar"
    )
    
    if uploaded_file:
        st.success(f"✅ Archivo cargado: {uploaded_file.name} ({uploaded_file.size / (1024*1024):.2f} MB)")
        
        # Cargar automáticamente
        with st.spinner("⏳ Cargando datos..."):
            file_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            
            df = pd.read_parquet(io.BytesIO(file_bytes))
            
            # Guardar en session state
            st.session_state['archivo_actual_bytes'] = file_bytes
            st.session_state['archivo_actual_nombre'] = uploaded_file.name
            st.session_state['archivo_cargado'] = True
            
            # Mostrar info rápida
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Eventos", f"{len(df):,}")
            with col2:
                col_player = 'playerName' if 'playerName' in df.columns else 'player_name'
                if col_player in df.columns:
                    st.metric("👤 Jugadores", f"{df[col_player].nunique():,}")
            with col3:
                if 'match_id' in df.columns:
                    st.metric("🎮 Partidos", f"{df['match_id'].nunique():,}")
            
            st.success("✅ Redirigiendo a visualizaciones...")
            st.rerun()

# ============================================================================
# FILTROS GLOBALES
# ============================================================================

def aplicar_filtros_globales(df):
    """Aplica filtros de Stage y Fecha al DataFrame"""
    
    st.sidebar.header("🔍 Filtros Globales")
    
    df_filtrado = df.copy()
    
    # FILTRO DE STAGE
    if 'stage_name' in df.columns:
        stages_disponibles = sorted(df['stage_name'].dropna().unique().tolist())
        
        if len(stages_disponibles) > 1:
            st.sidebar.subheader("📅 Stage / Fase")
            
            # Opción de selección múltiple
            stages_seleccionados = st.sidebar.multiselect(
                "Selecciona stage(s):",
                options=stages_disponibles,
                default=stages_disponibles,  # Por defecto, todos seleccionados
                key='filtro_stages'
            )
            
            if stages_seleccionados:
                df_filtrado = df_filtrado[df_filtrado['stage_name'].isin(stages_seleccionados)]
            else:
                st.sidebar.warning("⚠️ No hay stages seleccionados")
                return None
            
            # Mostrar info de stages seleccionados
            st.sidebar.caption(f"✅ {len(stages_seleccionados)} stage(s) seleccionado(s)")
    
    # FILTRO DE FECHA
    if 'match_date' in df_filtrado.columns:
        st.sidebar.subheader("📆 Rango de Fechas")
        
        # Obtener fechas mínima y máxima
        fechas_validas = df_filtrado['match_date'].dropna()
        
        if len(fechas_validas) > 0:
            fecha_min = fechas_validas.min()
            fecha_max = fechas_validas.max()
            
            # Convertir a date para el widget
            if isinstance(fecha_min, pd.Timestamp):
                fecha_min = fecha_min.date()
            if isinstance(fecha_max, pd.Timestamp):
                fecha_max = fecha_max.date()
            
            # Selector de rango de fechas
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                fecha_desde = st.date_input(
                    "Desde:",
                    value=fecha_min,
                    min_value=fecha_min,
                    max_value=fecha_max,
                    key='fecha_desde'
                )
            
            with col2:
                fecha_hasta = st.date_input(
                    "Hasta:",
                    value=fecha_max,
                    min_value=fecha_min,
                    max_value=fecha_max,
                    key='fecha_hasta'
                )
            
            # Aplicar filtro de fechas
            df_filtrado['match_date_only'] = pd.to_datetime(df_filtrado['match_date']).dt.date
            df_filtrado = df_filtrado[
                (df_filtrado['match_date_only'] >= fecha_desde) &
                (df_filtrado['match_date_only'] <= fecha_hasta)
            ]
            df_filtrado = df_filtrado.drop('match_date_only', axis=1)
            
            # Mostrar info
            partidos_en_rango = df_filtrado['match_id'].nunique() if 'match_id' in df_filtrado.columns else 0
            st.sidebar.caption(f"✅ {partidos_en_rango} partidos en el rango")
    
    st.sidebar.markdown("---")
    
    # Mostrar resumen de datos filtrados
    st.sidebar.subheader("📊 Datos Filtrados")
    st.sidebar.metric("Eventos", f"{len(df_filtrado):,}")
    
    if 'match_id' in df_filtrado.columns:
        st.sidebar.metric("Partidos", f"{df_filtrado['match_id'].nunique():,}")
    
    col_player = 'playerName' if 'playerName' in df_filtrado.columns else 'player_name'
    if col_player in df_filtrado.columns:
        st.sidebar.metric("Jugadores", f"{df_filtrado[col_player].nunique():,}")
    
    return df_filtrado

# ============================================================================
# PÁGINAS DE ANÁLISIS
# ============================================================================

def pagina_metricas_jugadores(df):
    """Página de métricas de jugadores"""
    st.title("📈 Métricas de Jugadores")
    st.markdown("---")
    
    # Normalizar nombres de columnas
    col_player = 'playerName' if 'playerName' in df.columns else 'player_name'
    col_team = 'teamName' if 'teamName' in df.columns else 'team_name'
    col_type = 'type' if 'type' in df.columns else 'type_name'
    
    if col_player not in df.columns:
        st.error("❌ El archivo no contiene información de jugadores")
        return
    
    # Filtro de equipo
    st.subheader("🔍 Filtros")
    col1, col2 = st.columns(2)
    
    with col1:
        equipos = ['Todos'] + obtener_lista_equipos(df)
        equipo_sel = st.selectbox(
            "Equipo:",
            options=equipos,
            index=0,
            key='equipo_metricas'
        )
        
        if equipo_sel != 'Todos':
            df = df[df[col_team] == equipo_sel].copy()
    
    with col2:
        # Selector de jugador
        jugadores = obtener_lista_jugadores(df)
        
        if not jugadores:
            st.warning("⚠️ No hay jugadores disponibles")
            return
        
        jugador_sel = st.selectbox(
            "Jugador:",
            options=jugadores,
            index=0,
            key='jugador_sel_metricas'
        )
    
    # Filtrar eventos del jugador
    df_jugador = df[df[col_player] == jugador_sel].copy()
    
    if len(df_jugador) == 0:
        st.warning(f"⚠️ No hay eventos para {jugador_sel}")
        return
    
    # Mostrar métricas
    st.markdown("---")
    st.subheader(f"📊 Estadísticas de {jugador_sel}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'match_id' in df_jugador.columns:
            st.metric("Partidos", df_jugador['match_id'].nunique())
    
    with col2:
        st.metric("Total Eventos", len(df_jugador))
    
    with col3:
        if 'outcome' in df_jugador.columns:
            eventos_con_outcome = df_jugador['outcome'].notna().sum()
            if eventos_con_outcome > 0:
                tasa_exito = (df_jugador['outcome'] == 1).sum() / eventos_con_outcome * 100
                st.metric("Tasa de Éxito", f"{tasa_exito:.1f}%")
    
    with col4:
        if 'match_id' in df_jugador.columns:
            eventos_por_partido = len(df_jugador) / df_jugador['match_id'].nunique()
            st.metric("Eventos/Partido", f"{eventos_por_partido:.1f}")
    
    # Distribución de eventos
    st.markdown("---")
    st.subheader("📊 Distribución de Eventos")
    
    event_counts = df_jugador[col_type].value_counts()
    
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
    if 'x' in df_jugador.columns and 'y' in df_jugador.columns:
        st.markdown("---")
        st.subheader("🗺️ Mapa de Eventos")
        
        tipo_evento_filtro = st.selectbox(
            "Filtrar por tipo de evento:",
            options=['Todos'] + sorted(df_jugador[col_type].unique().tolist()),
            index=0,
            key='tipo_evento_mapa'
        )
        
        if tipo_evento_filtro != 'Todos':
            df_visualizar = df_jugador[df_jugador[col_type] == tipo_evento_filtro].copy()
        else:
            df_visualizar = df_jugador.copy()
        
        if len(df_visualizar) > 0:
            if MPLSOCCER_AVAILABLE:
                fig_campo = visualizar_eventos_campo_optimizado(
                    df_visualizar,
                    f"{jugador_sel} - {tipo_evento_filtro}"
                )
                if fig_campo:
                    st.pyplot(fig_campo)
                    plt.close()
            else:
                st.info("📊 Visualización de campo no disponible. Mostrando tabla:")
                cols_mostrar = [col_type, 'x', 'y']
                if 'outcome' in df_visualizar.columns:
                    cols_mostrar.append('outcome')
                st.dataframe(df_visualizar[cols_mostrar].head(100))


def pagina_analisis_eventos(df):
    """Página de análisis de eventos"""
    st.title("🎯 Análisis de Eventos")
    st.markdown("---")
    
    # Normalizar nombres de columnas
    col_player = 'playerName' if 'playerName' in df.columns else 'player_name'
    col_team = 'teamName' if 'teamName' in df.columns else 'team_name'
    col_type = 'type' if 'type' in df.columns else 'type_name'
    
    if 'match_id' not in df.columns:
        st.error("❌ El archivo no contiene la columna 'match_id'")
        return
    
    # Selector de partido
    st.subheader("1️⃣ Seleccionar Partido")
    
    partidos_info = obtener_info_partidos(df)
    
    if not partidos_info:
        st.warning("⚠️ No hay partidos disponibles")
        return
    
    partido_sel = st.selectbox(
        "Selecciona un partido:",
        options=list(partidos_info.keys()),
        index=0,
        key='partido_analisis'
    )
    
    match_id = partidos_info[partido_sel]['match_id']
    df_partido = df[df['match_id'] == match_id].copy()
    
    # Información del partido
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Eventos", len(df_partido))
    
    with col2:
        st.metric("Jugadores", df_partido[col_player].nunique())
    
    with col3:
        st.metric("Equipos", df_partido[col_team].nunique())
    
    # Análisis por equipo
    st.markdown("---")
    st.subheader("📊 Análisis por Equipo")
    
    equipos = df_partido[col_team].unique()
    
    if len(equipos) >= 2:
        col1, col2 = st.columns(2)
        
        for i, equipo in enumerate(equipos[:2]):
            df_equipo = df_partido[df_partido[col_team] == equipo]
            
            with col1 if i == 0 else col2:
                st.markdown(f"### {equipo}")
                
                event_counts = df_equipo[col_type].value_counts().head(10)
                
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


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal"""
    
    # Configuración de la página
    st.set_page_config(
        page_title="WyScout Analytics",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded"
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
    
    # Inicializar session state
    if 'archivo_cargado' not in st.session_state:
        st.session_state['archivo_cargado'] = False
    
    # Si NO hay archivo cargado, mostrar página de carga
    if not st.session_state['archivo_cargado']:
        pagina_cargar_archivos()
        return
    
    # Si HAY archivo cargado, mostrar análisis
    if 'archivo_actual_bytes' in st.session_state:
        
        # Cargar datos
        df = cargar_archivo_subido(
            st.session_state['archivo_actual_bytes'],
            st.session_state['archivo_actual_nombre']
        )
        
        if df is None:
            st.error("❌ Error al cargar el archivo")
            if st.button("⬅️ Volver"):
                st.session_state['archivo_cargado'] = False
                st.rerun()
            return
        
        # Título principal
        st.title("⚽ WyScout Analytics Dashboard")
        
        # Botón para cambiar archivo
        col1, col2 = st.columns([5, 1])
        with col2:
            if st.button("📁 Cambiar Archivo", use_container_width=True):
                st.session_state['archivo_cargado'] = False
                st.cache_data.clear()
                st.rerun()
        
        st.caption(f"📄 {st.session_state.get('archivo_actual_nombre', 'archivo')}")
        st.markdown("---")
        
        # APLICAR FILTROS GLOBALES
        df_filtrado = aplicar_filtros_globales(df)
        
        if df_filtrado is None or len(df_filtrado) == 0:
            st.warning("⚠️ No hay datos con los filtros seleccionados")
            return
        
        # Pestañas de análisis
        tab1, tab2, tab3 = st.tabs([
            "📈 Métricas de Jugadores", 
            "🎯 Análisis de Eventos",
            "⚡ Expected Threat (xT)"
        ])
        
        with tab1:
            try:
                pagina_metricas_jugadores(df_filtrado)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
        
        with tab2:
            try:
                pagina_analisis_eventos(df_filtrado)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
        
        with tab3:
            pagina_expected_threat()


if __name__ == "__main__":
    main()