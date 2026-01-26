# passing_network_tab.py - VERSIÓN COMPLETA
# Módulo de análisis de redes de pases con soporte multi-formato y file uploader
import streamlit as st
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import numpy as np
import sys
import tempfile

# Agregar carpeta Codigos al path para importar procesadores
codigos_path = Path(__file__).parent / 'Codigos'
if codigos_path.exists():
    sys.path.insert(0, str(codigos_path))

def scan_data_directories():
    """Escanea las carpetas de datos y devuelve archivos disponibles"""
    project_root = Path(__file__).parent
    
    # Carpetas de datos
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    
    # Crear carpetas si no existen
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Buscar archivos JSON (cualquier formato)
    json_files = sorted(raw_dir.glob('*.json'))
    parquet_files = sorted(processed_dir.glob('*.parquet'))
    
    # Buscar también en subdirectorios de processed
    for subdir in processed_dir.iterdir():
        if subdir.is_dir():
            parquet_files.extend(subdir.glob('*.parquet'))
    
    return {
        'raw_dir': raw_dir,
        'processed_dir': processed_dir,
        'json_files': json_files,
        'parquet_files': sorted(parquet_files)
    }

def load_match_data(json_path):
    """Carga datos del archivo JSON y detecta formato automáticamente"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Detectar formato
        if 'Event' in data:
            return {'format': 'f24', 'data': data}
        elif 'matchInfo' in data and 'liveData' in data:
            return {'format': 'stats_perform', 'data': data}
        elif 'events' in data:
            return {'format': 'generic', 'data': data}
        else:
            st.warning("⚠️ Formato de JSON no reconocido. Intentando parsear...")
            return {'format': 'unknown', 'data': data}
            
    except Exception as e:
        st.error(f"Error cargando archivo: {e}")
        return None

def load_parquet_data(parquet_path):
    """Carga datos de archivo Parquet procesado"""
    try:
        df = pd.read_parquet(parquet_path)
        return df
    except Exception as e:
        st.error(f"Error cargando parquet: {e}")
        return None

def extract_passes(match_obj, team_id, period=None):
    """Extrae todos los pases de un equipo específico - soporta múltiples formatos"""
    
    if match_obj is None:
        return []
    
    format_type = match_obj.get('format', 'unknown')
    match_data = match_obj.get('data', {})
    
    if format_type == 'stats_perform':
        return extract_passes_stats_perform(match_data, team_id, period)
    elif format_type == 'f24':
        return extract_passes_f24(match_data, team_id, period)
    else:
        st.error(f"❌ Formato '{format_type}' no soportado para extracción de pases")
        return []

def extract_passes_stats_perform(match_data, team_id, period=None):
    """Extrae pases del formato Stats Perform / Opta API"""
    passes = []
    
    if 'liveData' not in match_data or 'event' not in match_data['liveData']:
        return passes
    
    for event in match_data['liveData']['event']:
        if event.get('typeId') != 1:
            continue
        
        if str(event.get('contestantId')) != str(team_id):
            continue
        
        if period and int(event.get('periodId', 0)) != period:
            continue
        
        x = float(event.get('x', 0))
        y = float(event.get('y', 0))
        
        end_x, end_y = None, None
        qualifiers = event.get('qualifier', [])
        
        for q in qualifiers:
            if q.get('qualifierId') == 140:
                end_x = float(q.get('value', 0))
            elif q.get('qualifierId') == 141:
                end_y = float(q.get('value', 0))
        
        outcome = event.get('outcomeType', 0)
        is_successful = outcome == 1
        
        passes.append({
            'player_id': event.get('playerId'),
            'x': x,
            'y': y,
            'end_x': end_x,
            'end_y': end_y,
            'outcome': is_successful,
            'timestamp': event.get('timeStamp'),
            'period': event.get('periodId')
        })
    
    return passes

def extract_passes_f24(match_data, team_id, period=None):
    """Extrae pases del formato F24 clásico de Opta"""
    passes = []
    
    for event in match_data.get('Event', []):
        if event.get('type_id') != 1:
            continue
            
        if str(event.get('team_id')) != str(team_id):
            continue
        
        if period and int(event.get('period_id', 0)) != period:
            continue
        
        x = float(event.get('x', 0))
        y = float(event.get('y', 0))
        
        end_x, end_y = None, None
        for q in event.get('qualifier', []):
            if q.get('qualifier_id') == 140:
                end_x = float(q.get('value', 0))
            elif q.get('qualifier_id') == 141:
                end_y = float(q.get('value', 0))
        
        outcome = event.get('outcome', 1)
        is_successful = outcome == 1
        
        passes.append({
            'player_id': event.get('player_id'),
            'x': x,
            'y': y,
            'end_x': end_x,
            'end_y': end_y,
            'outcome': is_successful,
            'timestamp': event.get('timestamp')
        })
    
    return passes

def get_player_names(match_obj, team_id):
    """Extrae nombres de jugadores de un equipo - soporta múltiples formatos"""
    
    if match_obj is None:
        return {}
    
    format_type = match_obj.get('format', 'unknown')
    match_data = match_obj.get('data', {})
    
    if format_type == 'stats_perform':
        return get_player_names_stats_perform(match_data, team_id)
    elif format_type == 'f24':
        return get_player_names_f24(match_data, team_id)
    else:
        return {}

def get_player_names_stats_perform(match_data, team_id):
    """Extrae nombres de jugadores del formato Stats Perform"""
    players = {}
    
    if 'liveData' in match_data and 'lineup' in match_data['liveData']:
        for team_lineup in match_data['liveData']['lineup']:
            if str(team_lineup.get('contestantId')) == str(team_id):
                for player in team_lineup.get('player', []):
                    player_id = player.get('playerId')
                    
                    first_name = player.get('matchName', '')
                    last_name = player.get('surname', '')
                    
                    if first_name and last_name:
                        full_name = f"{first_name} {last_name}"
                    else:
                        full_name = first_name or last_name or player.get('shortName', f'Player {player_id}')
                    
                    players[player_id] = full_name
                break
    
    if not players and 'liveData' in match_data and 'event' in match_data['liveData']:
        for event in match_data['liveData']['event']:
            if str(event.get('contestantId')) != str(team_id):
                continue
            
            player_id = event.get('playerId')
            if player_id and player_id not in players:
                players[player_id] = f'Jugador {player_id}'
    
    return players

def get_player_names_f24(match_data, team_id):
    """Extrae nombres de jugadores del formato F24"""
    players = {}
    
    for event in match_data.get('Event', []):
        if str(event.get('team_id')) != str(team_id):
            continue
        
        player_id = event.get('player_id')
        player_name = event.get('player_name', f'Player {player_id}')
        
        if player_id and player_name:
            players[player_id] = player_name
    
    return players

def get_team_names(match_obj):
    """Extrae nombres de equipos del match - soporta múltiples formatos"""
    
    if match_obj is None:
        return {}
    
    format_type = match_obj.get('format', 'unknown')
    match_data = match_obj.get('data', {})
    
    if format_type == 'stats_perform':
        return get_team_names_stats_perform(match_data)
    elif format_type == 'f24':
        return get_team_names_f24(match_data)
    else:
        return {}

def get_team_names_stats_perform(match_data):
    """Extrae nombres de equipos del formato Stats Perform"""
    teams = {}
    
    if 'matchInfo' in match_data and 'contestant' in match_data['matchInfo']:
        for team in match_data['matchInfo']['contestant']:
            team_id = team.get('id')
            team_name = team.get('name', f'Team {team_id}')
            
            if team_id:
                teams[team_id] = team_name
    
    return teams

def get_team_names_f24(match_data):
    """Extrae nombres de equipos del formato F24"""
    teams = {}
    
    for event in match_data.get('Event', []):
        team_id = str(event.get('team_id'))
        team_name = event.get('team_name', f'Team {team_id}')
        
        if team_id not in teams:
            teams[team_id] = team_name
    
    return teams

def calculate_pass_network_positions(passes, player_names):
    """Calcula posiciones promedio y conexiones entre jugadores"""
    player_positions = {}
    player_pass_counts = {}
    connections = {}
    
    for pass_event in passes:
        player_id = pass_event['player_id']
        
        if player_id not in player_positions:
            player_positions[player_id] = {'x': [], 'y': []}
            player_pass_counts[player_id] = 0
        
        player_positions[player_id]['x'].append(pass_event['x'])
        player_positions[player_id]['y'].append(pass_event['y'])
        
        if pass_event['outcome']:
            player_pass_counts[player_id] += 1
    
    avg_positions = {}
    for player_id, positions in player_positions.items():
        avg_positions[player_id] = {
            'x': np.mean(positions['x']),
            'y': np.mean(positions['y']),
            'name': player_names.get(player_id, f'Player {player_id}'),
            'passes': player_pass_counts.get(player_id, 0)
        }
    
    for i, pass_event in enumerate(passes):
        if not pass_event['outcome'] or not pass_event['end_x']:
            continue
        
        passer = pass_event['player_id']
        
        if i + 1 < len(passes):
            next_event = passes[i + 1]
            receiver = next_event['player_id']
            
            if passer != receiver:
                key = (passer, receiver)
                connections[key] = connections.get(key, 0) + 1
    
    return avg_positions, connections

def plot_passing_network(avg_positions, connections, team_name, ax, min_passes=3):
    """Visualiza la red de pases en una cancha"""
    pitch = Pitch(pitch_type='custom', pitch_length=105, pitch_width=68,
                  line_color='white', pitch_color='#1a5d1a')
    pitch.draw(ax=ax)
    
    scale_x = 105 / 100
    scale_y = 68 / 100
    
    for (passer, receiver), count in connections.items():
        if count < min_passes:
            continue
        
        if passer in avg_positions and receiver in avg_positions:
            x1 = avg_positions[passer]['x'] * scale_x
            y1 = avg_positions[passer]['y'] * scale_y
            x2 = avg_positions[receiver]['x'] * scale_x
            y2 = avg_positions[receiver]['y'] * scale_y
            
            width = max(0.5, count / 5)
            alpha = min(0.8, count / 10)
            
            ax.plot([x1, x2], [y1, y2], 
                   color='cyan', linewidth=width, alpha=alpha, zorder=1)
    
    for player_id, pos in avg_positions.items():
        x = pos['x'] * scale_x
        y = pos['y'] * scale_y
        passes = pos['passes']
        
        size = max(100, passes * 10)
        
        ax.scatter(x, y, s=size, c='gold', edgecolors='white', 
                  linewidths=2, zorder=2, marker='h')
        
        name_parts = pos['name'].split()
        short_name = name_parts[-1] if name_parts else pos['name']
        
        ax.text(x, y - 3, short_name, fontsize=8, color='white',
               ha='center', va='top', weight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
    
    ax.set_title(f'{team_name} - Passing Network', fontsize=14, weight='bold', color='white')
    ax.axis('off')

def process_json_file(json_path):
    """Procesa un archivo JSON y muestra la red de pases"""
    with st.spinner('Cargando match data...'):
        match_data = load_match_data(json_path)
    
    if match_data is None:
        return
    
    # Mostrar formato detectado
    format_type = match_data.get('format', 'unknown')
    format_label = {
        'f24': '🟢 Formato: Opta F24',
        'stats_perform': '🟡 Formato: Stats Perform / Opta API',
        'generic': '🟠 Formato: Genérico',
        'unknown': '⚠️ Formato: Desconocido'
    }
    st.info(format_label.get(format_type, format_type))
    
    # Obtener equipos
    teams = get_team_names(match_data)
    
    if len(teams) < 2:
        st.error("❌ No se encontraron 2 equipos en el archivo")
        return
    
    team_ids = list(teams.keys())
    
    st.success(f"✅ Match cargado: {teams[team_ids[0]]} vs {teams[team_ids[1]]}")
    
    # Filtros
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        period = st.selectbox(
            "Período:",
            [("Todos", None), ("1er Tiempo", 1), ("2do Tiempo", 2)],
            format_func=lambda x: x[0]
        )[1]
    
    with col2:
        min_passes = st.slider(
            "Pases mínimos (conexiones):",
            min_value=1,
            max_value=10,
            value=3
        )
    
    # Procesar y visualizar
    st.markdown("---")
    
    # Extraer datos de ambos equipos
    passes_team1 = extract_passes(match_data, team_ids[0], period)
    passes_team2 = extract_passes(match_data, team_ids[1], period)
    
    players_team1 = get_player_names(match_data, team_ids[0])
    players_team2 = get_player_names(match_data, team_ids[1])
    
    # Calcular redes
    positions1, connections1 = calculate_pass_network_positions(passes_team1, players_team1)
    positions2, connections2 = calculate_pass_network_positions(passes_team2, players_team2)
    
    # Métricas comparativas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(f"{teams[team_ids[0]]} - Pases", len([p for p in passes_team1 if p['outcome']]))
    with col2:
        acc1 = len([p for p in passes_team1 if p['outcome']]) / len(passes_team1) * 100 if passes_team1 else 0
        st.metric("Precisión", f"{acc1:.1f}%")
    with col3:
        st.metric(f"{teams[team_ids[1]]} - Pases", len([p for p in passes_team2 if p['outcome']]))
    with col4:
        acc2 = len([p for p in passes_team2 if p['outcome']]) / len(passes_team2) * 100 if passes_team2 else 0
        st.metric("Precisión", f"{acc2:.1f}%")
    
    # Visualización lado a lado
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10), facecolor='#0e1117')
    
    plot_passing_network(positions1, connections1, teams[team_ids[0]], ax1, min_passes)
    plot_passing_network(positions2, connections2, teams[team_ids[1]], ax2, min_passes)
    
    st.pyplot(fig)
    plt.close()
    
    # Tablas de conexiones principales
    st.markdown("---")
    st.subheader("📊 Top 5 Conexiones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{teams[team_ids[0]]}**")
        top_conn1 = sorted(connections1.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_conn1:
            conn_data1 = []
            for (p1, p2), count in top_conn1:
                name1 = players_team1.get(p1, f'P{p1}')
                name2 = players_team1.get(p2, f'P{p2}')
                conn_data1.append({
                    'De': name1.split()[-1],
                    'Para': name2.split()[-1],
                    'Pases': count
                })
            st.dataframe(pd.DataFrame(conn_data1), use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown(f"**{teams[team_ids[1]]}**")
        top_conn2 = sorted(connections2.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if top_conn2:
            conn_data2 = []
            for (p1, p2), count in top_conn2:
                name1 = players_team2.get(p1, f'P{p1}')
                name2 = players_team2.get(p2, f'P{p2}')
                conn_data2.append({
                    'De': name1.split()[-1],
                    'Para': name2.split()[-1],
                    'Pases': count
                })
            st.dataframe(pd.DataFrame(conn_data2), use_container_width=True, hide_index=True)

def show_passing_network_tab():
    """Muestra la pestaña de análisis de redes de pases"""
    
    st.markdown("### 🕸️ Passing Network Analysis")
    st.markdown("**Comparación lado a lado de ambos equipos**")
    
    # Escanear carpetas
    data_scan = scan_data_directories()
    
    # Modo de selección
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        data_mode = st.radio(
            "📂 Tipo de datos:",
            ["JSON Crudos", "Parquet Procesados"],
            help="Selecciona si quieres cargar archivos JSON crudos o datos ya procesados"
        )
    
    with col2:
        if data_mode == "JSON Crudos":
            st.info(f"📊 {len(data_scan['json_files'])} archivos JSON locales")
        else:
            st.info(f"📦 {len(data_scan['parquet_files'])} archivos Parquet")
    
    # Selección de archivo
    if data_mode == "Parquet Procesados":
        if not data_scan['parquet_files']:
            st.warning("⚠️ No hay archivos Parquet procesados. Usa 'JSON Crudos' primero.")
            return
        
        parquet_options = {}
        for pq in data_scan['parquet_files']:
            rel_path = pq.relative_to(data_scan['processed_dir'])
            parquet_options[str(rel_path)] = pq
        
        selected_name = st.selectbox(
            "Selecciona archivo Parquet:",
            list(parquet_options.keys())
        )
        
        if selected_name:
            selected_file = parquet_options[selected_name]
            
            with st.spinner('Cargando datos...'):
                df = load_parquet_data(selected_file)
            
            if df is not None:
                st.success(f"✅ Cargados {len(df):,} eventos")
                st.info("🚧 Análisis de Parquet en desarrollo. Por ahora, usa 'JSON Crudos' para redes de pases.")
    
    else:  # JSON Crudos
        st.markdown("---")
        st.markdown("#### 📁 Selección de archivos JSON")
        
        # Opción 1: Archivos locales (solo funciona en localhost)
        if data_scan['json_files']:
            st.success(f"✅ {len(data_scan['json_files'])} archivos locales detectados en data/raw/")
            
            json_options = {f.name: f for f in data_scan['json_files']}
            
            selected_name = st.selectbox(
                "Selecciona archivo JSON local:",
                list(json_options.keys())
            )
            
            if selected_name:
                selected_file = json_options[selected_name]
                process_json_file(selected_file)
        else:
            st.warning("⚠️ No hay archivos JSON en data/raw/ (carpeta local)")
        
        # Opción 2: Subir archivo (funciona en Streamlit Cloud)
        st.markdown("---")
        st.markdown("##### 📤 O sube un archivo JSON:")
        
        uploaded_file = st.file_uploader(
            "Arrastra un archivo JSON del partido:",
            type=['json'],
            help="Sube un archivo JSON con datos OPTA / Stats Perform"
        )
        
        if uploaded_file is not None:
            # Guardar temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8') as tmp:
                tmp.write(uploaded_file.getvalue().decode('utf-8'))
                tmp_path = Path(tmp.name)
            
            st.info(f"📄 Archivo subido: {uploaded_file.name}")
            process_json_file(tmp_path)
