# passing_network_tab.py - VERSIÓN MEJORADA
# Módulo de análisis de redes de pases con soporte multi-formato y file uploader SIEMPRE VISIBLE
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

def extract_passes(match_obj, team_id, period=None, time_range=None):
    """Extrae todos los pases de un equipo específico - soporta múltiples formatos"""
    
    if match_obj is None:
        return []
    
    format_type = match_obj.get('format', 'unknown')
    match_data = match_obj.get('data', {})
    
    if format_type == 'stats_perform':
        return extract_passes_stats_perform(match_data, team_id, period, time_range)
    elif format_type == 'f24':
        return extract_passes_f24(match_data, team_id, period)
    else:
        st.error(f"❌ Formato '{format_type}' no soportado para extracción de pases")
        return []

def extract_passes_stats_perform(match_data, team_id, period=None, time_range=None):
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
        
        # Filtro por rango de minutos
        if time_range:
            event_min = int(event.get('timeMin', 0))
            if period == 2:  # Segundo tiempo
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
        
        # FIX CRÍTICO: usar 'outcome' NO 'outcomeType'
        outcome = event.get('outcome', 0)
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
    
    # Extraer nombres directamente de los eventos (más confiable)
    if 'liveData' in match_data and 'event' in match_data['liveData']:
        for event in match_data['liveData']['event']:
            if str(event.get('contestantId')) != str(team_id):
                continue
            
            player_id = event.get('playerId')
            player_name = event.get('playerName')
            
            if player_id and player_name and player_id not in players:
                players[player_id] = player_name
    
    # Si no se encontraron nombres en eventos, intentar desde lineup
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

