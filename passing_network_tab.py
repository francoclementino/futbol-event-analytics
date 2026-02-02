# passing_network_tab.py - VERSIÓN DEFINITIVA
# Sistema de 3 variables visuales: Grosor=Combinaciones, Tamaño=Pases, Color=xT
import streamlit as st
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import numpy as np
import sys
import tempfile

# Agregar carpeta Codigos al path
codigos_path = Path(__file__).parent / 'Codigos'
if codigos_path.exists():
    sys.path.insert(0, str(codigos_path))

# Importar módulo xT
try:
    from xt_calculator import calculate_pass_xt, get_xt_value
    XT_AVAILABLE = True
except ImportError:
    XT_AVAILABLE = False

def scan_data_directories():
    """Escanea las carpetas de datos y devuelve archivos disponibles"""
    project_root = Path(__file__).parent
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    json_files = sorted(raw_dir.glob('*.json'))
    parquet_files = sorted(processed_dir.glob('*.parquet'))
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
        if 'Event' in data:
            return {'format': 'f24', 'data': data}
        elif 'matchInfo' in data and 'liveData' in data:
            return {'format': 'stats_perform', 'data': data}
        elif 'events' in data:
            return {'format': 'generic', 'data': data}
        else:
            st.warning("⚠️ Formato de JSON no reconocido")
            return {'format': 'unknown', 'data': data}
    except Exception as e:
        st.error(f"Error cargando archivo: {e}")
        return None

def extract_passes(match_obj, team_id, period=None, time_range=None):
    """Extrae todos los pases de un equipo específico"""
    if match_obj is None:
        return []
    format_type = match_obj.get('format', 'unknown')
    match_data = match_obj.get('data', {})
    if format_type == 'stats_perform':
        return extract_passes_stats_perform(match_data, team_id, period, time_range)
    elif format_type == 'f24':
        return extract_passes_f24(match_data, team_id, period)
    else:
        st.error(f"❌ Formato '{format_type}' no soportado")
        return []

def extract_passes_stats_perform(match_data, team_id, period=None, time_range=None):
    """Extrae pases del formato Stats Perform"""
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
        if time_range:
            event_min = int(event.get('timeMin', 0))
            if period == 2:
                event_min += 45
            if not (time_range[0] <= event_min <= time_range[1]):
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
        outcome = event.get('outcome', 0)
        is_successful = outcome == 1
        xt_value = 0.0
        if XT_AVAILABLE and is_successful and end_x is not None and end_y is not None:
            xt_value = calculate_pass_xt(x, y, end_x, end_y)
        passes.append({
            'player_id': event.get('playerId'),
            'x': x,
            'y': y,
            'end_x': end_x,
            'end_y': end_y,
            'outcome': is_successful,
            'timestamp': event.get('timeStamp'),
            'period': event.get('periodId'),
            'xt': xt_value
        })
    return passes

def extract_passes_f24(match_data, team_id, period=None):
    """Extrae pases del formato F24"""
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
        xt_value = 0.0
        if XT_AVAILABLE and is_successful and end_x is not None and end_y is not None:
            xt_value = calculate_pass_xt(x, y, end_x, end_y)
        passes.append({
            'player_id': event.get('player_id'),
            'x': x,
            'y': y,
            'end_x': end_x,
            'end_y': end_y,
            'outcome': is_successful,
            'timestamp': event.get('timestamp'),
            'xt': xt_value
        })
    return passes

def get_player_names(match_obj, team_id):
    """Extrae nombres de jugadores"""
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
    """Extrae nombres Stats Perform"""
    players = {}
    if 'liveData' in match_data and 'event' in match_data['liveData']:
        for event in match_data['liveData']['event']:
            if str(event.get('contestantId')) != str(team_id):
                continue
            player_id = event.get('playerId')
            player_name = event.get('playerName')
            if player_id and player_name and player_id not in players:
                players[player_id] = player_name
    if not players and 'liveData' in match_data and 'lineup' in match_data['liveData']:
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
    return players

def get_player_names_f24(match_data, team_id):
    """Extrae nombres F24"""
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
    """Extrae nombres de equipos"""
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
    """Extrae nombres de equipos Stats Perform"""
    teams = {}
    if 'matchInfo' in match_data and 'contestant' in match_data['matchInfo']:
        for team in match_data['matchInfo']['contestant']:
            team_id = team.get('id')
            team_name = team.get('name', f'Team {team_id}')
            if team_id:
                teams[team_id] = team_name
    return teams

