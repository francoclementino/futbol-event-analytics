# passing_network_tab.py
import streamlit as st
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import numpy as np

def load_match_data(f24_path):
    """Carga datos del archivo F24 JSON"""
    try:
        with open(f24_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Error cargando archivo: {e}")
        return None

def extract_passes(match_data, team_id, period=None):
    """Extrae todos los pases de un equipo específico"""
    passes = []
    
    for event in match_data.get('Event', []):
        if event.get('type_id') != 1:  # Solo pases
            continue
            
        if str(event.get('team_id')) != str(team_id):
            continue
        
        if period and event.get('period_id') != period:
            continue
        
        player_id = event.get('player_id')
        x = float(event.get('x', 0))
        y = float(event.get('y', 0))
        outcome = event.get('outcome', 0)
        
        # Buscar receptor (qualifier 140)
        recipient_id = None
        for qualifier in event.get('qualifier', []):
            if qualifier.get('qualifier_id') == 140:
                recipient_id = qualifier.get('value')
                break
        
        if recipient_id:
            passes.append({
                'player_id': player_id,
                'recipient_id': recipient_id,
                'x': x,
                'y': y,
                'outcome': outcome
            })
    
    return pd.DataFrame(passes)

def get_player_names(match_data):
    """Extrae diccionario de player_id -> nombre"""
    players = {}
    
    if 'TeamData' in match_data:
        for team in match_data['TeamData']:
            for player in team.get('PlayerLineUp', {}).get('MatchPlayer', []):
                player_id = player.get('PlayerRef')
                # Intentar obtener apellido primero
                last_name = player.get('PersonName', {}).get('Last', '')
                shirt_name = player.get('ShirtName', '')
                name = last_name if last_name else (shirt_name if shirt_name else f"Player {player_id}")
                players[player_id] = name
    
    # Backup desde eventos
    for event in match_data.get('Event', []):
        player_id = event.get('player_id')
        if player_id and player_id not in players:
            players[player_id] = f"Player {player_id}"
    
    return players

def get_team_names(match_data):
    """Extrae nombres de los equipos"""
    teams = {}
    
    if 'TeamData' in match_data:
        for team in match_data['TeamData']:
            team_id = team.get('TeamRef')
            team_name = team.get('Name', f'Team {team_id}')
            teams[team_id] = team_name
    
    return teams

def calculate_pass_network_positions(passes_df, player_names):
    """Calcula posiciones promedio y conexiones"""
    
    # Posiciones promedio
    player_stats = passes_df.groupby('player_id').agg({
        'x': 'mean',
        'y': 'mean',
        'player_id': 'count'
    }).reset_index(drop=True)
    
    player_stats.columns = ['avg_x', 'avg_y', 'passes_made']
    player_ids = passes_df.groupby('player_id').size().index.tolist()
    player_stats['player_id'] = player_ids
    player_stats['name'] = player_stats['player_id'].map(player_names)
    
    # Conexiones
    pass_connections = passes_df.groupby(['player_id', 'recipient_id']).size().reset_index(name='pass_count')
    pass_connections = pass_connections.sort_values('pass_count', ascending=False)
    
    return player_stats, pass_connections

def plot_passing_network(player_positions, pass_connections, player_names, team_name, min_passes=2, ax=None):
    """Crea visualización de red de pases en un eje específico"""
    
    # Crear pitch
    pitch = Pitch(
        pitch_type='opta',
        pitch_color='#1e3a5f',
        line_color='white',
        linewidth=1.5
    )
    
    if ax is None:
        fig, ax = pitch.draw(figsize=(10, 7))
    else:
        pitch.draw(ax=ax)
    
    # Filtrar conexiones
    pass_connections_filtered = pass_connections[pass_connections['pass_count'] >= min_passes].copy()
    
    # Dibujar líneas de pases
    if len(pass_connections_filtered) > 0:
        for _, row in pass_connections_filtered.iterrows():
            passer = row['player_id']
            receiver = row['recipient_id']
            count = row['pass_count']
            
            passer_pos = player_positions[player_positions['player_id'] == passer]
            receiver_pos = player_positions[player_positions['player_id'] == receiver]
            
            if len(passer_pos) > 0 and len(receiver_pos) > 0:
                x1, y1 = passer_pos.iloc[0][['avg_x', 'avg_y']]
                x2, y2 = receiver_pos.iloc[0][['avg_x', 'avg_y']]
                
                # Ancho proporcional
                line_width = np.interp(count, 
                                       [pass_connections_filtered['pass_count'].min(), 
                                        pass_connections_filtered['pass_count'].max()],
                                       [1, 8])
                
                alpha = np.interp(count,
                                 [pass_connections_filtered['pass_count'].min(),
                                  pass_connections_filtered['pass_count'].max()],
                                 [0.3, 0.8])
                
                pitch.lines(x1, y1, x2, y2,
                           lw=line_width,
                           color='white',
                           alpha=alpha,
                           ax=ax,
                           zorder=1)
    
    # Dibujar nodos
    for _, player in player_positions.iterrows():
        node_size = np.interp(player['passes_made'],
                             [player_positions['passes_made'].min(),
                              player_positions['passes_made'].max()],
                             [300, 1200])
        
        pitch.scatter(player['avg_x'], player['avg_y'],
                     s=node_size,
                     color='white',
                     edgecolors='#4a90e2',
                     linewidth=2.5,
                     alpha=0.9,
                     ax=ax,
                     zorder=2,
                     marker='h')
        
        # Nombre
        name = str(player['name'])
        if len(name.split()) > 1:
            parts = name.split()
            short_name = f"{parts[0][0]}. {parts[-1]}"
        else:
            short_name = name[:10]
        
        ax.text(player['avg_x'], player['avg_y'],
               short_name,
               ha='center',
               va='center',
               fontsize=8,
               fontweight='bold',
               color='#1e3a5f',
               zorder=3)
    
    # Título
    ax.set_title(team_name,
                fontsize=14,
                color='white',
                pad=15,
                fontweight='bold')
    
    return ax

def show_passing_network_tab():
    """Pestaña principal - COMPARACIÓN POR DEFECTO"""
    
    st.header("🕸️ Passing Network Analysis")
    st.markdown("**Comparación lado a lado de ambos equipos**")
    
    # Selector de archivo
    data_dir = Path("data")
    if not data_dir.exists():
        st.error("❌ No se encuentra el directorio 'data'")
        st.info("💡 Crea una carpeta 'data' en la raíz del proyecto")
        return
    
    f24_files = list(data_dir.glob("*f24*.json")) + list(data_dir.glob("*F24*.json"))
    
    if not f24_files:
        st.warning("⚠️ No se encontraron archivos F24 JSON en el directorio 'data'")
        st.info("💡 Coloca tus archivos F24 JSON en la carpeta 'data'")
        return
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_file = st.selectbox(
            "📁 Seleccionar partido",
            f24_files,
            format_func=lambda x: x.stem
        )
    
    # Cargar datos
    if selected_file:
        match_data = load_match_data(selected_file)
        
        if match_data:
            player_names = get_player_names(match_data)
            team_names = get_team_names(match_data)
            
            # Obtener equipos
            teams = set()
            for event in match_data.get('Event', []):
                teams.add(event.get('team_id'))
            
            teams = sorted(list(teams))
            
            if len(teams) < 2:
                st.error("❌ No se encontraron 2 equipos en este archivo")
                return
            
            with col2:
                period = st.selectbox(
                    "⏱️ Periodo",
                    [None, 1, 2],
                    format_func=lambda x: "Partido completo" if x is None else f"{x}° Tiempo"
                )
            
            with col3:
                min_passes = st.slider(
                    "🔗 Mín. pases",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Número mínimo de pases para mostrar la conexión"
                )
            
            # Procesar ambos equipos
            team1_id = teams[0]
            team2_id = teams[1]
            
            team1_name = team_names.get(team1_id, f'Equipo {team1_id}')
            team2_name = team_names.get(team2_id, f'Equipo {team2_id}')
            
            # Extraer pases
            passes_team1 = extract_passes(match_data, team1_id, period)
            passes_team2 = extract_passes(match_data, team2_id, period)
            
            if len(passes_team1) == 0 or len(passes_team2) == 0:
                st.warning("⚠️ No hay suficientes datos de pases para uno o ambos equipos")
                return
            
            # Calcular redes
            player_pos_t1, pass_conn_t1 = calculate_pass_network_positions(passes_team1, player_names)
            player_pos_t2, pass_conn_t2 = calculate_pass_network_positions(passes_team2, player_names)
            
            # Estadísticas comparativas
            st.subheader("📊 Comparación de Estadísticas")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(f"{team1_name} - Pases", len(passes_team1))
                st.metric(f"{team2_name} - Pases", len(passes_team2))
            
            with col2:
                acc1 = (passes_team1['outcome'] == 1).sum() / len(passes_team1) * 100
                acc2 = (passes_team2['outcome'] == 1).sum() / len(passes_team2) * 100
                st.metric(f"{team1_name} - Precisión", f"{acc1:.1f}%")
                st.metric(f"{team2_name} - Precisión", f"{acc2:.1f}%")
            
            with col3:
                st.metric(f"{team1_name} - Jugadores", len(player_pos_t1))
                st.metric(f"{team2_name} - Jugadores", len(player_pos_t2))
            
            with col4:
                top1 = pass_conn_t1.iloc[0]['pass_count'] if len(pass_conn_t1) > 0 else 0
                top2 = pass_conn_t2.iloc[0]['pass_count'] if len(pass_conn_t2) > 0 else 0
                st.metric(f"{team1_name} - Top Conexión", f"{top1}")
                st.metric(f"{team2_name} - Top Conexión", f"{top2}")
            
            # Visualización lado a lado
            st.subheader("🕸️ Redes de Pases - Comparación")
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
            fig.patch.set_facecolor('#0e1117')
            
            # Red equipo 1
            plot_passing_network(player_pos_t1, pass_conn_t1, player_names, team1_name, min_passes, ax1)
            
            # Red equipo 2
            plot_passing_network(player_pos_t2, pass_conn_t2, player_names, team2_name, min_passes, ax2)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
            
            # Top conexiones comparadas
            st.subheader("🔗 Top 5 Conexiones por Equipo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**{team1_name}**")
                top_5_t1 = pass_conn_t1.head(5).copy()
                top_5_t1['Pasador'] = top_5_t1['player_id'].map(player_names)
                top_5_t1['Receptor'] = top_5_t1['recipient_id'].map(player_names)
                top_5_t1 = top_5_t1[['Pasador', 'Receptor', 'pass_count']]
                top_5_t1.columns = ['Pasador', 'Receptor', 'Pases']
                st.dataframe(top_5_t1, hide_index=True, use_container_width=True)
            
            with col2:
                st.markdown(f"**{team2_name}**")
                top_5_t2 = pass_conn_t2.head(5).copy()
                top_5_t2['Pasador'] = top_5_t2['player_id'].map(player_names)
                top_5_t2['Receptor'] = top_5_t2['recipient_id'].map(player_names)
                top_5_t2 = top_5_t2[['Pasador', 'Receptor', 'pass_count']]
                top_5_t2.columns = ['Pasador', 'Receptor', 'Pases']
                st.dataframe(top_5_t2, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    show_passing_network_tab()
