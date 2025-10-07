"""
app.py - Sistema completo con filtros mejorados y métricas avanzadas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

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
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file):
    return pd.read_parquet(file)

def get_match_mapping(df):
    matches = {}
    for mid in df['match_id'].unique():
        mdf = df[df['match_id'] == mid]
        teams = mdf['teamName'].unique()
        date = mdf['match_date'].iloc[0] if 'match_date' in mdf.columns else ""
        name = f"{teams[0]} vs {teams[1]}" if len(teams) >= 2 else (teams[0] if len(teams) == 1 else mid)
        if date and date != "Unknown":
            name = f"{name} ({date})"
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
        'Medio_Izq': 'Mid_Izq',
        'Medio_Centro': 'Mid_Centro',
        'Medio_Der': 'Mid_Der'
    }
    
    mapped_zones = []
    for z in selected_zones:
        mapped_zones.append(zone_reverse_mapping.get(z, z))
    
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
    
    styled = df.style
    
    for col in numeric_cols:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            styled = styled.applymap(lambda v: color_scale(v, min_val, max_val), subset=[col])
    
    return styled

def main():
    st.title("⚽ Análisis de Eventos de Fútbol")
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
        
        st.header("🔍 Filtros")
        
        # CATEGORÍA DE EVENTOS
        st.markdown("**Categoría de Eventos**")
        categorias_disponibles = ['Todas', 'ACCIONES_ARQUERO', 'CONDUCCIONES', 
                                   'DUELOS_DEFENSIVOS', 'DUELOS_OFENSIVOS', 'PASES', 'TIROS']
        sel_categorias = st.multiselect("", categorias_disponibles, default=['Todas'], key='cat')
        
        if 'Todas' in sel_categorias:
            df_f = df.copy()
        else:
            df_f = df[df['category'].isin(sel_categorias)]
        
        # TIPOS DE EVENTOS
        st.markdown("**Tipos de Eventos**")
        tipos = sorted(df_f['type'].unique().tolist())
        sel_tipos = st.multiselect("", ['Todos'] + tipos, default=['Todos'], key='tipos')
        if 'Todos' not in sel_tipos:
            df_f = df_f[df_f['type'].isin(sel_tipos)]
        
        # LIGA
        st.markdown("**Liga**")
        ligas = sorted(df_f['competition'].unique().tolist())
        sel_ligas = st.multiselect("", ['Todas'] + ligas, default=['Todas'], key='ligas')
        if 'Todas' not in sel_ligas:
            df_f = df_f[df_f['competition'].isin(sel_ligas)]
        
        # EQUIPOS
        st.markdown("**Equipos**")
        equipos = sorted(df_f['teamName'].unique().tolist())
        sel_equipos = st.multiselect("", ['Todos'] + equipos, default=['Todos'], key='equipos')
        if 'Todos' not in sel_equipos:
            df_f = df_f[df_f['teamName'].isin(sel_equipos)]
        
        # JUGADORES
        st.markdown("**Jugadores**")
        jugadores = sorted(df_f['playerName'].dropna().unique().tolist())
        sel_jugadores = st.multiselect("", ['Todos'] + jugadores, default=['Todos'], key='jugadores')
        if 'Todos' not in sel_jugadores:
            df_f = df_f[df_f['playerName'].isin(sel_jugadores)]
        
        # PARTIDOS
        st.markdown("**Partidos**")
        if 'match_id' in df_f.columns:
            match_map = get_match_mapping(df_f)
            mids = sorted(df_f['match_id'].unique().tolist())
            mopts = [match_map.get(m, m) for m in mids]
            sel_matches = st.multiselect("", ['Todos'] + mopts, default=['Todos'], key='partidos')
            if 'Todos' not in sel_matches:
                sel_mids = [m for m, n in match_map.items() if n in sel_matches]
                df_f = df_f[df_f['match_id'].isin(sel_mids)]
        
        st.markdown("---")
        st.subheader("📍 Filtro por Zonas")
        
        zonas_disponibles = ['Todas', 'Def_Izq', 'Def_Centro', 'Def_Der',
                            'Medio_Izq', 'Medio_Centro', 'Medio_Der',
                            'Att_Izq', 'Att_Centro', 'Att_Der']
        
        sel_zonas = st.multiselect("Zonas", zonas_disponibles, default=['Todas'])
        df_f = filter_by_zones(df_f, sel_zonas)
        
        st.markdown("---")
        st.subheader("Filtros Adicionales")
        
        col1, col2 = st.columns(2)
        with col1:
            prog = st.checkbox("Solo Progresivos")
        with col2:
            exito = st.checkbox("Solo Exitosos")
        
        show_heatmap = st.checkbox("🔥 Mapa de Calor por Zonas")
        
        if prog and 'is_progressive' in df_f.columns:
            df_f = df_f[df_f['is_progressive'] == 1]
        if exito:
            df_f = df_f[df_f['outcomeType'] == 'Successful']
        
        st.markdown("---")
        st.subheader("📊 Stats")
        
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
    
    if len(df_f) == 0:
        st.warning("Sin datos")
        st.stop()
    
    st.markdown(f"### 🎯 Mapa - {len(df_f):,} eventos")
    
    fig = create_pitch()
    
    if show_heatmap:
        fig = plot_heatmap_zones(fig, df_f)
    else:
        fig = plot_events_optimized(fig, df_f)
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    st.subheader("📊 Resumen")
    
    agg_dict = {
        'event_id': 'count',
        'outcomeType': lambda x: (x == 'Successful').sum(),
        'distance': 'mean'
    }
    
    if 'xT' in df_f.columns:
        agg_dict['xT'] = 'sum'
    
    if 'total_minutes' in df_f.columns:
        agg_dict['total_minutes'] = 'first'
    
    resumen = df_f.groupby(['playerName', 'teamName', 'type']).agg(agg_dict).reset_index()
    
    cols = ['Jugador', 'Equipo', 'Tipo', 'Total', 'Exitosos', 'Dist. Media']
    
    if 'total_minutes' in df_f.columns:
        cols.append('Minutos')
    
    if 'xT' in df_f.columns:
        cols.append('xT')
    
    resumen.columns = cols
    
    if 'xT' in resumen.columns:
        resumen['xT'] = resumen['xT'].round(3)
    
    resumen['% Éxito'] = (resumen['Exitosos'] / resumen['Total'] * 100).round(1)
    resumen['Dist. Media'] = resumen['Dist. Media'].round(1)
    
    if 'Minutos' in resumen.columns:
        resumen['Total/90'] = (resumen['Total'] / resumen['Minutos'] * 90).round(2)
        resumen['Exitosos/90'] = (resumen['Exitosos'] / resumen['Minutos'] * 90).round(2)
        if 'xT' in resumen.columns:
            resumen['xT/90'] = (resumen['xT'] / resumen['Minutos'] * 90).round(3)
    
    resumen = resumen.sort_values('Total', ascending=False)
    
    st.dataframe(style_dataframe(resumen), use_container_width=True, height=400)
    
    csv = df_f.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Descargar CSV", csv, "eventos.csv", "text/csv")

if __name__ == "__main__":
    main()