def get_team_names_f24(match_data):
    """Extrae nombres de equipos F24"""
    teams = {}
    for event in match_data.get('Event', []):
        team_id = str(event.get('team_id'))
        team_name = event.get('team_name', f'Team {team_id}')
        if team_id not in teams:
            teams[team_id] = team_name
    return teams

def get_player_short_name(full_name):
    """Convierte nombre completo a formato con inicial"""
    if not full_name or pd.isna(full_name):
        return "Unknown"
    parts = str(full_name).strip().split()
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0][0]}. {parts[1]}"
    else:
        return f"{parts[0][0]}. {parts[-1]}"

def calculate_pass_network_positions(passes, player_names, invert_coords=False):
    """Calcula posiciones promedio y conexiones entre jugadores con xT"""
    import pandas as pd
    if not passes:
        return {}, {}
    df = pd.DataFrame(passes)
    if invert_coords:
        df['x'] = 100 - df['x']
        df['y'] = 100 - df['y']
        df.loc[df['end_x'].notnull(), 'end_x'] = 100 - df.loc[df['end_x'].notnull(), 'end_x']
        df.loc[df['end_y'].notnull(), 'end_y'] = 100 - df.loc[df['end_y'].notnull(), 'end_y']
    avg_locs = df.groupby('player_id').agg({'x': 'mean', 'y': 'mean'})
    pass_counts = df[df['outcome'] == True].groupby('player_id').size()
    if 'xt' in df.columns:
        player_xt = df[df['outcome'] == True].groupby('player_id')['xt'].sum()
    else:
        player_xt = pd.Series(dtype=float)
    avg_positions = {}
    for player_id in avg_locs.index:
        avg_positions[player_id] = {
            'x': avg_locs.loc[player_id, 'x'],
            'y': avg_locs.loc[player_id, 'y'],
            'name': player_names.get(player_id, f'Player {player_id}'),
            'passes': int(pass_counts.get(player_id, 0)),
            'xt': float(player_xt.get(player_id, 0.0))
        }
    connections = {}
    connection_xt = {}
    successful_passes = df[
        (df['outcome'] == True) & 
        (df['end_x'].notnull()) & 
        (df['end_y'].notnull())
    ].copy()
    if len(successful_passes) == 0:
        return avg_positions, connections
    for idx, pass_row in successful_passes.iterrows():
        passer_id = pass_row['player_id']
        end_x = pass_row['end_x']
        end_y = pass_row['end_y']
        pass_xt = pass_row.get('xt', 0.0)
        min_distance = float('inf')
        receiver_id = None
        for player_id, pos in avg_positions.items():
            if player_id == passer_id:
                continue
            distance = ((pos['x'] - end_x)**2 + (pos['y'] - end_y)**2)**0.5
            if distance < min_distance:
                min_distance = distance
                receiver_id = player_id
        if receiver_id and min_distance < 25:
            key = (passer_id, receiver_id)
            connections[key] = connections.get(key, 0) + 1
            connection_xt[key] = connection_xt.get(key, 0.0) + pass_xt
    for key in connections.keys():
        connections[key] = {
            'count': connections[key],
            'xt': connection_xt.get(key, 0.0)
        }
    return avg_positions, connections

