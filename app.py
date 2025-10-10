"""
app.py - Sistema completo con Stage, Fechas y Top Progresivos
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Análisis de Eventos", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    .main, .block-container { background-color: #0E1117; }
    * { color: #FAFAFA !important; }
    [data-testid="stSidebar"] { background-color: #262730; }
    .stSelectbox [data-baseweb="select"] > div { background-color: #31333F !important; }
    .stMultiSelect [data-baseweb="select"] > div { background-color: #31333F !important; }
    [data-baseweb="popover"], [role="listbox"], [role="option"] { background-color: #31333F !important; }
    [role="option"]:hover { background-color: #4A4C5A !important; }
    [data-testid="stMetricValue"] { color: #FAFAFA !important; }
    
    /* Mejorar espaciado de filtros */
    .stMultiSelect { margin-top: 5px; margin-bottom: 15px; }
    [data-testid="stSidebar"] h3 { margin-top: 20px; margin-bottom: 5px; }
    [data-testid="stSidebar"] .element-container { margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file):
    df = pd.read_parquet(file)
    
    # Convertir match_date a datetime
    if 'match_date' in df.columns:
        df['match_date'] = pd.to_datetime(df['match_date'], errors='coerce')
    
    return df

def get_match_mapping(df):
    matches = {}
    for mid in df['match_id'].unique():
        mdf = df[df['match_id'] == mid]
        teams = mdf['teamName'].unique()
        date = mdf['match_date'].iloc[0] if 'match_date' in mdf.columns else ""
        name = f"{teams[0]} vs {teams[1]}" if len(teams) >= 2 else (teams[0] if len(teams) == 1 else mid)
        
        if pd.notna(date):
            try:
                date_str = date.strftime('%Y-%m-%d')
                name = f"{date_str} - {name}"
            except:
                pass
        
        matches[mid] = name
    return matches

def create_pitch():
    fig = go.Figure()
    L, W = 120, 80
    lc = "#E0E0E0"
    
    shapes = [
        dict(type="rect", x0=0, y0=0, x1=L, y1=W, line=dict(color=lc, width=2), fillcolor="rgba(0,0,0,0)"),
        dict(type="line", x0=L/2, y0=0, x1=L/2, y1=W, line=dict(color=lc, width=2)),
        dict(type="circle", x0=L/2-9.15, y0=W/2-9.15, x1=L/2+9.15, y1=W/2+9.15, line=dict(color=lc, width=2))
    ]
    
    for x in [0, L]:
        d = 1 if x == 0 else -1
        shapes.extend([
            dict(type="rect", x0=x, y0=W/2-20.16, x1=x+d*16.5, y1=W/2+20.16, line=dict(color=lc, width=2), fillcolor="rgba(0,0,0,0)"),
            dict(type="rect", x0=x, y0=W/2-9.16, x1=x+d*5.5, y1=W/2+9.16, line=dict(color=lc, width=2), fillcolor="rgba(0,0,0,0)"),
            dict(type="line", x0=x, y0=W/2-3.66, x1=x, y1=W/2+3.66, line=dict(color=lc, width=3))
        ])
    
    fig.update_layout(
        shapes=shapes,
        plot_bgcolor='#1A5D1A', paper_bgcolor='#0E1117',
        xaxis=dict(range=[-5, L+5], visible=False),
        yaxis=dict(range=[-5, W+5], visible=False, scaleanchor="x", scaleratio=1),
        height=600, margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False, hovermode='closest'
    )
    return fig

def create_mini_pitch():
    """Crea una mini cancha para el top de progresivos"""
    fig = go.Figure()
    L, W = 120, 80
    lc = "#FFFFFF"
    
    shapes = [
        dict(type="rect", x0=0, y0=0, x1=L, y1=W, line=dict(color=lc, width=1.5), fillcolor="rgba(0,0,0,0.3)"),
        dict(type="line", x0=L/2, y0=0, x1=L/2, y1=W, line=dict(color=lc, width=1.5)),
    ]
    
    for x in [0, L]:
        d = 1 if x == 0 else -1
        shapes.extend([
            dict(type="rect", x0=x, y0=W/2-20.16, x1=x+d*16.5, y1=W/2+20.16, line=dict(color=lc, width=1.5), fillcolor="rgba(0,0,0,0)"),
        ])
    
    fig.update_layout(
        shapes=shapes,
        plot_bgcolor='#1A5D1A', 
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(range=[-5, L+5], visible=False),
        yaxis=dict(range=[-5, W+5], visible=False, scaleanchor="x", scaleratio=1),
        height=250, 
        margin=dict(l=5, r=5, t=30, b=40),
        showlegend=False, 
        hovermode=False
    )
    return fig

def plot_progressive_actions(fig, df_player, player_name):
    """Plotea acciones progresivas en mini cancha"""
    
    # Filtrar eventos con coordenadas válidas
    df_valid = df_player[
        df_player['x_scaled'].notna() & 
        df_player['y_scaled'].notna()
    ].copy()
    
    if len(df_valid) == 0:
        # Si no hay coordenadas válidas, mostrar mensaje
        fig.add_annotation(
            x=60, y=40,
            text="Sin coordenadas<br>disponibles",
            showarrow=False,
            font=dict(size=12, color='white'),
            bgcolor='rgba(255,0,0,0.3)',
            borderpad=10
        )
        fig.update_layout(
            title=dict(
                text=f"<b>{player_name}</b>",
                x=0.5,
                xanchor='center',
                font=dict(size=14, color='white')
            )
        )
        return fig
    
    # Conducciones progresivas (azul)
    df_carries = df_valid[df_valid['type'] == 'CONDUCCION'].copy()
    
    carries_plotted = 0
    if len(df_carries) > 0:
        for _, row in df_carries.iterrows():
            # Intentar graficar con flecha si tiene end coordinates
            if pd.notna(row.get('end_x_scaled')) and pd.notna(row.get('end_y_scaled')):
                fig.add_trace(go.Scatter(
                    x=[row['x_scaled'], row['end_x_scaled']],
                    y=[row['y_scaled'], row['end_y_scaled']],
                    mode='lines',
                    line=dict(color='#00BFFF', width=2),
                    opacity=0.6,
                    hoverinfo='skip',
                    showlegend=False
                ))
                carries_plotted += 1
            else:
                # Si no tiene end coordinates, solo graficar punto de inicio
                fig.add_trace(go.Scatter(
                    x=[row['x_scaled']],
                    y=[row['y_scaled']],
                    mode='markers',
                    marker=dict(color='#00BFFF', size=8, symbol='circle'),
                    opacity=0.7,
                    hoverinfo='skip',
                    showlegend=False
                ))
                carries_plotted += 1
    
    # Pases progresivos (rosa)
    df_passes = df_valid[
        (df_valid['type'] == 'PASE') & 
        (df_valid['outcomeType'] == 'Successful')
    ].copy()
    
    passes_plotted = 0
    if len(df_passes) > 0:
        for _, row in df_passes.iterrows():
            # Intentar graficar con flecha si tiene end coordinates
            if pd.notna(row.get('end_x_scaled')) and pd.notna(row.get('end_y_scaled')):
                fig.add_trace(go.Scatter(
                    x=[row['x_scaled'], row['end_x_scaled']],
                    y=[row['y_scaled'], row['end_y_scaled']],
                    mode='lines',
                    line=dict(color='#FF1493', width=2),
                    opacity=0.6,
                    hoverinfo='skip',
                    showlegend=False
                ))
                passes_plotted += 1
            else:
                # Si no tiene end coordinates, solo graficar punto de inicio
                fig.add_trace(go.Scatter(
                    x=[row['x_scaled']],
                    y=[row['y_scaled']],
                    mode='markers',
                    marker=dict(color='#FF1493', size=8, symbol='circle'),
                    opacity=0.7,
                    hoverinfo='skip',
                    showlegend=False
                ))
                passes_plotted += 1
    
    # Agregar anotación si se graficaron eventos
    total_plotted = carries_plotted + passes_plotted
    if total_plotted > 0 and total_plotted < len(df_valid):
        fig.add_annotation(
            x=10, y=75,
            text=f"⚠️ {len(df_valid) - total_plotted} sin coords finales",
            showarrow=False,
            font=dict(size=8, color='yellow'),
            bgcolor='rgba(0,0,0,0.5)',
            borderpad=3
        )
    
    # Título con nombre del jugador
    fig.update_layout(
        title=dict(
            text=f"<b>{player_name}</b>",
            x=0.5,
            xanchor='center',
            font=dict(size=14, color='white')
        )
    )
    
    return fig

def get_zone_coordinates():
    zones = {
        'Def_Izq':    {'x0': 0,   'x1': 40,  'y0': 53.33, 'y1': 80},
        'Def_Centro': {'x0': 0,   'x1': 40,  'y0': 26.67, 'y1': 53.33},
        'Def_Der':    {'x0': 0,   'x1': 40,  'y0': 0,     'y1': 26.67},
        'Medio_Izq':    {'x0': 40,  'x1': 80,  'y0': 53.33, 'y1': 80},
        'Medio_Centro': {'x0': 40,  'x1': 80,  'y0': 26.67, 'y1': 53.33},
        'Medio_Der':    {'x0': 40,  'x1': 80,  'y0': 0,     'y1': 26.67},
        'Att_Izq':    {'x0': 80,  'x1': 120, 'y0': 53.33, 'y1': 80},
        'Att_Centro': {'x0': 80,  'x1': 120, 'y0': 26.67, 'y1': 53.33},
        'Att_Der':    {'x0': 80,  'x1': 120, 'y0': 0,     'y1': 26.67}
    }
    return zones

def plot_heatmap_zones(fig, df):
    zone_mapping = {
        'Def_Izq': 'Def_Izq',
        'Def_Centro': 'Def_Centro',
        'Def_Der': 'Def_Der',
        'Mid_Izq': 'Medio_Izq',
        'Mid_Centro': 'Medio_Centro',
        'Mid_Der': 'Medio_Der',
        'Medio_Izq': 'Medio_Izq',
        'Medio_Centro': 'Medio_Centro',
        'Medio_Der': 'Medio_Der',
        'Att_Izq': 'Att_Izq',
        'Att_Centro': 'Att_Centro',
        'Att_Der': 'Att_Der'
    }
    
    df['zone_display'] = df['zone'].map(zone_mapping).fillna(df['zone'])
    zone_counts = df['zone_display'].value_counts().to_dict()
    max_count = max(zone_counts.values()) if zone_counts else 1
    
    zones = get_zone_coordinates()
    
    for zone_name, coords in zones.items():
        count = zone_counts.get(zone_name, 0)
        intensity = count / max_count
        
        if intensity < 0.3:
            color = f'rgba(255, 255, {int(100 + 155 * (1 - intensity/0.3))}, 0.5)'
        elif intensity < 0.6:
            adj_intensity = (intensity - 0.3) / 0.3
            red = 255
            green = int(255 - 100 * adj_intensity)
            color = f'rgba({red}, {green}, 0, 0.6)'
        else:
            adj_intensity = (intensity - 0.6) / 0.4
            red = int(255 - 55 * adj_intensity)
            color = f'rgba({red}, 0, 0, 0.7)'
        
        fig.add_shape(
            type="rect",
            x0=coords['x0'], y0=coords['y0'],
            x1=coords['x1'], y1=coords['y1'],
            fillcolor=color,
            line=dict(color='rgba(255,255,255,0.4)', width=1.5),
            layer='below'
        )
        
        center_x = (coords['x0'] + coords['x1']) / 2
        center_y = (coords['y0'] + coords['y1']) / 2
        
        fig.add_annotation(
            x=center_x, y=center_y,
            text=f"<b>{count}</b><br>{zone_name.replace('_', ' ')}",
            showarrow=False,
            font=dict(size=14, color='white', family='Arial Black'),
            bgcolor='rgba(0,0,0,0.7)',
            borderpad=6,
            bordercolor='white',
            borderwidth=1
        )
    
    return fig

def add_arrows_batch(fig, df_subset, color, max_arrows=150):
    if len(df_subset) == 0:
        return
    
    if len(df_subset) > max_arrows:
        df_subset = df_subset.sample(n=max_arrows, random_state=42)
    
    for _, row in df_subset.iterrows():
        if pd.notna(row['end_x_scaled']) and pd.notna(row['end_y_scaled']):
            fig.add_trace(go.Scatter(
                x=[row['x_scaled'], row['end_x_scaled'], None],
                y=[row['y_scaled'], row['end_y_scaled'], None],
                mode='lines',
                line=dict(color=color, width=1),
                opacity=0.4,
                hoverinfo='skip',
                showlegend=False
            ))

def plot_events_optimized(fig, df):
    df['hover_text'] = df.apply(lambda r: 
        f"<b>{r['type']}</b><br>"
        f"{r.get('playerName', 'N/A')}<br>"
        f"{r['teamName']}<br>"
        f"{r['timeMin']}:{r['timeSec']:02d}<br>"
        f"{r['outcomeType']}<br>"
        f"xT: {r.get('xT', 0):.3f}", axis=1)
    
    df_perdida = df[df['type'] == 'PERDIDA']
    if len(df_perdida) > 0:
        fig.add_trace(go.Scattergl(
            x=df_perdida['x_scaled'], y=df_perdida['y_scaled'],
            mode='markers',
            marker=dict(size=10, color='#FF4444', symbol='x', line=dict(width=2, color='white')),
            text=df_perdida['hover_text'],
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
    
    df_pases = df[df['type'] == 'PASE']
    for outcome, color in [('Successful', '#00FF41'), ('Unsuccessful', '#FF4444')]:
        dfo = df_pases[df_pases['outcomeType'] == outcome]
        if len(dfo) == 0:
            continue
        
        fig.add_trace(go.Scattergl(
            x=dfo['x_scaled'], y=dfo['y_scaled'],
            mode='markers',
            marker=dict(size=5, color=color, opacity=0.7),
            text=dfo['hover_text'],
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
    
    add_arrows_batch(fig, df_pases[df_pases['outcomeType']=='Successful'], '#00FF41', 100)
    add_arrows_batch(fig, df_pases[df_pases['outcomeType']=='Unsuccessful'], '#FF4444', 50)
    
    df_carries = df[df['type'] == 'CONDUCCION']
    if len(df_carries) > 0:
        fig.add_trace(go.Scattergl(
            x=df_carries['x_scaled'], y=df_carries['y_scaled'],
            mode='markers',
            marker=dict(size=5, color='#00FFFF', opacity=0.7),
            text=df_carries['hover_text'],
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
        add_arrows_batch(fig, df_carries, '#00FFFF', 80)
    
    tiros_exitosos = ['GOL', 'PALO']
    tiros_fallidos = ['TIRO DESVIADO', 'REMATE ATAJADO']
    
    df_tiros_ok = df[df['type'].isin(tiros_exitosos)]
    if len(df_tiros_ok) > 0:
        fig.add_trace(go.Scattergl(
            x=df_tiros_ok['x_scaled'], y=df_tiros_ok['y_scaled'],
            mode='markers',
            marker=dict(size=8, color='#00FF41', opacity=0.9),
            text=df_tiros_ok['hover_text'],
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
        add_arrows_batch(fig, df_tiros_ok, '#00FF41', 50)
    
    df_tiros_fail = df[df['type'].isin(tiros_fallidos)]
    if len(df_tiros_fail) > 0:
        fig.add_trace(go.Scattergl(
            x=df_tiros_fail['x_scaled'], y=df_tiros_fail['y_scaled'],
            mode='markers',
            marker=dict(size=8, color='#FF4444', opacity=0.9),
            text=df_tiros_fail['hover_text'],
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
        add_arrows_batch(fig, df_tiros_fail, '#FF4444', 50)
    
    eventos_especiales = ['PERDIDA', 'PASE', 'CONDUCCION'] + tiros_exitosos + tiros_fallidos
    df_otros = df[~df['type'].isin(eventos_especiales)]
    
    for outcome, color in [('Successful', '#00FF41'), ('Unsuccessful', '#FF4444')]:
        dfo = df_otros[df_otros['outcomeType'] == outcome]
        if len(dfo) == 0:
            continue
        
        fig.add_trace(go.Scattergl(
            x=dfo['x_scaled'], y=dfo['y_scaled'],
            mode='markers',
            marker=dict(size=5, color=color, opacity=0.7),
            text=dfo['hover_text'],
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
    
    return fig

def filter_by_zones(df, selected_zones):
    if not selected_zones or 'Todas' in selected_zones:
        return df
    
    zone_reverse_mapping = {
        'Medio_Izq': ['Mid_Izq', 'Medio_Izq'],
        'Medio_Centro': ['Mid_Centro', 'Medio_Centro'],
        'Medio_Der': ['Mid_Der', 'Medio_Der']
    }
    
    mapped_zones = []
    for z in selected_zones:
        if z in zone_reverse_mapping:
            mapped_zones.extend(zone_reverse_mapping[z])
        else:
            mapped_zones.append(z)
    
    return df[df['zone'].isin(mapped_zones)]

def style_dataframe(df):
    def color_scale(val, min_val, max_val):
        if pd.isna(val) or max_val == min_val:
            return ''
        
        normalized = (val - min_val) / (max_val - min_val)
        green = int(50 + 150 * normalized)
        return f'background-color: rgba(0, {green}, 50, 0.4)'
    
    numeric_cols = ['Total', 'Exitosos', 'Dist. Media', '% Éxito']
    if 'xT' in df.columns:
        numeric_cols.append('xT')
    if 'Minutos' in df.columns:
        numeric_cols.append('Minutos')
    if 'Total/90' in df.columns:
        numeric_cols.extend(['Total/90', 'Exitosos/90'])
    if 'xT/90' in df.columns:
        numeric_cols.append('xT/90')
    
    styled = df.style
    
    for col in numeric_cols:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            styled = styled.applymap(lambda v: color_scale(v, min_val, max_val), subset=[col])
    
    return styled

def pagina_analisis_principal(df_f, show_heatmap):
    """Página principal de análisis"""
    
    if len(df_f) == 0:
        st.warning("Sin datos")
        return
    
    st.markdown(f"### 🎯 Mapa - {len(df_f):,} eventos")
    
    fig = create_pitch()
    
    if show_heatmap:
        fig = plot_heatmap_zones(fig, df_f)
    else:
        fig = plot_events_optimized(fig, df_f)
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    st.subheader("📊 Resumen por Jugador")
    
    # Tabla de resumen
    resumen = df_f.groupby(['playerName', 'teamName', 'type']).agg({
        'event_id': 'count',
        'outcomeType': lambda x: (x == 'Successful').sum(),
        'distance': 'mean',
        'xT': 'sum' if 'xT' in df_f.columns else lambda x: 0,
        'total_minutes': 'first' if 'total_minutes' in df_f.columns else lambda x: 90
    }).reset_index()
    
    resumen.columns = ['Jugador', 'Equipo', 'Tipo', 'Total', 'Exitosos', 'Dist. Media', 'xT', 'Minutos']
    resumen['% Éxito'] = (resumen['Exitosos'] / resumen['Total'] * 100).round(1)
    resumen['Dist. Media'] = resumen['Dist. Media'].round(1)
    resumen['xT'] = resumen['xT'].round(3)
    resumen['Minutos'] = resumen['Minutos'].round(0).astype(int)
    resumen['Total/90'] = ((resumen['Total'] / resumen['Minutos']) * 90).round(2)
    resumen['Exitosos/90'] = ((resumen['Exitosos'] / resumen['Minutos']) * 90).round(2)
    resumen['xT/90'] = ((resumen['xT'] / resumen['Minutos']) * 90).round(3)
    resumen = resumen.sort_values('Total', ascending=False)
    
    st.dataframe(style_dataframe(resumen), use_container_width=True, height=400)
    
    csv = df_f.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Descargar CSV", csv, "eventos.csv", "text/csv")

def pagina_top_progresivos(df_f):
    """Página de Top Jugadores con Acciones Progresivas"""
    
    st.markdown("### 🚀 Top Jugadores - Acciones Progresivas")
    st.markdown("**Conducciones Progresivas** (azul) y **Pases Progresivos** (rosa)")
    
    # Filtrar solo acciones progresivas
    df_prog = df_f[
        ((df_f['type'] == 'CONDUCCION') | (df_f['type'] == 'PASE')) &
        (df_f.get('is_progressive', 0) == 1)
    ].copy()
    
    if len(df_prog) == 0:
        st.warning("⚠️ No hay acciones progresivas con los filtros seleccionados")
        return
    
    # Diagnóstico de coordenadas
    with st.expander("🔍 Diagnóstico de Datos"):
        total_prog = len(df_prog)
        con_x_y = df_prog['x_scaled'].notna().sum()
        con_end_x_y = df_prog['end_x_scaled'].notna().sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Progresivas", total_prog)
        with col2:
            st.metric("Con coordenadas inicio", f"{con_x_y} ({con_x_y/total_prog*100:.1f}%)")
        with col3:
            st.metric("Con coordenadas fin", f"{con_end_x_y} ({con_end_x_y/total_prog*100:.1f}%)")
        
        if con_end_x_y < total_prog * 0.5:
            st.warning("⚠️ Más del 50% de las acciones no tienen coordenadas finales. Las flechas serán limitadas.")
    
    # Calcular estadísticas por jugador
    stats_by_player = df_prog.groupby('playerName').agg({
        'event_id': 'count',
        'total_minutes': 'first',
        'teamName': 'first'
    }).reset_index()
    
    stats_by_player.columns = ['playerName', 'total_prog', 'minutes', 'teamName']
    
    # Calcular por tipo
    carries = df_prog[df_prog['type'] == 'CONDUCCION'].groupby('playerName').size().reset_index(name='prog_carries')
    passes = df_prog[df_prog['type'] == 'PASE'].groupby('playerName').size().reset_index(name='prog_passes')
    
    stats_by_player = stats_by_player.merge(carries, on='playerName', how='left')
    stats_by_player = stats_by_player.merge(passes, on='playerName', how='left')
    stats_by_player['prog_carries'] = stats_by_player['prog_carries'].fillna(0).astype(int)
    stats_by_player['prog_passes'] = stats_by_player['prog_passes'].fillna(0).astype(int)
    
    # Calcular por 90
    stats_by_player['prog_per_90'] = ((stats_by_player['total_prog'] / stats_by_player['minutes']) * 90).round(2)
    
    # Ordenar y tomar top 12
    stats_by_player = stats_by_player.sort_values('prog_per_90', ascending=False).head(12)
    
    # Selector de cantidad a mostrar
    col1, col2 = st.columns([3, 1])
    with col2:
        num_players = st.selectbox("Top:", [9, 12], index=1, key='num_players_top')
    
    top_players = stats_by_player.head(num_players)
    
    # Crear grid 3x3 o 4x3
    if num_players == 9:
        cols_per_row = 3
        num_rows = 3
    else:
        cols_per_row = 4
        num_rows = 3
    
    st.markdown("---")
    
    for row in range(num_rows):
        cols = st.columns(cols_per_row)
        
        for col_idx in range(cols_per_row):
            player_idx = row * cols_per_row + col_idx
            
            if player_idx >= len(top_players):
                break
            
            player_row = top_players.iloc[player_idx]
            player_name = player_row['playerName']
            
            # Datos del jugador
            df_player = df_prog[df_prog['playerName'] == player_name]
            
            with cols[col_idx]:
                # Crear mini cancha
                fig = create_mini_pitch()
                fig = plot_progressive_actions(fig, df_player, player_name)
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                # Estadísticas debajo
                st.markdown(f"""
                <div style='text-align: center; padding: 5px; background-color: rgba(0,0,0,0.3); border-radius: 5px;'>
                    <span style='color: #FF1493; font-weight: bold;'>{player_row['prog_passes']:.0f}</span>
                    <span style='color: white;'> | </span>
                    <span style='color: #00BFFF; font-weight: bold;'>{player_row['prog_carries']:.0f}</span>
                    <br>
                    <span style='color: white; font-size: 12px;'>Prog p90: <b>{player_row['prog_per_90']:.2f}</b></span>
                </div>
                """, unsafe_allow_html=True)

def main():
    st.title("⚽ Análisis de Eventos")
    st.markdown("**Visualización profesional con xT | Datos Opta 120x80**")
    
    with st.sidebar:
        st.header("📁 Cargar Datos")
        uploaded = st.file_uploader("Archivo .parquet", type=['parquet'])
        
        if not uploaded:
            st.info("Carga un archivo")
            st.stop()
        
        df = load_data(uploaded)
        st.success(f"{len(df):,} eventos")
        
        if 'xT' in df.columns:
            total_xt = df['xT'].sum()
            st.info(f"✅ xT Total: {total_xt:.2f}")
        
        st.markdown("---")
        st.header("🔍 Filtros")
        
        # FILTRO DE STAGE
        if 'stage_name' in df.columns:
            st.subheader("📅 Stage / Fase")
            stages_disponibles = sorted(df['stage_name'].dropna().unique().tolist())
            
            if len(stages_disponibles) > 1:
                sel_stages = st.multiselect(
                    "Selecciona stage(s):",
                    options=stages_disponibles,
                    default=stages_disponibles,
                    key='stages'
                )
                
                if sel_stages:
                    df = df[df['stage_name'].isin(sel_stages)]
                else:
                    st.warning("Selecciona al menos un stage")
        
        # FILTRO DE FECHA
        if 'match_date' in df.columns:
            st.subheader("📆 Rango de Fechas")
            fechas_validas = df['match_date'].dropna()
            
            if len(fechas_validas) > 0:
                fecha_min = fechas_validas.min().date()
                fecha_max = fechas_validas.max().date()
                
                col1, col2 = st.columns(2)
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
                df['match_date_only'] = pd.to_datetime(df['match_date']).dt.date
                df = df[
                    (df['match_date_only'] >= fecha_desde) &
                    (df['match_date_only'] <= fecha_hasta)
                ]
                df = df.drop('match_date_only', axis=1)
                
                partidos_en_rango = df['match_id'].nunique() if 'match_id' in df.columns else 0
                st.caption(f"✅ {partidos_en_rango} partidos en rango")
        
        st.markdown("---")
        
        # Resto de filtros
        st.subheader("Categoría de Eventos")
        categorias_disponibles = ['Todas', 'ACCIONES_ARQUERO', 'CONDUCCIONES', 
                                   'DUELOS_DEFENSIVOS', 'DUELOS_OFENSIVOS', 'PASES', 'TIROS']
        sel_categorias = st.multiselect(
            "",
            categorias_disponibles,
            default=['Todas'],
            key='cat',
            label_visibility='collapsed'
        )
        
        if 'Todas' in sel_categorias:
            df_f = df.copy()
        else:
            df_f = df[df['category'].isin(sel_categorias)]
        
        st.subheader("Tipos de Eventos")
        tipos = sorted(df_f['type'].unique().tolist())
        sel_tipos = st.multiselect(
            "",
            ['Todos'] + tipos,
            default=['Todos'],
            key='tipos',
            label_visibility='collapsed'
        )
        if 'Todos' not in sel_tipos:
            df_f = df_f[df_f['type'].isin(sel_tipos)]
        
        st.subheader("Liga")
        ligas = sorted(df_f['competition'].unique().tolist())
        sel_ligas = st.multiselect(
            "",
            ['Todas'] + ligas,
            default=['Todas'],
            key='ligas',
            label_visibility='collapsed'
        )
        if 'Todas' not in sel_ligas:
            df_f = df_f[df_f['competition'].isin(sel_ligas)]
        
        st.subheader("Equipos")
        equipos = sorted(df_f['teamName'].unique().tolist())
        sel_equipos = st.multiselect(
            "",
            ['Todos'] + equipos,
            default=['Todos'],
            key='equipos',
            label_visibility='collapsed'
        )
        if 'Todos' not in sel_equipos:
            df_f = df_f[df_f['teamName'].isin(sel_equipos)]
        
        st.subheader("Jugadores")
        jugadores = sorted(df_f['playerName'].dropna().unique().tolist())
        sel_jugadores = st.multiselect(
            "",
            ['Todos'] + jugadores,
            default=['Todos'],
            key='jugadores',
            label_visibility='collapsed'
        )
        if 'Todos' not in sel_jugadores:
            df_f = df_f[df_f['playerName'].isin(sel_jugadores)]
        
        st.subheader("Partidos")
        if 'match_id' in df_f.columns:
            match_map = get_match_mapping(df_f)
            mids = sorted(df_f['match_id'].unique().tolist())
            mopts = [match_map.get(m, m) for m in mids]
            sel_matches = st.multiselect(
                "",
                ['Todos'] + mopts,
                default=['Todos'],
                key='partidos',
                label_visibility='collapsed'
            )
            if 'Todos' not in sel_matches:
                sel_mids = [m for m, n in match_map.items() if n in sel_matches]
                df_f = df_f[df_f['match_id'].isin(sel_mids)]
        
        st.markdown("---")
        st.subheader("📍 Filtro por Zonas")
        
        zonas_disponibles = ['Todas', 'Def_Izq', 'Def_Centro', 'Def_Der',
                            'Medio_Izq', 'Medio_Centro', 'Medio_Der',
                            'Att_Izq', 'Att_Centro', 'Att_Der']
        
        sel_zonas = st.multiselect(
            "",
            zonas_disponibles,
            default=['Todas'],
            label_visibility='collapsed'
        )
        df_f = filter_by_zones(df_f, sel_zonas)
        
        st.markdown("---")
        st.subheader("⚙️ Opciones")
        
        col1, col2 = st.columns(2)
        with col1:
            prog = st.checkbox("Solo Progresivos")
        with col2:
            exito = st.checkbox("Solo Exitosos")
        
        show_heatmap = st.checkbox("🔥 Mapa de Calor")
        
        if prog and 'is_progressive' in df_f.columns:
            df_f = df_f[df_f['is_progressive'] == 1]
        if exito:
            df_f = df_f[df_f['outcomeType'] == 'Successful']
        
        st.markdown("---")
        st.subheader("📊 Resumen")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", f"{len(df_f):,}")
            if len(df_f) > 0:
                st.metric("% Éxito", f"{(df_f['outcomeType']=='Successful').mean()*100:.1f}%")
        with col2:
            if len(df_f) > 0:
                st.metric("Exitosos", f"{(df_f['outcomeType']=='Successful').sum():,}")
                if 'xT' in df_f.columns:
                    st.metric("xT Filtrado", f"{df_f['xT'].sum():.2f}")
    
    # TABS PRINCIPALES
    tab1, tab2 = st.tabs(["🗺️ Análisis en Campo", "🚀 Top Progresivos"])
    
    with tab1:
        pagina_analisis_principal(df_f, show_heatmap)
    
    with tab2:
        pagina_top_progresivos(df_f)

if __name__ == "__main__":
    main()