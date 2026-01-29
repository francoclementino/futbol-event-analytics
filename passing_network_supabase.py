"""
Versión de passing_network_tab.py que usa SUPABASE en lugar de archivos locales
Reemplaza la función show_passing_network_tab() con esta versión
"""

import streamlit as st
from supabase import create_client
import tempfile
from pathlib import Path
import json

def show_passing_network_tab_supabase():
    """Muestra la pestaña de análisis usando Supabase como backend"""
    
    st.markdown("### 🕸️ Passing Network Analysis")
    st.markdown("**Comparación lado a lado de ambos equipos**")
    
    # Conectar a Supabase
    try:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error("❌ Error conectando a Supabase")
        st.info("💡 Verifica las credenciales en Streamlit secrets")
        return
    
    # ========================================
    # SIDEBAR - FILTROS
    # ========================================
    st.sidebar.markdown("## ⚙️ Configuración")
    st.sidebar.markdown("---")
    
    # Cargar lista de competiciones
    try:
        competitions_query = supabase.table('matches')\
            .select('competition_full')\
            .execute()
        
        competitions = sorted(list(set([
            c['competition_full'] for c in competitions_query.data
        ])))
        
    except Exception as e:
        st.sidebar.error("❌ Error cargando competiciones")
        return
    
    if not competitions:
        st.sidebar.warning("⚠️ No hay partidos en la base de datos")
        st.info("💡 Ejecuta `upload_to_supabase.py` para subir partidos")
        return
    
    # 1. COMPETICIÓN
    st.sidebar.markdown("### 🏆 Competición")
    selected_competition = st.sidebar.selectbox(
        "Liga:",
        competitions,
        label_visibility="collapsed"
    )
    
    # 2. TEMPORADA
    seasons_query = supabase.table('matches')\
        .select('season')\
        .eq('competition_full', selected_competition)\
        .execute()
    
    seasons = sorted(list(set([
        s['season'] for s in seasons_query.data
    ])), reverse=True)
    
    st.sidebar.markdown("### 📅 Temporada")
    selected_season = st.sidebar.selectbox(
        "Season:",
        seasons,
        label_visibility="collapsed"
    )
    
    # 3. EQUIPO
    st.sidebar.markdown("### ⚽ Equipo")
    
    # Obtener equipos únicos
    teams_query = supabase.table('matches')\
        .select('description')\
        .eq('competition_full', selected_competition)\
        .eq('season', selected_season)\
        .execute()
    
    all_teams = set()
    for match in teams_query.data:
        teams = match['description'].split(' vs ')
        all_teams.update(teams)
    
    teams_list = ['Todos'] + sorted(list(all_teams))
    selected_team = st.sidebar.selectbox(
        "Team:",
        teams_list,
        label_visibility="collapsed"
    )
    
    # 4. TIPO DE PARTIDO
    st.sidebar.markdown("### 🎯 Tipo de Partido")
    match_type = st.sidebar.radio(
        "Match type:",
        ["Partido más reciente", "Partido específico"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # Construir query base
    query = supabase.table('matches')\
        .select('*')\
        .eq('competition_full', selected_competition)\
        .eq('season', selected_season)\
        .order('date', desc=True)
    
    # Filtrar por equipo si no es "Todos"
    if selected_team != 'Todos':
        query = query.ilike('description', f'%{selected_team}%')
    
    # Ejecutar query
    try:
        matches_result = query.execute()
        filtered_matches = matches_result.data
    except Exception as e:
        st.error(f"❌ Error buscando partidos: {e}")
        return
    
    # Mostrar contador
    st.sidebar.metric("Partidos encontrados", len(filtered_matches))
    
    # ========================================
    # SELECCIÓN DE PARTIDO
    # ========================================
    
    if len(filtered_matches) == 0:
        st.warning("⚠️ No se encontraron partidos con los filtros aplicados")
        return
    
    selected_match = None
    
    if match_type == "Partido más reciente":
        # Seleccionar automáticamente el más reciente
        selected_match = filtered_matches[0]
        
        st.info(f"📅 **Partido más reciente:** {selected_match['description']} ({selected_match['date']})")
    
    else:
        # Mostrar dropdown con todos los partidos
        st.markdown("#### 📋 Selecciona el partido:")
        
        match_options = {}
        for match in filtered_matches:
            code = match['competition_code'] if match['competition_code'] else match['competition'][:3].upper()
            stage = f" | {match['stage']}" if match['stage'] else ''
            
            display_name = f"📅 {match['date']} | {code}{stage} | {match['description']}"
            match_options[display_name] = match
        
        selected_display = st.selectbox(
            "Partido:",
            list(match_options.keys()),
            label_visibility="collapsed"
        )
        
        selected_match = match_options[selected_display]
    
    # ========================================
    # MOSTRAR INFO Y PROCESAR
    # ========================================
    
    if selected_match:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.info(f"🌎 {selected_match['country']}")
        with col2:
            st.info(f"📅 {selected_match['date']}")
        with col3:
            st.info(f"⏰ {selected_match['time']}")
        with col4:
            st.info(f"🏆 {selected_match['competition_code'] or selected_match['competition'][:3]}")
        with col5:
            st.info(f"📊 {selected_match['season']}")
        
        st.markdown("---")
        
        # Obtener JSON completo desde el campo 'data'
        match_data = selected_match['data']
        
        # Guardar temporalmente como archivo para usar process_json_file()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8') as tmp:
            json.dump(match_data, tmp)
            tmp_path = Path(tmp.name)
        
        # Procesar el partido
        process_json_file(tmp_path)
