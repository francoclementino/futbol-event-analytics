# passing_network_tab.py
# Módulo de análisis de redes de pases con procesamiento integrado
import streamlit as st
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import numpy as np
import sys

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
    
    # Buscar archivos
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

def load_match_data(f24_path):
    """Carga datos del archivo F24 JSON"""
    try:
        with open(f24_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
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

def extract_passes(match_data, team_id, period=None):
    """Extrae todos los pases de un equipo específico"""
    passes = []
    
    for event in match_data.get('Event', []):
        if event.get('type_id') != 1:  # Solo pases
            continue
            
        if str(event.get('team_id')) != str(team_id):
            continue
        
        if period and int(event.get('period_id', 0)) != period:
            continue
        
        # Obtener coordenadas
        x = float(event.get('x', 0))
        y = float(event.get('y', 0))
        
        # Buscar coordenadas finales en qualifiers
        end_x, end_y = None, None
        for q in event.get('qualifier', []):
            if q.get('qualifier_id') == 140:
                end_x = float(q.get('value', 0))
            elif q.get('qualifier_id') == 141:
                end_y = float(q.get('value', 0))
        
        # Resultado del pase
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

def get_player_names(match_data, team_id):
    """Extrae nombres de jugadores de un equipo"""
    players = {}
    
    for event in match_data.get('Event', []):
        if str(event.get('team_id')) != str(team_id):
            continue
        
        player_id = event.get('player_id')
        player_name = event.get('player_name', f'Player {player_id}')
        
        if player_id and player_name:
            players[player_id] = player_name
    
    return players

def get_team_names(match_data):
    """Extrae nombres de equipos del match"""
    teams = {}
    
    for event in match_data.get('Event', []):
        team_id = str(event.get('team_id'))
        team_name = event.get('team_name', f'Team {team_id}')
        
        if team_id not in teams:
            teams[team_id] = team_name
    
    return teams

def calculate_pass_network_positions(passes, player_names):
    """Calcula posiciones promedio y conexiones entre jugadores"""
    # Agrupar pases por jugador
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
    
    # Calcular promedios
    avg_positions = {}
    for player_id, positions in player_positions.items():
        avg_positions[player_id] = {
            'x': np.mean(positions['x']),
            'y': np.mean(positions['y']),
            'name': player_names.get(player_id, f'Player {player_id}'),
            'passes': player_pass_counts.get(player_id, 0)
        }
    
    # Calcular conexiones (simplificado para esta versión)
    for i, pass_event in enumerate(passes):
        if not pass_event['outcome'] or not pass_event['end_x']:
            continue
        
        passer = pass_event['player_id']
        
        # Buscar receptor aproximado por posición
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
    
    # Escalar coordenadas OPTA (100x100) a dimensiones reales (105x68)
    scale_x = 105 / 100
    scale_y = 68 / 100
    
    # Dibujar conexiones
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
    
    # Dibujar jugadores
    for player_id, pos in avg_positions.items():
        x = pos['x'] * scale_x
        y = pos['y'] * scale_y
        passes = pos['passes']
        
        size = max(100, passes * 10)
        
        ax.scatter(x, y, s=size, c='gold', edgecolors='white', 
                  linewidths=2, zorder=2, marker='h')
        
        # Etiqueta con nombre
        name_parts = pos['name'].split()
        short_name = name_parts[-1] if name_parts else pos['name']
        
        ax.text(x, y - 3, short_name, fontsize=8, color='white',
               ha='center', va='top', weight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
    
    ax.set_title(f'{team_name} - Passing Network', fontsize=14, weight='bold', color='white')
    ax.axis('off')

def show_passing_network_tab():
    """Muestra la pestaña de análisis de redes de pases"""
    
    st.markdown("### 🕸️ Passing Network Analysis")
    st.markdown("**Comparación lado a lado de ambos equipos**")
    
    # Escanear carpetas
    data_scan = scan_data_directories()
    
    # Verificar si hay datos
    if not data_scan['json_files'] and not data_scan['parquet_files']:
        st.error("❌ No se encuentra el directorio 'data'")
        st.info("💡 Crea una carpeta 'data' y coloca tus archivos F24 JSON")
        
        # Mostrar rutas esperadas
        with st.expander("📁 Estructura de carpetas esperada"):
            st.code("""
futbol-event-analytics/
├── data/
│   ├── raw/           ← Coloca aquí tus archivos JSON F24
│   └── processed/     ← Aquí se guardarán los Parquet procesados
└── app.py
            """)
        return
    
    # Modo de selección
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        data_mode = st.radio(
            "📂 Tipo de datos:",
            ["Parquet Procesados", "JSON Crudos (F24)"],
            help="Selecciona si quieres cargar datos ya procesados o archivos JSON crudos"
        )
    
    with col2:
        if data_mode == "JSON Crudos (F24)":
            st.info(f"📊 {len(data_scan['json_files'])} archivos JSON disponibles")
        else:
            st.info(f"📦 {len(data_scan['parquet_files'])} archivos Parquet disponibles")
    
    # Selección de archivo
    if data_mode == "Parquet Procesados":
        if not data_scan['parquet_files']:
            st.warning("⚠️ No hay archivos Parquet procesados. Usa 'JSON Crudos' primero.")
            return
        
        # Crear nombres amigables para los parquets
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
            
            # Cargar datos
            with st.spinner('Cargando datos...'):
                df = load_parquet_data(selected_file)
            
            if df is not None:
                st.success(f"✅ Cargados {len(df):,} eventos")
                
                # Filtros para Parquet (implementar análisis completo después)
                st.info("🚧 Análisis de Parquet en desarrollo. Por ahora, usa 'JSON Crudos' para redes de pases.")
    
    else:  # JSON Crudos
        if not data_scan['json_files']:
            st.warning("⚠️ No hay archivos JSON en data/raw/")
            return
        
        # Crear nombres amigables para JSON
        json_options = {f.name: f for f in data_scan['json_files']}
        
        selected_name = st.selectbox(
            "Selecciona archivo F24 JSON:",
            list(json_options.keys())
        )
        
        if selected_name:
            selected_file = json_options[selected_name]
            
            # Cargar datos
            with st.spinner('Cargando match data...'):
                match_data = load_match_data(selected_file)
            
            if match_data is not None:
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
