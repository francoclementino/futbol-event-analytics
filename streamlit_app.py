# streamlit_app.py
# Versión: 1.2 - Sistema de análisis de fútbol con OPTA F24 (actualizado)
import streamlit as st
import sys
from pathlib import Path

# Agregar carpeta Codigos al path
sys.path.insert(0, str(Path(__file__).parent / 'Codigos'))

# Configuración de página (debe ser lo primero)
st.set_page_config(
    page_title="Football Analytics Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar módulos de pestañas
from passing_network_tab import show_passing_network_tab

def main():
    """Aplicación principal de Streamlit"""
    
    # Header principal
    st.title("⚽ Football Analytics Dashboard")
    st.markdown("**Análisis avanzado de datos de fútbol con OPTA F24**")
    
    # Sidebar con información
    with st.sidebar:
        st.header("📊 Sistema de Análisis")
        st.markdown("---")
        
        # Info del proyecto
        st.subheader("ℹ️ Información")
        st.markdown("""
        **Capacidades:**
        - 🕸️ Redes de pases
        - 📈 Expected Threat (xT)
        - 🎯 Análisis de tiros
        - 🏃 Detección de carries
        - 📊 Estadísticas avanzadas
        """)
        
        st.markdown("---")
        
        # Verificar carpeta de datos
        data_dir = Path("data")
        if data_dir.exists():
            json_files = list(data_dir.glob("*f24*.json")) + list(data_dir.glob("*F24*.json"))
            st.success(f"✅ {len(json_files)} archivos F24 disponibles")
        else:
            st.error("❌ No se encuentra carpeta 'data'")
            st.info("💡 Crea una carpeta 'data' y coloca tus archivos F24 JSON")
        
        st.markdown("---")
        st.caption("Powered by OPTA Data & Streamlit")
    
    # Crear pestañas principales
    tabs = st.tabs([
        "🕸️ Passing Network",
        "📊 Match Stats",
        "📈 xT Analysis",
        "🎯 Shot Analysis",
        "🏃 Carry Analysis"
    ])
    
    # Pestaña 1: Passing Network
    with tabs[0]:
        show_passing_network_tab()
    
    # Pestaña 2: Match Stats (placeholder)
    with tabs[1]:
        st.header("📊 Match Statistics")
        st.info("🚧 Esta sección estará disponible próximamente")
        st.markdown("""
        **Funcionalidades planeadas:**
        - Comparación de estadísticas entre equipos
        - Gráficos de posesión por zona
        - Métricas de presión
        - Análisis de transiciones
        """)
    
    # Pestaña 3: xT Analysis (placeholder)
    with tabs[2]:
        st.header("📈 Expected Threat Analysis")
        st.info("🚧 Esta sección estará disponible próximamente")
        st.markdown("""
        **Funcionalidades planeadas:**
        - Mapa de calor de xT
        - Jugadores con mayor xT
        - Análisis de progresión de balón
        - Zonas de peligro
        """)
    
    # Pestaña 4: Shot Analysis (placeholder)
    with tabs[3]:
        st.header("🎯 Shot Analysis")
        st.info("🚧 Esta sección estará disponible próximamente")
        st.markdown("""
        **Funcionalidades planeadas:**
        - Mapa de tiros (Shot map)
        - xG por jugador
        - Análisis de finalizaciones
        - Comparación de porteros
        """)
    
    # Pestaña 5: Carry Analysis (placeholder)
    with tabs[4]:
        st.header("🏃 Carry Analysis")
        st.info("🚧 Esta sección estará disponible próximamente")
        st.markdown("""
        **Funcionalidades planeadas:**
        - Mapa de carries
        - Distancias recorridas con balón
        - Carries progresivos
        - Jugadores más dinámicos
        """)
    
    # Footer
    st.markdown("---")
    st.caption("💡 Selecciona un archivo F24 JSON en cada pestaña para comenzar el análisis")

if __name__ == "__main__":
    main()

# Última actualización: Enero 2025 - Corrección de imports