def add_legend(ax, team_color='red'):
    """Agrega leyenda visual explicativa con 3 variables"""
    import matplotlib.patheffects as path_effects
    
    # Colores según equipo
    if team_color == 'red':
        color_light = '#e89b97'
        color_mid = '#e74c3c'
        color_dark = '#c0392b'
    elif team_color == 'orange':
        color_light = '#ffb366'
        color_mid = '#ff9500'
        color_dark = '#cc7700'
    else:
        color_light = '#66e6ff'
        color_mid = '#00d9ff'
        color_dark = '#00aac7'
    
    legend_y = 72
    legend_x = 2
    
    # 1. CANTIDAD DE PASES (Tamaño de círculo)
    text = ax.text(legend_x, legend_y, "Low pass count", 
                   fontsize=8, color='white', weight='bold', ha='left')
    text.set_path_effects([path_effects.Stroke(linewidth=2, foreground='black'), path_effects.Normal()])
    
    sizes = [300, 600, 1200]
    for i, size in enumerate(sizes):
        x = legend_x + 16 + (i * 5)
        ax.scatter(x, legend_y, s=size, c=color_mid, edgecolors='white', linewidths=1.5, alpha=0.9, zorder=10)
    
    text = ax.text(legend_x + 33, legend_y, "High pass count", 
                   fontsize=8, color='white', weight='bold', ha='left')
    text.set_path_effects([path_effects.Stroke(linewidth=2, foreground='black'), path_effects.Normal()])
    
    # 2. CANTIDAD DE COMBINACIONES (Grosor de línea)
    legend_y -= 6
    text = ax.text(legend_x, legend_y, "Low pass combination", 
                   fontsize=8, color='white', weight='bold', ha='left')
    text.set_path_effects([path_effects.Stroke(linewidth=2, foreground='black'), path_effects.Normal()])
    
    widths = [2, 5, 10]
    for i, width in enumerate(widths):
        x_start = legend_x + 20 + (i * 6)
        x_end = x_start + 4
        ax.plot([x_start, x_end], [legend_y, legend_y],
               color=color_mid, linewidth=width, alpha=0.9,
               solid_capstyle='round', zorder=10)
    
    text = ax.text(legend_x + 42, legend_y, "High pass combination", 
                   fontsize=8, color='white', weight='bold', ha='left')
    text.set_path_effects([path_effects.Stroke(linewidth=2, foreground='black'), path_effects.Normal()])

def plot_passing_network(avg_positions, connections, team_name, ax, min_passes=3, team_color='cyan'):
    """Visualiza red de pases con 3 variables: Grosor=Count, Tamaño=Pases, Color=xT"""
    pitch = Pitch(pitch_type='custom', pitch_length=105, pitch_width=68,
                  line_color='white', pitch_color='#0a3d0a', linewidth=2,
                  pad_top=10)
    pitch.draw(ax=ax)
    
    scale_x = 105 / 100
    scale_y = 68 / 100
    
    # Colores base
    if team_color == 'red':
        base_rgb = (231, 76, 60)
    elif team_color == 'orange':
        base_rgb = (255, 149, 0)
    else:
        base_rgb = (0, 217, 255)
    
    # Encontrar máximos para normalización
    if connections:
        max_xt_conn = max([conn.get('xt', 0) for conn in connections.values()] + [0.01])
        max_count = max([conn.get('count', 1) for conn in connections.values()] + [1])
    else:
        max_xt_conn = 0.01
        max_count = 1
    
    if avg_positions:
        max_xt_player = max([pos['xt'] for pos in avg_positions.values()] + [0.01])
        max_passes = max([pos['passes'] for pos in avg_positions.values()] + [1])
    else:
        max_xt_player = 0.01
        max_passes = 1
    
    connections_drawn = 0
    for (passer, receiver), conn_data in connections.items():
        if isinstance(conn_data, dict):
            count = conn_data['count']
            xt = conn_data.get('xt', 0.0)
        else:
            count = conn_data
            xt = 0.0
        
        if count < min_passes:
            continue
        
        if passer in avg_positions and receiver in avg_positions:
            x1 = avg_positions[passer]['x'] * scale_x
            y1 = avg_positions[passer]['y'] * scale_y
            x2 = avg_positions[receiver]['x'] * scale_x
            y2 = avg_positions[receiver]['y'] * scale_y
            
            # GROSOR basado en CANTIDAD DE COMBINACIONES
            width = max(2, min(count * 0.8, 12))
            
            # COLOR basado en xT (degradado de intensidad)
            if XT_AVAILABLE and xt > 0:
                xt_norm = min(xt / max_xt_conn, 1.0)
                intensity = 0.4 + (xt_norm * 0.6)
                r = int(base_rgb[0] * intensity)
                g = int(base_rgb[1] * intensity)
                b = int(base_rgb[2] * intensity)
                line_color = f'#{r:02x}{g:02x}{b:02x}'
                alpha = 0.6 + (xt_norm * 0.35)
            else:
                intensity = 0.7
                r = int(base_rgb[0] * intensity)
                g = int(base_rgb[1] * intensity)
                b = int(base_rgb[2] * intensity)
                line_color = f'#{r:02x}{g:02x}{b:02x}'
                alpha = 0.8
            
            ax.plot([x1, x2], [y1, y2], 
                   color=line_color, linewidth=width, alpha=alpha, zorder=1,
                   solid_capstyle='round')
            connections_drawn += 1
    
    if connections_drawn == 0:
        ax.text(52.5, 5, f'No hay conexiones con min_passes={min_passes}', 
               fontsize=10, color='yellow', ha='center', weight='bold',
               bbox=dict(boxstyle='round', facecolor='red', alpha=0.7))
    
    for player_id, pos in avg_positions.items():
        x = pos['x'] * scale_x
        y = pos['y'] * scale_y
        passes = pos['passes']
        player_xt = pos['xt']
        
        # TAMAÑO basado en CANTIDAD DE PASES
        size = max(400, min((passes / max_passes) * 2500, 3000))
        
        # COLOR basado en xT del jugador
        if XT_AVAILABLE and player_xt > 0:
            xt_norm = min(player_xt / max_xt_player, 1.0)
            intensity = 0.4 + (xt_norm * 0.6)
        else:
            intensity = 0.7
        
        r = int(base_rgb[0] * intensity)
        g = int(base_rgb[1] * intensity)
        b = int(base_rgb[2] * intensity)
        node_color = f'#{r:02x}{g:02x}{b:02x}'
        
        ax.scatter(x, y, s=size, c=node_color, edgecolors='white', 
                  linewidths=3, zorder=2, marker='o', alpha=0.95)
        
        short_name = get_player_short_name(pos['name'])
        if len(short_name) > 10:
            short_name = short_name[:10]
        
        if y > 34:
            text_y = y - 4
            va = 'top'
        else:
            text_y = y + 4
            va = 'bottom'
        
        import matplotlib.patheffects as path_effects
        text = ax.text(x, text_y, short_name, fontsize=10, color='white',
                      ha='center', va=va, weight='bold', zorder=3)
        text.set_path_effects([
            path_effects.Stroke(linewidth=2, foreground='black'),
            path_effects.Normal()
        ])
    
    # Agregar leyenda
    add_legend(ax, team_color)
    
    ax.set_title(f'{team_name} - Passing Network', 
                fontsize=16, weight='bold', color='white', pad=15)
    ax.axis('off')

