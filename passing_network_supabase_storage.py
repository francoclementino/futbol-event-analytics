"""
Nueva versión de show_passing_network_tab() que consume JSONs desde Supabase Storage
"""

import streamlit as st
import requests
import json
from pathlib import Path
import tempfile

def show_passing_network_tab():
    """Muestra la pestaña de análisis consumiendo JSONs desde Supabase Storage"""
    
    st.markdown("### 🕸️ Passing Network Analysis")
    st.markdown("**Comparación lado a lado de ambos equipos**")
    
    # ========================================
    # SIDEBAR - CONFIGURACIÓN
    # ========================================
    st.sidebar.markdown("## ⚙️ Configuración")
    st.sidebar.markdown("---")
    
    # Verificar si existe metadata local (para desarrollo) o usar Supabase
    data_scan = scan_data_directories()
    raw_dir = data_scan['raw_dir']
    global_metadata_file = raw_dir / 'matches_metadata.json'
    
    # Intentar cargar metadata desde GitHub (incluida en el repo)
    metadata_url = "https://raw.githubusercontent.com/[TU-USUARIO]/[TU-REPO]/main/data/raw/matches_metadata.json"
    
    try:
        # Primero intentar local (para desarrollo)
        if global_metadata_file.exists():
            with open(global_metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            # Si no existe local, cargar desde GitHub
            response = requests.get(metadata_url)
            metadata = response.json()
        
        df_matches = pd.DataFrame(metadata)
        df_matches['date'] = pd.to_datetime(df_matches['date'])
        df_matches = df_matches.sort_values('date', ascending=False)
        
    except Exception as e:
        st.sidebar.error("⚠️ No se pudo cargar metadata")
        st.sidebar.info("💡 Sube un archivo JSON manualmente:")
        
        uploaded_file = st.sidebar.file_uploader(
            "Arrastra un archivo JSON:",
            type=['json']
        )
        
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as tmp:
                tmp.write(uploaded_file.getvalue().decode('utf-8'))
                tmp_path = Path(tmp.name)
            
            st.info(f"📄 {uploaded_file.name}")
            process_json_file(tmp_path)
        return
    
    # ========================================
    # FILTROS EN SIDEBAR
    # ========================================
    
    # 1. COMPETICIÓN
    st.sidebar.markdown("### 🏆 Competición")
    competitions = sorted(df_matches['competition_full_name'].unique().tolist())
    selected_comp = st.sidebar.selectbox(
        "Liga:",
        competitions,
        label_visibility="collapsed"
    )
    
    filtered_df = df_matches[df_matches['competition_full_name'] == selected_comp]
    
    # 2. TEMPORADA
    st.sidebar.markdown("### 📅 Temporada")
    seasons = sorted(filtered_df['season'].unique().tolist(), reverse=True)
    selected_season = st.sidebar.selectbox(
        "Season:",
        seasons,
        label_visibility="collapsed"
    )
    
    filtered_df = filtered_df[filtered_df['season'] == selected_season]
    
    # 3. EQUIPO
    st.sidebar.markdown("### ⚽ Equipo")
    all_teams = set()
    for desc in filtered_df['description'].unique():
        teams = desc.split(' vs ')
        all_teams.update(teams)
    
    teams_list = ['Todos'] + sorted(list(all_teams))
    selected_team = st.sidebar.selectbox(
        "Team:",
        teams_list,
        label_visibility="collapsed"
    )
    
    if selected_team != 'Todos':
        filtered_df = filtered_df[
            filtered_df['description'].str.contains(selected_team, case=False, na=False)
        ]
    
    # 4. TIPO DE PARTIDO
    st.sidebar.markdown("### 🎯 Tipo de Partido")
    match_type = st.sidebar.radio(
        "Match type:",
        ["Partido más reciente", "Partido específico"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.metric("Partidos", len(filtered_df))
    
    # ========================================
    # SELECCIÓN Y DESCARGA
    # ========================================
    
    if len(filtered_df) == 0:
        st.warning("⚠️ No hay partidos con esos filtros")
        return
    
    selected_match = None
    
    if match_type == "Partido más reciente":
        selected_match = filtered_df.iloc[0]
        st.info(f"📅 **Más reciente:** {selected_match['description']} ({selected_match['date'].strftime('%d/%m/%Y')})")
    else:
        st.markdown("#### 📋 Selecciona el partido:")
        
        match_options = {}
        for idx, row in filtered_df.iterrows():
            date_str = row['date'].strftime('%d/%m/%Y')
            code = row['competition_code'] or row['competition'][:3].upper()
            stage = f" | {row['stage']}" if row['stage'] else ''
            
            display = f"📅 {date_str} | {code}{stage} | {row['description']}"
            match_options[display] = row
        
        selected_display = st.selectbox(
            "Partido:",
            list(match_options.keys()),
            label_visibility="collapsed"
        )
        
        selected_match = match_options[selected_display]
    
    # ========================================
    # DESCARGAR JSON DESDE SUPABASE
    # ========================================
    
    if selected_match is not None:
        # Mostrar info
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.info(f"🌎 {selected_match['country']}")
        with col2:
            st.info(f"📅 {selected_match['date'].strftime('%d/%m/%Y')}")
        with col3:
            st.info(f"⏰ {selected_match['time']}")
        with col4:
            st.info(f"🏆 {selected_match['competition_code'] or selected_match['competition'][:3]}")
        with col5:
            st.info(f"📊 {selected_match['season']}")
        
        st.markdown("---")
        
        # Construir URL de Supabase Storage
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://[TU-PROYECTO].supabase.co")
        filepath = selected_match['filepath']
        json_url = f"{SUPABASE_URL}/storage/v1/object/public/matches/{filepath}"
        
        # Descargar JSON
        with st.spinner('📥 Descargando partido desde Supabase...'):
            try:
                response = requests.get(json_url, timeout=10)
                response.raise_for_status()
                match_data = response.json()
                
                # Guardar temporalmente
                with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as tmp:
                    json.dump(match_data, tmp)
                    tmp_path = Path(tmp.name)
                
                # Procesar
                process_json_file(tmp_path)
                
            except Exception as e:
                st.error(f"❌ Error descargando: {e}")
                st.info("💡 Verifica que el archivo esté en Supabase Storage")
