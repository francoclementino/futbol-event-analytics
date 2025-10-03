# =============================================================================
# 1. IMPORTS
# =============================================================================
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# =============================================================================
# 2. CONFIGURACIÓN INICIAL
# =============================================================================
st.set_page_config(
    page_title="⚽ Football Event Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚽ Football Event Analytics Dashboard")

# =============================================================================
# 3. FUNCIONES AUXILIARES
# =============================================================================

def load_data(uploaded_file):
    """Carga datos desde archivo parquet"""
    try:
        return pd.read_parquet(uploaded_file)
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return pd.DataFrame()

def apply_filters(df, selected_team, selected_event, selected_players):
    """Filtra el DataFrame por equipo, evento y jugadores"""
    if not df.empty:
        if selected_team and selected_team != "Todos los equipos" and "teamId" in df.columns:
            df = df[df["teamId"] == selected_team]

        if selected_event and selected_event != "Todos los eventos" and "eventName" in df.columns:
            df = df[df["eventName"] == selected_event]

        if selected_players and "Todos los jugadores" not in selected_players and "playerName" in df.columns:
            df = df[df["playerName"].isin(selected_players)]
    return df

# =============================================================================
# 4. SIDEBAR - FILTROS
# =============================================================================
st.sidebar.header("⚙️ Configuración y Filtros")

uploaded_file = st.sidebar.file_uploader("📂 Cargar archivo de eventos (.parquet)", type=["parquet"])

selected_team = None
selected_event = None
selected_players = None

df = pd.DataFrame()

if uploaded_file is not None:
    df = load_data(uploaded_file)

    if not df.empty:
        # Filtro equipos
        teams = ["Todos los equipos"] + sorted(df["teamId"].dropna().unique().tolist()) if "teamId" in df.columns else []
        selected_team = st.sidebar.selectbox("🏳️ Equipo", teams)

        # Filtro eventos
        events = ["Todos los eventos"] + sorted(df["eventName"].dropna().unique().tolist()) if "eventName" in df.columns else []
        selected_event = st.sidebar.selectbox("📌 Evento", events)

        # Filtro jugadores
        players = ["Todos los jugadores"] + sorted(df["playerName"].dropna().unique().tolist()) if "playerName" in df.columns else []
        selected_players = st.sidebar.multiselect("🧑‍🤝‍🧑 Jugadores", players, default=["Todos los jugadores"])

        # Aplicar filtros
        df = apply_filters(df, selected_team, selected_event, selected_players)

# =============================================================================
# 5. VISUALIZACIONES PRINCIPALES
# =============================================================================
if not df.empty:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Vista General",
        "📈 Carries",
        "🎯 Expected Threat",
        "📦 Packing Zones",
        "🔍 Análisis Avanzado"
    ])

    with tab1:
        st.header("📊 Vista General de Eventos")
        st.write(f"Total de eventos: {len(df)}")
        st.dataframe(df.head(10))

        if "eventName" in df.columns:
            st.subheader("Distribución de Eventos")
            fig, ax = plt.subplots(figsize=(8, 4))
            df["eventName"].value_counts().plot(kind="bar", ax=ax)
            st.pyplot(fig)

    with tab2:
        st.header("📈 Análisis de Carries")
        if {"x", "y", "end_x", "end_y"}.issubset(df.columns):
            fig, ax = plt.subplots(figsize=(7, 5))
            sns.scatterplot(data=df, x="x", y="y", ax=ax, label="Inicio")
            sns.scatterplot(data=df, x="end_x", y="end_y", ax=ax, label="Fin")
            st.pyplot(fig)
        else:
            st.info("No hay columnas suficientes para analizar carries.")

    with tab3:
        st.header("🎯 Expected Threat (xT)")
        if "xt_value" in df.columns:
            st.metric("Promedio xT", round(df["xt_value"].mean(), 4))
            st.metric("Eventos con xT > 0", (df["xt_value"] > 0).sum())
            fig, ax = plt.subplots(figsize=(7, 4))
            sns.histplot(df["xt_value"], bins=30, kde=True, ax=ax)
            st.pyplot(fig)
        else:
            st.info("No se detectó la columna 'xt_value'.")

    with tab4:
        st.header("📦 Packing Zones")
        if {"x", "y"}.issubset(df.columns):
            fig, ax = plt.subplots(figsize=(7, 5))
            sns.kdeplot(data=df, x="x", y="y", fill=True, alpha=0.4, ax=ax)
            st.pyplot(fig)
        else:
            st.info("No hay columnas suficientes para mostrar packing zones.")

    with tab5:
        st.header("🔍 Análisis Avanzado")
        if "possession_id" in df.columns:
            st.subheader("🔄 Posesiones y Carries")
            possession_stats = df.groupby(["possession_id", "possession_team"]).agg({
                "type": "count",
                "xt_value": "sum"
            }).reset_index()
            st.dataframe(possession_stats.head(10))
        else:
            st.info("No se detectó columna de 'possession_id'.")

# =============================================================================
# 6. DEBUG INFO
# =============================================================================
st.markdown("---")

if not df.empty:
    with st.expander("🔍 Información de Debug del Archivo"):
        st.write("**Columnas clave detectadas:**")
        important_cols = [col for col in df.columns if col in [
            "x", "y", "end_x", "end_y", "type", "eventName",
            "playerName", "teamId", "outcomeType", "xt_value",
            "carry_distance", "accurate"
        ]]
        st.code(important_cols)

        st.write("**Muestra de datos (5 filas):**")
        display_cols = ["x", "y", "eventName", "playerName", "accurate", "xt_value", "carry_distance"]
        available_cols = [col for col in display_cols if col in df.columns]
        st.dataframe(df[available_cols].head())

        st.write("**Estadísticas de columnas clave:**")
        col1, col2 = st.columns(2)

        with col1:
            if "accurate" in df.columns:
                st.write("Distribución accurate:", df["accurate"].value_counts().to_dict())
            if "outcomeType" in df.columns:
                st.write("Distribución outcomeType:", df["outcomeType"].value_counts().to_dict())

        with col2:
            if "xt_value" in df.columns:
                xt_stats = df["xt_value"].describe()
                st.write("Estadísticas xT:")
                st.write(f"Min: {xt_stats['min']:.4f}, Max: {xt_stats['max']:.4f}")
                st.write(f"Media: {xt_stats['mean']:.4f}, No-cero: {(df['xt_value'] != 0).sum()}")

# =============================================================================
# 7. FOOTER
# =============================================================================
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px; padding: 20px;'>
    <p>⚽ <strong>Sistema Especializado para Datos Opta</strong></p>
    <p>Expected Threat • Análisis de Conducciones • Métricas Avanzadas</p>
</div>
""", unsafe_allow_html=True)