def get_player_short_name(full_name):
    """
    Convierte nombre completo a formato con inicial.
    Ejemplos:
    - "Lionel Messi" -> "L. Messi"
    - "Castro" -> "Castro"
    - "Juan Manuel García" -> "J. García"
    """
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
    """Calcula posiciones promedio y conexiones entre jugadores usando método mplsoccer"""
    import pandas as pd
    
    if not passes:
        return {}, {}
    
    # Convertir a DataFrame para facilitar procesamiento
    df = pd.DataFrame(passes)
    
    # Aplicar inversión de coordenadas si es necesario
    if invert_coords:
        df['x'] = 100 - df['x']
        df['y'] = 100 - df['y']
        df.loc[df['end_x'].notnull(), 'end_x'] = 100 - df.loc[df['end_x'].notnull(), 'end_x']
        df.loc[df['end_y'].notnull(), 'end_y'] = 100 - df.loc[df['end_y'].notnull(), 'end_y']
    
    # Calcular posiciones promedio por jugador
    avg_locs = df.groupby('player_id').agg({
        'x': 'mean',
        'y': 'mean'
    })
    
    # Contar pases exitosos por jugador
    pass_counts = df[df['outcome'] == True].groupby('player_id').size()
    
    # Construir diccionario de posiciones
    avg_positions = {}
    for player_id in avg_locs.index:
        avg_positions[player_id] = {
            'x': avg_locs.loc[player_id, 'x'],
            'y': avg_locs.loc[player_id, 'y'],
            'name': player_names.get(player_id, f'Player {player_id}'),
            'passes': int(pass_counts.get(player_id, 0))
        }
    
    # Calcular conexiones usando el método de mplsoccer:
    # Para cada pase exitoso, el receptor es el jugador en la posición final
    connections = {}
    
    # Filtrar solo pases exitosos con coordenadas finales
    successful_passes = df[
        (df['outcome'] == True) & 
        (df['end_x'].notnull()) & 
        (df['end_y'].notnull())
    ].copy()
    
    if len(successful_passes) == 0:
        return avg_positions, connections
    
    # Para cada pase exitoso, encontrar el jugador más cercano a las coordenadas finales
    for idx, pass_row in successful_passes.iterrows():
        passer_id = pass_row['player_id']
        end_x = pass_row['end_x']
        end_y = pass_row['end_y']
        
        # Buscar el jugador más cercano a las coordenadas finales
        min_distance = float('inf')
        receiver_id = None
        
        for player_id, pos in avg_positions.items():
            if player_id == passer_id:
                continue
            
            # Distancia euclidiana entre coordenadas finales y posición promedio del jugador
            distance = ((pos['x'] - end_x)**2 + (pos['y'] - end_y)**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
                receiver_id = player_id
        
        # Solo agregar conexión si encontramos un receptor razonablemente cercano
        if receiver_id and min_distance < 25:  # Umbral de 25 unidades
            key = (passer_id, receiver_id)
            connections[key] = connections.get(key, 0) + 1
    
    return avg_positions, connections

def plot_passing_network(avg_positions, connections, team_name, ax, min_passes=3, team_color='cyan'):
    """Visualiza la red de pases en una cancha"""
    pitch = Pitch(pitch_type='custom', pitch_length=105, pitch_width=68,
                  line_color='white', pitch_color='#0a3d0a', linewidth=2)
    pitch.draw(ax=ax)
    
    scale_x = 105 / 100
    scale_y = 68 / 100
    
    # Colores por equipo - NUEVO: Rojo para team 1
    if team_color == 'red':
        node_color = '#e74c3c'  # Rojo vibrante
        line_color = '#e74c3c'
    elif team_color == 'cyan':
        node_color = '#00d9ff'
        line_color = '#00d9ff'
    else:  # orange
        node_color = '#ff9500'
        line_color = '#ff9500'
    
    # Dibujar conexiones primero (para que queden debajo de los nodos)
    connections_drawn = 0
    for (passer, receiver), count in connections.items():
        if count < min_passes:
            continue
        
        if passer in avg_positions and receiver in avg_positions:
            x1 = avg_positions[passer]['x'] * scale_x
            y1 = avg_positions[passer]['y'] * scale_y
            x2 = avg_positions[receiver]['x'] * scale_x
            y2 = avg_positions[receiver]['y'] * scale_y
            
            # Grosor muy visible proporcional al número de pases (estilo The Athletic)
            width = max(2, min(count / 1.2, 12))  # Entre 2 y 12 (más ancho)
            alpha = min(0.95, 0.4 + (count / 15))  # Entre 0.4 y 0.95
            
            ax.plot([x1, x2], [y1, y2], 
                   color=line_color, linewidth=width, alpha=alpha, zorder=1,
                   solid_capstyle='round')
            connections_drawn += 1
    
    # DEBUG: Mostrar cantidad de conexiones dibujadas
    if connections_drawn == 0:
        ax.text(52.5, 5, f'No hay conexiones con min_passes={min_passes}', 
               fontsize=10, color='yellow', ha='center', weight='bold',
               bbox=dict(boxstyle='round', facecolor='red', alpha=0.7))
    
    # Calcular tamaño máximo de pases para escalar (estilo The Athletic)
    max_passes = max([pos['passes'] for pos in avg_positions.values()]) if avg_positions else 1
    
    # Dibujar jugadores encima
    for player_id, pos in avg_positions.items():
        x = pos['x'] * scale_x
        y = pos['y'] * scale_y
        passes = pos['passes']
        
        # Tamaño MUY proporcional a los pases (estilo The Athletic)
        # El jugador con más pases tendrá el círculo más grande
        size = max(400, min((passes / max_passes) * 2000, 2500))
        
        # Círculos de color con borde blanco (estilo The Athletic)
        ax.scatter(x, y, s=size, c=node_color, edgecolors='white', 
                  linewidths=3, zorder=2, marker='o', alpha=0.95)
        
        # Nombre del jugador con inicial
        short_name = get_player_short_name(pos['name'])
        
        # Limitar longitud del nombre
        if len(short_name) > 10:
            short_name = short_name[:10]
        
        # NUEVO: Texto arriba o abajo según posición Y
        # Si está en la mitad superior (y > 34), texto abajo
        # Si está en la mitad inferior (y <= 34), texto arriba
        if y > 34:  # Mitad superior
            text_y = y - 4  # Texto abajo del círculo
            va = 'top'
        else:  # Mitad inferior
            text_y = y + 4  # Texto arriba del círculo
            va = 'bottom'
        
        # Texto BLANCO con borde negro (estilo The Athletic)
        import matplotlib.patheffects as path_effects
        text = ax.text(x, text_y, short_name, fontsize=10, color='white',
                      ha='center', va=va, weight='bold', zorder=3)
        text.set_path_effects([
            path_effects.Stroke(linewidth=2, foreground='black'),
            path_effects.Normal()
        ])
    
    ax.set_title(f'{team_name} - Passing Network', 
                fontsize=16, weight='bold', color='white', pad=15)
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
        # Calcular duración máxima del partido
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
    
    # Slider de rango de minutos (solo si está activado)
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
    
    # Procesar y visualizar
    st.markdown("---")
    
    # Extraer datos de ambos equipos
    passes_team1 = extract_passes(match_data, team_ids[0], period, time_range)
    passes_team2 = extract_passes(match_data, team_ids[1], period, time_range)
    
    # DEBUG: Verificar si hay pases
    if not passes_team1 and not passes_team2:
        st.error("❌ No se encontraron pases en el rango seleccionado")
        st.info("💡 Intenta ajustar los filtros (período o rango de minutos)")
        return
    
    players_team1 = get_player_names(match_data, team_ids[0])
    players_team2 = get_player_names(match_data, team_ids[1])
    
    # Calcular redes
    # Team 1: izquierda a derecha (normal)
    # Team 2: derecha a izquierda (invertir coordenadas)
    positions1, connections1 = calculate_pass_network_positions(passes_team1, players_team1, invert_coords=False)
    positions2, connections2 = calculate_pass_network_positions(passes_team2, players_team2, invert_coords=True)
    
    # Métricas comparativas
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
    
    # Visualización lado a lado
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10), facecolor='#0e1117')
    
    # Team 1: ROJO (ataca de izquierda a derecha)
    plot_passing_network(positions1, connections1, teams[team_ids[0]], ax1, min_passes, team_color='red')
    
    # Team 2: Orange (ataca de derecha a izquierda, coordenadas ya invertidas)
    plot_passing_network(positions2, connections2, teams[team_ids[1]], ax2, min_passes, team_color='orange')
    
    st.pyplot(fig)
    plt.close()
    
    # ====================
    # TABLAS DE COMBINACIONES CON FORMATO CONDICIONAL
    # ====================
    st.markdown("---")
    st.subheader("📊 Top 10 Combinaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{teams[team_ids[0]]}**")
        top_conn1 = sorted(connections1.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_conn1:
            conn_data1 = []
            for rank, ((p1, p2), count) in enumerate(top_conn1, 1):
                name1 = players_team1.get(p1, f'P{p1}')
                name2 = players_team1.get(p2, f'P{p2}')
                conn_data1.append({
                    '#': rank,
                    'Combinación': f"{name1} → {name2}",
                    'Pases': count
                })
            
            df_conn1 = pd.DataFrame(conn_data1)
            
            # NUEVO: Formato condicional verde→rojo
            max_val = df_conn1['Pases'].max()
            min_val = df_conn1['Pases'].min()
            
            def color_scale_conn(val):
                if max_val == min_val:
                    return 'background-color: #90EE90'
                # Escala de verde (#90EE90) a rojo (#FF6B6B)
                ratio = (val - min_val) / (max_val - min_val)
                r = int(144 + (255 - 144) * (1 - ratio))
                g = int(238 - (238 - 107) * (1 - ratio))
                b = int(144 - (144 - 107) * (1 - ratio))
                return f'background-color: rgb({r},{g},{b})'
            
            styled_conn1 = df_conn1.style.applymap(color_scale_conn, subset=['Pases'])
            st.dataframe(
                styled_conn1,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("⚠️ No hay conexiones suficientes para mostrar")
    
    with col2:
        st.markdown(f"**{teams[team_ids[1]]}**")
        top_conn2 = sorted(connections2.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_conn2:
            conn_data2 = []
            for rank, ((p1, p2), count) in enumerate(top_conn2, 1):
                name1 = players_team2.get(p1, f'P{p1}')
                name2 = players_team2.get(p2, f'P{p2}')
                conn_data2.append({
                    '#': rank,
                    'Combinación': f"{name1} → {name2}",
                    'Pases': count
                })
            
            df_conn2 = pd.DataFrame(conn_data2)
            
            # NUEVO: Formato condicional verde→rojo
            max_val = df_conn2['Pases'].max()
            min_val = df_conn2['Pases'].min()
            
            def color_scale_conn(val):
                if max_val == min_val:
                    return 'background-color: #90EE90'
                ratio = (val - min_val) / (max_val - min_val)
                r = int(144 + (255 - 144) * (1 - ratio))
                g = int(238 - (238 - 107) * (1 - ratio))
                b = int(144 - (144 - 107) * (1 - ratio))
                return f'background-color: rgb({r},{g},{b})'
            
            styled_conn2 = df_conn2.style.applymap(color_scale_conn, subset=['Pases'])
            st.dataframe(
                styled_conn2,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("⚠️ No hay conexiones suficientes para mostrar")
    
    # ====================
    # TABLAS DE PASES INDIVIDUALES CON FORMATO CONDICIONAL
    # ====================
    st.markdown("---")
    st.subheader("🎯 Top 10 Jugadores por Pases")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{teams[team_ids[0]]}**")
        
        # Extraer pases por jugador
        player_pass_data1 = []
        for player_id, pos in positions1.items():
            player_pass_data1.append({
                'Jugador': pos['name'],
                'Pases': pos['passes']
            })
        
        if player_pass_data1:
            df_passes1 = pd.DataFrame(player_pass_data1)
            df_passes1 = df_passes1.sort_values('Pases', ascending=False).head(10).reset_index(drop=True)
            df_passes1.insert(0, '#', range(1, len(df_passes1) + 1))
            
            # Formato condicional: verde (máximo) a rojo (mínimo)
            max_val = df_passes1['Pases'].max()
            min_val = df_passes1['Pases'].min()
            
            def color_scale(val):
                if max_val == min_val:
                    return 'background-color: #90EE90'
                # Escala de verde (#90EE90) a rojo (#FF6B6B)
                ratio = (val - min_val) / (max_val - min_val)
                r = int(144 + (255 - 144) * (1 - ratio))
                g = int(238 - (238 - 107) * (1 - ratio))
                b = int(144 - (144 - 107) * (1 - ratio))
                return f'background-color: rgb({r},{g},{b})'
            
            styled_df1 = df_passes1.style.applymap(color_scale, subset=['Pases'])
            st.dataframe(
                styled_df1,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("⚠️ No hay datos de pases")
    
    with col2:
        st.markdown(f"**{teams[team_ids[1]]}**")
        
        # Extraer pases por jugador
        player_pass_data2 = []
        for player_id, pos in positions2.items():
            player_pass_data2.append({
                'Jugador': pos['name'],
                'Pases': pos['passes']
            })
        
        if player_pass_data2:
            df_passes2 = pd.DataFrame(player_pass_data2)
            df_passes2 = df_passes2.sort_values('Pases', ascending=False).head(10).reset_index(drop=True)
            df_passes2.insert(0, '#', range(1, len(df_passes2) + 1))
            
            # Formato condicional: verde (máximo) a rojo (mínimo)
            max_val = df_passes2['Pases'].max()
            min_val = df_passes2['Pases'].min()
            
            def color_scale(val):
                if max_val == min_val:
                    return 'background-color: #90EE90'
                ratio = (val - min_val) / (max_val - min_val)
                r = int(144 + (255 - 144) * (1 - ratio))
                g = int(238 - (238 - 107) * (1 - ratio))
                b = int(144 - (144 - 107) * (1 - ratio))
                return f'background-color: rgb({r},{g},{b})'
            
            styled_df2 = df_passes2.style.applymap(color_scale, subset=['Pases'])
            st.dataframe(
                styled_df2,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("⚠️ No hay datos de pases")


def load_matches_metadata(raw_dir, scope='global', country=None, competition=None):
    """
    Carga metadata de partidos según el nivel de scope solicitado.
    
    CORRECCIÓN: Normaliza todos los paths a formato Unix (/)
    
    Args:
        raw_dir: Ruta base de data/raw
        scope: 'global', 'country', o 'competition'
        country: Nombre del país (requerido si scope='country' o 'competition')
        competition: Nombre de la competición (requerido si scope='competition')
    
    Returns:
        DataFrame con metadata de partidos o None si no existe
    """
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
                
                # CORRECCIÓN CRÍTICA: Normalizar paths a Unix format
                if 'filepath' in df.columns:
                    df['filepath'] = df['filepath'].str.replace('\\', '/', regex=False)
                
                return df.sort_values('date', ascending=False)
        except Exception as e:
            st.error(f"Error cargando metadata: {e}")
    
    return None

def show_passing_network_tab():
    """Muestra la pestaña de análisis de redes de pases con sidebar"""
    
    st.markdown("### 🕸️ Passing Network Analysis")
    st.markdown("**Comparación lado a lado de ambos equipos**")
    
    # Escanear carpetas
    data_scan = scan_data_directories()
    raw_dir = data_scan['raw_dir']
    
    # ========================================
    # SIDEBAR - PANEL LATERAL
    # ========================================
    st.sidebar.markdown("## ⚙️ Configuración")
    st.sidebar.markdown("---")
    
    # ========================================
    # FILE UPLOADER SIEMPRE VISIBLE
    # ========================================
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
    
    # Verificar si existe metadata global
    global_metadata_file = raw_dir / 'matches_metadata.json'
    
    if not global_metadata_file.exists():
        st.sidebar.error("⚠️ No hay metadata")
        st.sidebar.info("Ejecuta: `python generate_metadata.py`")
        st.info("💡 Usa el uploader de arriba para cargar un JSON manualmente")
        return
    
    # Cargar metadata global
    df_matches = load_matches_metadata(raw_dir, scope='global')
    
    if df_matches is None or len(df_matches) == 0:
        st.sidebar.error("⚠️ No hay partidos")
        st.sidebar.info("Agrega JSONs y ejecuta: `python generate_metadata.py`")
        return
    
    # ========================================
    # FILTROS EN SIDEBAR
    # ========================================
    
    # 1. COMPETICIÓN / LIGA
    st.sidebar.markdown("### 🏆 Competición")
    competitions_list = sorted(df_matches['competition_full_name'].unique().tolist())
    selected_competition = st.sidebar.selectbox(
        "Liga:",
        competitions_list,
        label_visibility="collapsed"
    )
    
    # Filtrar por competición seleccionada
    filtered_df = df_matches[df_matches['competition_full_name'] == selected_competition].copy()
    
    # 2. TEMPORADA
    st.sidebar.markdown("### 📅 Temporada")
    seasons = sorted(filtered_df['season'].unique().tolist(), reverse=True)
    selected_season = st.sidebar.selectbox(
        "Season:",
        seasons,
        label_visibility="collapsed"
    )
    
    # Filtrar por temporada
    filtered_df = filtered_df[filtered_df['season'] == selected_season]
    
    # 3. EQUIPO
    st.sidebar.markdown("### ⚽ Equipo")
    
    # Extraer equipos únicos de las descripciones
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
    
    # Filtrar por equipo si no es "Todos"
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
    
    # Mostrar contador de partidos encontrados
    st.sidebar.metric("Partidos encontrados", len(filtered_df))
    
    # ========================================
    # SELECCIÓN DE PARTIDO
    # ========================================
    
    if len(filtered_df) == 0:
        st.warning("⚠️ No se encontraron partidos con los filtros aplicados")
        return
    
    selected_match = None
    
    if match_type == "Partido más reciente":
        # Seleccionar automáticamente el más reciente
        selected_match = filtered_df.iloc[0]
        
        st.info(f"📅 **Partido más reciente:** {selected_match['description']} ({selected_match['date'].strftime('%d/%m/%Y')})")
    
    else:
        # Mostrar dropdown con todos los partidos
        st.markdown("#### 📋 Selecciona el partido:")
        
        match_options = {}
        for idx, row in filtered_df.iterrows():
            date_str = row['date'].strftime('%d/%m/%Y')
            code = row['competition_code'] if row['competition_code'] else row['competition'][:3].upper()
            stage = f" | {row['stage']}" if row['stage'] else ''
            
            display_name = f"📅 {date_str} | {code}{stage} | {row['description']}"
            match_options[display_name] = row
        
        selected_display = st.selectbox(
            "Partido:",
            list(match_options.keys()),
            label_visibility="collapsed"
        )
        
        selected_match = match_options[selected_display]
    
    # ========================================
    # MOSTRAR INFO DEL PARTIDO
    # ========================================
    
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
        
        # Procesar el partido seleccionado
        selected_file = raw_dir / selected_match['filepath']
        
        if selected_file.exists():
            process_json_file(selected_file)
        else:
            st.error(f"❌ Archivo no encontrado: {selected_file}")