def process_json_file(json_path):
    """Procesa un archivo JSON y muestra la red de pases"""
    with st.spinner('Cargando match data...'):
        match_data = load_match_data(json_path)
    
    if match_data is None:
        return
    
    format_type = match_data.get('format', 'unknown')
    format_label = {
        'f24': '🟢 Formato: Opta F24',
        'stats_perform': '🟡 Formato: Stats Perform / Opta API',
        'generic': '🟠 Formato: Genérico',
        'unknown': '⚠️ Formato: Desconocido'
    }
    st.info(format_label.get(format_type, format_type))
    
    teams = get_team_names(match_data)
    
    if len(teams) < 2:
        st.error("❌ No se encontraron 2 equipos en el archivo")
        return
    
    team_ids = list(teams.keys())
    st.success(f"✅ Match cargado: {teams[team_ids[0]]} vs {teams[team_ids[1]]}")
    
    st.markdown("---")
    st.markdown("#### ⚙️ Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        period = st.selectbox(
            "Período:",
            [("Partido Completo", None), ("1er Tiempo", 1), ("2do Tiempo", 2)],
            format_func=lambda x: x[0]
        )[1]
    
    with col2:
        min_passes = st.slider(
            "Pases mínimos (conexiones):",
            min_value=1,
            max_value=10,
            value=2,
            help="Mínimo número de pases entre dos jugadores para mostrar la conexión"
        )
    
    with col3:
        max_minutes = 90
        if period == 1:
            max_minutes = 45
        elif period == 2:
            max_minutes = 90
        
        use_time_filter = st.checkbox(
            "Filtrar por minutos",
            value=False,
            help="Activar para analizar un rango específico de minutos"
        )
    
    time_range = None
    if use_time_filter:
        st.markdown("**Rango de tiempo:**")
        time_range = st.slider(
            "Selecciona rango de minutos:",
            min_value=0,
            max_value=max_minutes,
            value=(0, max_minutes),
            help="Arrastra para seleccionar el rango de minutos a analizar"
        )
        st.info(f"🕒 Analizando minutos {time_range[0]} - {time_range[1]}")
    
    st.markdown("---")
    
    passes_team1 = extract_passes(match_data, team_ids[0], period, time_range)
    passes_team2 = extract_passes(match_data, team_ids[1], period, time_range)
    
    if not passes_team1 and not passes_team2:
        st.error("❌ No se encontraron pases en el rango seleccionado")
        st.info("💡 Intenta ajustar los filtros")
        return
    
    players_team1 = get_player_names(match_data, team_ids[0])
    players_team2 = get_player_names(match_data, team_ids[1])
    
    positions1, connections1 = calculate_pass_network_positions(passes_team1, players_team1, invert_coords=False)
    positions2, connections2 = calculate_pass_network_positions(passes_team2, players_team2, invert_coords=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    successful_passes_1 = len([p for p in passes_team1 if p['outcome']])
    successful_passes_2 = len([p for p in passes_team2 if p['outcome']])
    total_passes_1 = len(passes_team1)
    total_passes_2 = len(passes_team2)
    
    with col1:
        st.metric(f"{teams[team_ids[0]]} - Pases", successful_passes_1)
    with col2:
        acc1 = (successful_passes_1 / total_passes_1 * 100) if total_passes_1 > 0 else 0
        st.metric("Precisión", f"{acc1:.1f}%")
    with col3:
        st.metric(f"{teams[team_ids[1]]} - Pases", successful_passes_2)
    with col4:
        acc2 = (successful_passes_2 / total_passes_2 * 100) if total_passes_2 > 0 else 0
        st.metric("Precisión", f"{acc2:.1f}%")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 11), facecolor='#0e1117')
    
    plot_passing_network(positions1, connections1, teams[team_ids[0]], ax1, min_passes, team_color='red')
    plot_passing_network(positions2, connections2, teams[team_ids[1]], ax2, min_passes, team_color='orange')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    
    # TABLAS CON xT
    st.markdown("---")
    st.subheader("📊 Top 10 Combinaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{teams[team_ids[0]]}**")
        top_conn1 = sorted(connections1.items(), key=lambda x: x[1]['count'] if isinstance(x[1], dict) else x[1], reverse=True)[:10]
        
        if top_conn1:
            conn_data1 = []
            for rank, ((p1, p2), conn_info) in enumerate(top_conn1, 1):
                name1 = players_team1.get(p1, f'P{p1}')
                name2 = players_team1.get(p2, f'P{p2}')
                
                if isinstance(conn_info, dict):
                    count = conn_info['count']
                    xt = conn_info.get('xt', 0.0)
                else:
                    count = conn_info
                    xt = 0.0
                
                row = {
                    '#': rank,
                    'Combinación': f"{name1} → {name2}",
                    'Pases': count
                }
                
                if XT_AVAILABLE and xt > 0:
                    row['xT'] = f"{xt:.3f}"
                
                conn_data1.append(row)
            
            df_conn1 = pd.DataFrame(conn_data1)
            
            max_val = df_conn1['Pases'].max()
            min_val = df_conn1['Pases'].min()
            
            def color_scale(val):
                if max_val == min_val:
                    return 'background-color: #90EE90'
                ratio = (val - min_val) / (max_val - min_val)
                r = int(144 + (255 - 144) * (1 - ratio))
                g = int(238 - (238 - 107) * (1 - ratio))
                b = int(144 - (144 - 107) * (1 - ratio))
                return f'background-color: rgb({r},{g},{b})'
            
            styled = df_conn1.style.applymap(color_scale, subset=['Pases'])
            st.dataframe(styled, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ No hay conexiones suficientes")
    
    with col2:
        st.markdown(f"**{teams[team_ids[1]]}**")
        top_conn2 = sorted(connections2.items(), key=lambda x: x[1]['count'] if isinstance(x[1], dict) else x[1], reverse=True)[:10]
        
        if top_conn2:
            conn_data2 = []
            for rank, ((p1, p2), conn_info) in enumerate(top_conn2, 1):
                name1 = players_team2.get(p1, f'P{p1}')
                name2 = players_team2.get(p2, f'P{p2}')
                
                if isinstance(conn_info, dict):
                    count = conn_info['count']
                    xt = conn_info.get('xt', 0.0)
                else:
                    count = conn_info
                    xt = 0.0
                
                row = {
                    '#': rank,
                    'Combinación': f"{name1} → {name2}",
                    'Pases': count
                }
                
                if XT_AVAILABLE and xt > 0:
                    row['xT'] = f"{xt:.3f}"
                
                conn_data2.append(row)
            
            df_conn2 = pd.DataFrame(conn_data2)
            
            max_val = df_conn2['Pases'].max()
            min_val = df_conn2['Pases'].min()
            
            def color_scale(val):
                if max_val == min_val:
                    return 'background-color: #90EE90'
                ratio = (val - min_val) / (max_val - min_val)
                r = int(144 + (255 - 144) * (1 - ratio))
                g = int(238 - (238 - 107) * (1 - ratio))
                b = int(144 - (144 - 107) * (1 - ratio))
                return f'background-color: rgb({r},{g},{b})'
            
            styled = df_conn2.style.applymap(color_scale, subset=['Pases'])
            st.dataframe(styled, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ No hay conexiones suficientes")
    
    # TABLA DE JUGADORES CON xT
    st.markdown("---")
    st.subheader("🎯 Top 10 Jugadores")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{teams[team_ids[0]]}**")
        player_data1 = []
        for player_id, pos in positions1.items():
            row = {
                'Jugador': pos['name'],
                'Pases': pos['passes']
            }
            if XT_AVAILABLE:
                row['xT'] = f"{pos['xt']:.3f}"
            player_data1.append(row)
        
        if player_data1:
            df_p1 = pd.DataFrame(player_data1).sort_values('Pases', ascending=False).head(10).reset_index(drop=True)
            df_p1.insert(0, '#', range(1, len(df_p1) + 1))
            
            max_val = df_p1['Pases'].max()
            min_val = df_p1['Pases'].min()
            
            def color_scale(val):
                if max_val == min_val:
                    return 'background-color: #90EE90'
                ratio = (val - min_val) / (max_val - min_val)
                r = int(144 + (255 - 144) * (1 - ratio))
                g = int(238 - (238 - 107) * (1 - ratio))
                b = int(144 - (144 - 107) * (1 - ratio))
                return f'background-color: rgb({r},{g},{b})'
            
            styled = df_p1.style.applymap(color_scale, subset=['Pases'])
            st.dataframe(styled, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown(f"**{teams[team_ids[1]]}**")
        player_data2 = []
        for player_id, pos in positions2.items():
            row = {
                'Jugador': pos['name'],
                'Pases': pos['passes']
            }
            if XT_AVAILABLE:
                row['xT'] = f"{pos['xt']:.3f}"
            player_data2.append(row)
        
        if player_data2:
            df_p2 = pd.DataFrame(player_data2).sort_values('Pases', ascending=False).head(10).reset_index(drop=True)
            df_p2.insert(0, '#', range(1, len(df_p2) + 1))
            
            max_val = df_p2['Pases'].max()
            min_val = df_p2['Pases'].min()
            
            def color_scale(val):
                if max_val == min_val:
                    return 'background-color: #90EE90'
                ratio = (val - min_val) / (max_val - min_val)
                r = int(144 + (255 - 144) * (1 - ratio))
                g = int(238 - (238 - 107) * (1 - ratio))
                b = int(144 - (144 - 107) * (1 - ratio))
                return f'background-color: rgb({r},{g},{b})'
            
            styled = df_p2.style.applymap(color_scale, subset=['Pases'])
            st.dataframe(styled, use_container_width=True, hide_index=True)

def load_matches_metadata(raw_dir, scope='global', country=None, competition=None):
    """Carga metadata de partidos"""
    metadata_file = None
    if scope == 'global':
        metadata_file = raw_dir / 'matches_metadata.json'
    elif scope == 'country' and country:
        metadata_file = raw_dir / country / 'matches_metadata.json'
    elif scope == 'competition' and country and competition:
        metadata_file = raw_dir / country / competition / 'matches_metadata.json'
    if metadata_file and metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            if metadata:
                df = pd.DataFrame(metadata)
                df['date'] = pd.to_datetime(df['date'])
                if 'filepath' in df.columns:
                    df['filepath'] = df['filepath'].str.replace('\\', '/', regex=False)
                return df.sort_values('date', ascending=False)
        except Exception as e:
            st.error(f"Error cargando metadata: {e}")
    return None

def show_passing_network_tab():
    """Muestra la pestaña de análisis de redes de pases"""
    st.markdown("### 🕸️ Passing Network Analysis")
    st.markdown("**Comparación lado a lado con 3 variables visuales**")
    data_scan = scan_data_directories()
    raw_dir = data_scan['raw_dir']
    st.sidebar.markdown("## ⚙️ Configuración")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📤 Subir JSON Manual")
    uploaded_file = st.sidebar.file_uploader(
        "Arrastra un archivo JSON:",
        type=['json'],
        help="Sube un archivo JSON con datos OPTA / Stats Perform",
        key="manual_json_uploader"
    )
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8') as tmp:
            tmp.write(uploaded_file.getvalue().decode('utf-8'))
            tmp_path = Path(tmp.name)
        st.info(f"📄 Archivo subido: {uploaded_file.name}")
        process_json_file(tmp_path)
        return
    st.sidebar.markdown("---")
    global_metadata_file = raw_dir / 'matches_metadata.json'
    if not global_metadata_file.exists():
        st.sidebar.error("⚠️ No hay metadata")
        st.sidebar.info("Ejecuta: `python generate_metadata.py`")
        st.info("💡 Usa el uploader de arriba para cargar un JSON manualmente")
        return
    df_matches = load_matches_metadata(raw_dir, scope='global')
    if df_matches is None or len(df_matches) == 0:
        st.sidebar.error("⚠️ No hay partidos")
        st.sidebar.info("Agrega JSONs y ejecuta: `python generate_metadata.py`")
        return
    st.sidebar.markdown("### 🏆 Competición")
    competitions_list = sorted(df_matches['competition_full_name'].unique().tolist())
    selected_competition = st.sidebar.selectbox("Liga:", competitions_list, label_visibility="collapsed")
    filtered_df = df_matches[df_matches['competition_full_name'] == selected_competition].copy()
    st.sidebar.markdown("### 📅 Temporada")
    seasons = sorted(filtered_df['season'].unique().tolist(), reverse=True)
    selected_season = st.sidebar.selectbox("Season:", seasons, label_visibility="collapsed")
    filtered_df = filtered_df[filtered_df['season'] == selected_season]
    st.sidebar.markdown("### ⚽ Equipo")
    all_teams = set()
    for desc in filtered_df['description'].unique():
        teams = desc.split(' vs ')
        all_teams.update(teams)
    teams_list = ['Todos'] + sorted(list(all_teams))
    selected_team = st.sidebar.selectbox("Team:", teams_list, label_visibility="collapsed")
    if selected_team != 'Todos':
        filtered_df = filtered_df[filtered_df['description'].str.contains(selected_team, case=False, na=False)]
    st.sidebar.markdown("### 🎯 Tipo de Partido")
    match_type = st.sidebar.radio("Match type:", ["Partido más reciente", "Partido específico"], label_visibility="collapsed")
    st.sidebar.markdown("---")
    st.sidebar.metric("Partidos encontrados", len(filtered_df))
    if len(filtered_df) == 0:
        st.warning("⚠️ No se encontraron partidos con los filtros aplicados")
        return
    selected_match = None
    if match_type == "Partido más reciente":
        selected_match = filtered_df.iloc[0]
        st.info(f"📅 **Partido más reciente:** {selected_match['description']} ({selected_match['date'].strftime('%d/%m/%Y')})")
    else:
        st.markdown("#### 📋 Selecciona el partido:")
        match_options = {}
        for idx, row in filtered_df.iterrows():
            date_str = row['date'].strftime('%d/%m/%Y')
            code = row['competition_code'] if row['competition_code'] else row['competition'][:3].upper()
            stage = f" | {row['stage']}" if row['stage'] else ''
            display_name = f"📅 {date_str} | {code}{stage} | {row['description']}"
            match_options[display_name] = row
        selected_display = st.selectbox("Partido:", list(match_options.keys()), label_visibility="collapsed")
        selected_match = match_options[selected_display]
    if selected_match is not None:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.info(f"🌎 {selected_match['country']}")
        with col2:
            st.info(f"📅 {selected_match['date'].strftime('%d/%m/%Y')}")
        with col3:
            st.info(f"⏰ {selected_match['time']}")
        with col4:
            code = selected_match['competition_code'] if selected_match['competition_code'] else selected_match['competition'][:3]
            st.info(f"🏆 {code}")
        with col5:
            st.info(f"📊 {selected_match['season']}")
        st.markdown("---")
        selected_file = raw_dir / selected_match['filepath']
        if selected_file.exists():
            process_json_file(selected_file)
        else:
            st.error(f"❌ Archivo no encontrado: {selected_file}")