# tactical_zones.py
"""
Módulo de Zonificación Táctica Avanzada
Basado en el concepto de Zonas de Packing para análisis dinámico
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
import matplotlib.patches as mpatches
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import streamlit as st

class TacticalZones:
    """
    Define y analiza zonas tácticas dinámicas en el campo de fútbol
    """
    
    def __init__(self, pitch_length=120, pitch_width=80):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        
        # Definir las 11 zonas tácticas basadas en la imagen
        self.zones = self._define_zones()
        
        # Colores para cada zona (gradiente de azul)
        self.zone_colors = {
            'Zona Lateral Izquierda': '#1e3a5f',
            'Zona Defensa Central': '#2c4d7b',
            'Zona Lateral Derecha': '#3a5f8d',
            'Zona Banda Izquierda': '#4a6fa0',
            'Zona Mediocentro Defensivo': '#5a7fb0',
            'Zona Banda Derecha': '#6a8fc0',
            'Zona detrás Defensa (Banda Izquierda)': '#7a9fd0',
            'Zona Mediocentro': '#8aafd0',
            'Zona detrás Defensa (Banda Derecha)': '#9abfe0',
            'Zona Centrocampista Ofensivo': '#aacfef',
            'Zona detrás Defensa Central': '#badfff'
        }
        
    def _define_zones(self) -> Dict[str, Dict]:
        """
        Define las coordenadas y características de cada zona táctica
        Similar a las zonas de Packing mostradas en la imagen
        """
        zones = {
            # Zonas defensivas (tercio defensivo)
            'Zona Lateral Izquierda': {
                'id': 0,
                'bounds': {'x_min': 0, 'x_max': 25, 'y_min': 0, 'y_max': 25},
                'type': 'defensive',
                'vertical_position': 'deep',
                'horizontal_position': 'left',
                'typical_position': 'LB',
                'events_count': 0
            },
            'Zona Defensa Central': {
                'id': 3,
                'bounds': {'x_min': 0, 'x_max': 25, 'y_min': 25, 'y_max': 55},
                'type': 'defensive',
                'vertical_position': 'deep',
                'horizontal_position': 'center',
                'typical_position': 'CB',
                'events_count': 0
            },
            'Zona Lateral Derecha': {
                'id': 3,
                'bounds': {'x_min': 0, 'x_max': 25, 'y_min': 55, 'y_max': 80},
                'type': 'defensive',
                'vertical_position': 'deep',
                'horizontal_position': 'right',
                'typical_position': 'RB',
                'events_count': 0
            },
            
            # Zonas de mediocentro defensivo
            'Zona Mediocentro Defensivo': {
                'id': 26,
                'bounds': {'x_min': 25, 'x_max': 50, 'y_min': 20, 'y_max': 60},
                'type': 'defensive_midfield',
                'vertical_position': 'defensive_third',
                'horizontal_position': 'center',
                'typical_position': 'CDM',
                'events_count': 0
            },
            
            # Bandas defensivas
            'Zona Banda Izquierda': {
                'id': 22,
                'bounds': {'x_min': 25, 'x_max': 50, 'y_min': 0, 'y_max': 20},
                'type': 'defensive_midfield',
                'vertical_position': 'defensive_third',
                'horizontal_position': 'left_wing',
                'typical_position': 'LWB',
                'events_count': 0
            },
            'Zona Banda Derecha': {
                'id': 24,
                'bounds': {'x_min': 25, 'x_max': 50, 'y_min': 60, 'y_max': 80},
                'type': 'defensive_midfield',
                'vertical_position': 'defensive_third',
                'horizontal_position': 'right_wing',
                'typical_position': 'RWB',
                'events_count': 0
            },
            
            # Zona de mediocentro (centro del campo)
            'Zona Mediocentro': {
                'id': 47,
                'bounds': {'x_min': 50, 'x_max': 70, 'y_min': 25, 'y_max': 55},
                'type': 'midfield',
                'vertical_position': 'middle_third',
                'horizontal_position': 'center',
                'typical_position': 'CM',
                'events_count': 0
            },
            
            # Zonas ofensivas de banda
            'Zona detrás Defensa (Banda Izquierda)': {
                'id': 33,
                'bounds': {'x_min': 70, 'x_max': 95, 'y_min': 0, 'y_max': 25},
                'type': 'offensive_midfield',
                'vertical_position': 'attacking_third',
                'horizontal_position': 'left_wing',
                'typical_position': 'LW',
                'events_count': 0
            },
            'Zona detrás Defensa (Banda Derecha)': {
                'id': 17,
                'bounds': {'x_min': 70, 'x_max': 95, 'y_min': 55, 'y_max': 80},
                'type': 'offensive_midfield',
                'vertical_position': 'attacking_third',
                'horizontal_position': 'right_wing',
                'typical_position': 'RW',
                'events_count': 0
            },
            
            # Zonas centrales ofensivas
            'Zona Centrocampista Ofensivo': {
                'id': 55,
                'bounds': {'x_min': 70, 'x_max': 95, 'y_min': 25, 'y_max': 55},
                'type': 'offensive_midfield',
                'vertical_position': 'attacking_third',
                'horizontal_position': 'center',
                'typical_position': 'CAM',
                'events_count': 0
            },
            'Zona detrás Defensa Central': {
                'id': 101,
                'bounds': {'x_min': 95, 'x_max': 120, 'y_min': 25, 'y_max': 55},
                'type': 'offensive',
                'vertical_position': 'final_third',
                'horizontal_position': 'center',
                'typical_position': 'ST',
                'events_count': 0
            }
        }
        
        return zones
    
    def get_zone_for_coordinates(self, x: float, y: float) -> str:
        """
        Determina en qué zona táctica se encuentra un punto dado
        
        Args:
            x: Coordenada x (0-120)
            y: Coordenada y (0-80)
            
        Returns:
            Nombre de la zona táctica
        """
        for zone_name, zone_info in self.zones.items():
            bounds = zone_info['bounds']
            if (bounds['x_min'] <= x <= bounds['x_max'] and 
                bounds['y_min'] <= y <= bounds['y_max']):
                return zone_name
        
        # Si no está en ninguna zona específica, determinar la más cercana
        return self._get_nearest_zone(x, y)
    
    def _get_nearest_zone(self, x: float, y: float) -> str:
        """
        Encuentra la zona más cercana a un punto dado
        """
        min_distance = float('inf')
        nearest_zone = 'Zona Mediocentro'
        
        for zone_name, zone_info in self.zones.items():
            bounds = zone_info['bounds']
            # Calcular centro de la zona
            center_x = (bounds['x_min'] + bounds['x_max']) / 2
            center_y = (bounds['y_min'] + bounds['y_max']) / 2
            
            # Distancia euclidiana
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_zone = zone_name
        
        return nearest_zone
    
    def add_zones_to_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Añade columnas de zona táctica al DataFrame de eventos
        
        Args:
            df: DataFrame con eventos (debe tener columnas 'x' e 'y')
            
        Returns:
            DataFrame con columnas adicionales de zonas
        """
        if 'x' not in df.columns or 'y' not in df.columns:
            st.warning("DataFrame debe tener columnas 'x' e 'y'")
            return df
        
        # Añadir zona de inicio
        df['tactical_zone'] = df.apply(
            lambda row: self.get_zone_for_coordinates(row['x'], row['y']),
            axis=1
        )
        
        # Si hay coordenadas de fin, añadir zona de fin
        if 'end_x' in df.columns and 'end_y' in df.columns:
            df['tactical_zone_end'] = df.apply(
                lambda row: self.get_zone_for_coordinates(row['end_x'], row['end_y'])
                if pd.notna(row.get('end_x')) and pd.notna(row.get('end_y'))
                else None,
                axis=1
            )
            
            # Determinar si es una transición entre zonas
            df['zone_transition'] = df.apply(
                lambda row: f"{row['tactical_zone']} → {row['tactical_zone_end']}"
                if pd.notna(row.get('tactical_zone_end')) and 
                   row['tactical_zone'] != row['tactical_zone_end']
                else None,
                axis=1
            )
        
        # Añadir información adicional de la zona
        df['zone_type'] = df['tactical_zone'].map(
            lambda z: self.zones.get(z, {}).get('type', 'unknown')
        )
        df['zone_vertical'] = df['tactical_zone'].map(
            lambda z: self.zones.get(z, {}).get('vertical_position', 'unknown')
        )
        df['zone_horizontal'] = df['tactical_zone'].map(
            lambda z: self.zones.get(z, {}).get('horizontal_position', 'unknown')
        )
        
        return df
    
    def visualize_zones(self, ax=None, show_labels=True, alpha=0.6):
        """
        Visualiza las zonas tácticas en el campo
        
        Args:
            ax: Axes de matplotlib (opcional)
            show_labels: Si mostrar etiquetas de zonas
            alpha: Transparencia de las zonas
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 9))
            ax.set_xlim(0, self.pitch_length)
            ax.set_ylim(0, self.pitch_width)
            ax.set_aspect('equal')
            ax.set_facecolor('#1a1a1a')
        
        # Dibujar cada zona
        for zone_name, zone_info in self.zones.items():
            bounds = zone_info['bounds']
            
            # Crear rectángulo para la zona
            rect = Rectangle(
                (bounds['x_min'], bounds['y_min']),
                bounds['x_max'] - bounds['x_min'],
                bounds['y_max'] - bounds['y_min'],
                facecolor=self.zone_colors.get(zone_name, '#5a7fb0'),
                edgecolor='white',
                linewidth=2,
                alpha=alpha
            )
            ax.add_patch(rect)
            
            # Añadir etiqueta si está habilitado
            if show_labels:
                center_x = (bounds['x_min'] + bounds['x_max']) / 2
                center_y = (bounds['y_min'] + bounds['y_max']) / 2
                
                # Texto principal (nombre de zona)
                ax.text(center_x, center_y + 2, 
                       zone_name.replace(' ', '\n'),
                       ha='center', va='center',
                       fontsize=8, color='white',
                       fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor='black', alpha=0.7))
                
                # ID de zona (número)
                ax.text(center_x, center_y - 3,
                       str(zone_info['id']),
                       ha='center', va='center',
                       fontsize=14, color='white',
                       fontweight='bold')
        
        return ax
    
    def analyze_zone_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analiza la distribución de eventos por zona táctica
        
        Args:
            df: DataFrame con columna 'tactical_zone'
            
        Returns:
            DataFrame con estadísticas por zona
        """
        if 'tactical_zone' not in df.columns:
            df = self.add_zones_to_dataframe(df)
        
        # Contar eventos por zona
        zone_stats = df.groupby('tactical_zone').agg({
            'type': 'count',
            'outcomeType': lambda x: (x == 'Successful').mean() * 100 if len(x) > 0 else 0,
            'progressive_distance': 'sum' if 'progressive_distance' in df.columns else lambda x: 0,
            'xT': 'sum' if 'xT' in df.columns else lambda x: 0
        }).round(2)
        
        zone_stats.columns = ['events_count', 'success_rate', 'total_progressive', 'total_xT']
        
        # Añadir información de la zona
        zone_stats['zone_type'] = zone_stats.index.map(
            lambda z: self.zones.get(z, {}).get('type', 'unknown')
        )
        zone_stats['zone_position'] = zone_stats.index.map(
            lambda z: self.zones.get(z, {}).get('typical_position', 'unknown')
        )
        
        return zone_stats.sort_values('events_count', ascending=False)
    
    def analyze_zone_transitions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analiza las transiciones entre zonas (para pases y carries)
        
        Args:
            df: DataFrame con eventos
            
        Returns:
            DataFrame con estadísticas de transiciones
        """
        if 'zone_transition' not in df.columns:
            df = self.add_zones_to_dataframe(df)
        
        # Filtrar solo eventos con transiciones
        transitions = df[df['zone_transition'].notna()]
        
        if transitions.empty:
            return pd.DataFrame()
        
        # Analizar transiciones
        transition_stats = transitions.groupby('zone_transition').agg({
            'type': 'count',
            'outcomeType': lambda x: (x == 'Successful').mean() * 100,
            'progressive_distance': 'mean' if 'progressive_distance' in transitions.columns else lambda x: 0
        }).round(2)
        
        transition_stats.columns = ['count', 'success_rate', 'avg_progressive']
        
        return transition_stats.sort_values('count', ascending=False)
    
    def create_zone_heatmap(self, df: pd.DataFrame, event_type: Optional[str] = None,
                           team: Optional[str] = None, player: Optional[str] = None):
        """
        Crea un heatmap de eventos por zona táctica
        
        Args:
            df: DataFrame con eventos
            event_type: Tipo de evento a filtrar (opcional)
            team: Equipo a filtrar (opcional)
            player: Jugador a filtrar (opcional)
            
        Returns:
            Figure de matplotlib
        """
        # Filtrar datos
        data = df.copy()
        if event_type:
            data = data[data['type'] == event_type]
        if team:
            data = data[data['teamName'] == team]
        if player:
            data = data[data['playerName'] == player]
        
        # Añadir zonas si no existen
        if 'tactical_zone' not in data.columns:
            data = self.add_zones_to_dataframe(data)
        
        # Contar eventos por zona
        zone_counts = data['tactical_zone'].value_counts()
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(14, 9))
        ax.set_xlim(0, self.pitch_length)
        ax.set_ylim(0, self.pitch_width)
        ax.set_aspect('equal')
        ax.set_facecolor('#1a1a1a')
        
        # Normalizar conteos para colores
        max_count = zone_counts.max() if not zone_counts.empty else 1
        
        # Dibujar cada zona con intensidad basada en eventos
        for zone_name, zone_info in self.zones.items():
            bounds = zone_info['bounds']
            
            # Obtener conteo de eventos para esta zona
            count = zone_counts.get(zone_name, 0)
            intensity = count / max_count if max_count > 0 else 0
            
            # Color basado en intensidad
            base_color = np.array([0.2, 0.5, 0.8])  # Azul base
            heat_color = np.array([1.0, 0.2, 0.2])  # Rojo para alta intensidad
            color = base_color * (1 - intensity) + heat_color * intensity
            
            # Crear rectángulo
            rect = Rectangle(
                (bounds['x_min'], bounds['y_min']),
                bounds['x_max'] - bounds['x_min'],
                bounds['y_max'] - bounds['y_min'],
                facecolor=color,
                edgecolor='white',
                linewidth=2,
                alpha=0.7
            )
            ax.add_patch(rect)
            
            # Añadir texto con conteo
            center_x = (bounds['x_min'] + bounds['x_max']) / 2
            center_y = (bounds['y_min'] + bounds['y_max']) / 2
            
            ax.text(center_x, center_y,
                   f"{count}\n({count/len(data)*100:.1f}%)" if count > 0 else "0",
                   ha='center', va='center',
                   fontsize=10, color='white',
                   fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', 
                           facecolor='black', alpha=0.7))
        
        # Título
        title = "Heatmap de Eventos por Zona Táctica"
        if event_type:
            title += f" - {event_type}"
        if team:
            title += f" - {team}"
        if player:
            title += f" - {player}"
        
        ax.set_title(title, color='white', fontsize=14, pad=20)
        ax.axis('off')
        
        # Añadir leyenda de colores
        from matplotlib.colorbar import ColorbarBase
        from matplotlib.colors import LinearSegmentedColormap
        
        cmap = LinearSegmentedColormap.from_list('heat', 
                                                 [(0.2, 0.5, 0.8), (1.0, 0.2, 0.2)])
        sm = plt.cm.ScalarMappable(cmap=cmap)
        sm.set_array([0, max_count])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
        cbar.set_label('Número de Eventos', color='white')
        cbar.ax.yaxis.set_tick_params(color='white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
        
        return fig
    
    def get_player_zone_profile(self, df: pd.DataFrame, player_name: str) -> Dict:
        """
        Obtiene el perfil de zonas de un jugador específico
        
        Args:
            df: DataFrame con eventos
            player_name: Nombre del jugador
            
        Returns:
            Diccionario con perfil del jugador
        """
        player_data = df[df['playerName'] == player_name].copy()
        
        if player_data.empty:
            return {}
        
        # Añadir zonas si no existen
        if 'tactical_zone' not in player_data.columns:
            player_data = self.add_zones_to_dataframe(player_data)
        
        # Calcular estadísticas por zona
        zone_distribution = player_data['tactical_zone'].value_counts(normalize=True) * 100
        
        # Zona más frecuente
        main_zone = zone_distribution.index[0] if not zone_distribution.empty else 'Unknown'
        main_zone_pct = zone_distribution.iloc[0] if not zone_distribution.empty else 0
        
        # Diversidad de zonas (entropía)
        zone_diversity = -sum(p * np.log(p) for p in zone_distribution / 100 if p > 0)
        
        profile = {
            'player_name': player_name,
            'main_zone': main_zone,
            'main_zone_percentage': round(main_zone_pct, 1),
            'zones_covered': len(zone_distribution),
            'zone_diversity': round(zone_diversity, 2),
            'zone_distribution': zone_distribution.to_dict(),
            'typical_position': self.zones.get(main_zone, {}).get('typical_position', 'Unknown'),
            'zone_type': self.zones.get(main_zone, {}).get('type', 'Unknown')
        }
        
        # Añadir métricas por tipo de zona
        for zone_type in ['defensive', 'midfield', 'offensive']:
            zones_of_type = [z for z, info in self.zones.items() 
                            if info.get('type', '').startswith(zone_type)]
            pct_in_type = player_data[player_data['tactical_zone'].isin(zones_of_type)].shape[0]
            pct_in_type = (pct_in_type / len(player_data) * 100) if len(player_data) > 0 else 0
            profile[f'{zone_type}_percentage'] = round(pct_in_type, 1)
        
        return profile


# ======================================
# INTEGRACIÓN CON STREAMLIT APP
# ======================================

def add_tactical_zones_tab(df: pd.DataFrame):
    """
    Añade una tab de análisis por zonas tácticas a la app de Streamlit
    
    Args:
        df: DataFrame con eventos
    """
    st.header("🎯 Análisis por Zonas Tácticas")
    
    # Inicializar el sistema de zonas
    zones = TacticalZones()
    
    # Añadir zonas al DataFrame si no existen
    if 'tactical_zone' not in df.columns:
        with st.spinner("Calculando zonas tácticas..."):
            df = zones.add_zones_to_dataframe(df)
            st.session_state['data_with_zones'] = df
    
    # Sub-tabs para diferentes análisis
    zone_tab1, zone_tab2, zone_tab3, zone_tab4 = st.tabs([
        "📍 Visualización de Zonas",
        "📊 Distribución de Eventos",
        "🔄 Transiciones",
        "👤 Perfiles por Zona"
    ])
    
    with zone_tab1:
        st.subheader("Mapa de Zonas Tácticas")
        
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("### Filtros")
            
            # Selector de tipo de evento
            event_types = ['Todos'] + sorted(df['type'].unique().tolist())
            selected_event = st.selectbox(
                "Tipo de Evento",
                event_types,
                key='zone_event_filter'
            )
            
            # Selector de equipo
            teams = ['Todos'] + sorted(df['teamName'].dropna().unique().tolist())
            selected_team = st.selectbox(
                "Equipo",
                teams,
                key='zone_team_filter'
            )
            
            # Selector de jugador
            players = ['Todos'] + sorted(df['playerName'].dropna().unique().tolist())
            selected_player = st.selectbox(
                "Jugador",
                players[:50],  # Limitar a 50 para rendimiento
                key='zone_player_filter'
            )
            
            # Checkbox para mostrar etiquetas
            show_labels = st.checkbox("Mostrar nombres de zonas", value=True)
        
        with col1:
            # Filtrar datos
            filtered_df = df.copy()
            if selected_event != 'Todos':
                filtered_df = filtered_df[filtered_df['type'] == selected_event]
            if selected_team != 'Todos':
                filtered_df = filtered_df[filtered_df['teamName'] == selected_team]
            if selected_player != 'Todos':
                filtered_df = filtered_df[filtered_df['playerName'] == selected_player]
            
            # Crear heatmap de zonas
            fig = zones.create_zone_heatmap(
                filtered_df,
                event_type=None if selected_event == 'Todos' else selected_event,
                team=None if selected_team == 'Todos' else selected_team,
                player=None if selected_player == 'Todos' else selected_player
            )
            
            st.pyplot(fig)
            
            # Estadísticas rápidas
            st.markdown("### 📈 Estadísticas Rápidas")
            zone_stats = zones.analyze_zone_distribution(filtered_df)
            
            if not zone_stats.empty:
                col_s1, col_s2, col_s3 = st.columns(3)
                
                with col_s1:
                    most_active = zone_stats.index[0]
                    st.metric(
                        "Zona más activa",
                        most_active.replace('Zona ', ''),
                        f"{zone_stats.iloc[0]['events_count']} eventos"
                    )
                
                with col_s2:
                    best_success = zone_stats.nlargest(1, 'success_rate').index[0]
                    st.metric(
                        "Zona más efectiva",
                        best_success.replace('Zona ', ''),
                        f"{zone_stats.loc[best_success, 'success_rate']:.1f}% éxito"
                    )
                
                with col_s3:
                    if 'total_progressive' in zone_stats.columns:
                        most_progressive = zone_stats.nlargest(1, 'total_progressive').index[0]
                        st.metric(
                            "Zona más progresiva",
                            most_progressive.replace('Zona ', ''),
                            f"{zone_stats.loc[most_progressive, 'total_progressive']:.1f}m"
                        )
    
    with zone_tab2:
        st.subheader("📊 Distribución de Eventos por Zona")
        
        # Análisis de distribución
        zone_stats = zones.analyze_zone_distribution(df)
        
        if not zone_stats.empty:
            # Gráfico de barras
            import plotly.express as px
            
            fig_bar = px.bar(
                zone_stats.reset_index(),
                x='events_count',
                y='tactical_zone',
                orientation='h',
                title='Eventos por Zona Táctica',
                color='success_rate',
                color_continuous_scale='RdYlGn',
                labels={
                    'tactical_zone': 'Zona',
                    'events_count': 'Número de Eventos',
                    'success_rate': 'Tasa de Éxito (%)'
                }
            )
            fig_bar.update_layout(height=600)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Tabla detallada
            st.markdown("### Tabla Detallada de Zonas")
            
            # Formatear tabla
            zone_stats_display = zone_stats[['events_count', 'success_rate', 'zone_type', 'zone_position']].copy()
            zone_stats_display.columns = ['Eventos', 'Éxito %', 'Tipo', 'Posición']
            
            st.dataframe(
                zone_stats_display.style.background_gradient(
                    subset=['Eventos'],
                    cmap='Blues'
                ).background_gradient(
                    subset=['Éxito %'],
                    cmap='RdYlGn'
                ).format({
                    'Éxito %': '{:.1f}%',
                    'Eventos': '{:.0f}'
                }),
                height=400
            )
    
    with zone_tab3:
        st.subheader("🔄 Análisis de Transiciones entre Zonas")
        
        # Filtrar eventos con transiciones (pases y carries)
        transition_events = df[(df['type'].isin(['Pass', 'Carry'])) & 
                              (df['zone_transition'].notna())].copy()
        
        if not transition_events.empty:
            # Análisis de transiciones
            transitions = zones.analyze_zone_transitions(transition_events)
            
            if not transitions.empty:
                # Top transiciones
                st.markdown("### Top 15 Transiciones Más Frecuentes")
                
                top_transitions = transitions.head(15).reset_index()
                
                # Gráfico de flujo
                fig_flow = px.bar(
                    top_transitions,
                    x='count',
                    y='zone_transition',
                    orientation='h',
                    title='Transiciones entre Zonas Tácticas',
                    color='success_rate',
                    color_continuous_scale='RdYlGn',
                    labels={
                        'zone_transition': 'Transición',
                        'count': 'Frecuencia',
                        'success_rate': 'Éxito %'
                    }
                )
                fig_flow.update_layout(height=600)
                st.plotly_chart(fig_flow, use_container_width=True)
                
                # Métricas de transición
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_transitions = transitions['count'].sum()
                    st.metric("Total Transiciones", f"{total_transitions:,}")
                
                with col2:
                    avg_success = transitions['success_rate'].mean()
                    st.metric("Éxito Promedio", f"{avg_success:.1f}%")
                
                with col3:
                    unique_transitions = len(transitions)
                    st.metric("Patrones Únicos", unique_transitions)
                
                # Matriz de transiciones
                st.markdown("### Matriz de Transiciones")
                
                # Crear matriz pivoteada
                transition_matrix = pd.DataFrame()
                for idx, row in transitions.iterrows():
                    if ' → ' in idx:
                        from_zone, to_zone = idx.split(' → ')
                        transition_matrix.loc[from_zone, to_zone] = row['count']
                
                if not transition_matrix.empty:
                    # Llenar NaN con 0
                    transition_matrix = transition_matrix.fillna(0).astype(int)
                    
                    # Heatmap de matriz
                    import plotly.graph_objects as go
                    
                    fig_matrix = go.Figure(data=go.Heatmap(
                        z=transition_matrix.values,
                        x=transition_matrix.columns,
                        y=transition_matrix.index,
                        colorscale='Blues',
                        text=transition_matrix.values,
                        texttemplate='%{text}',
                        textfont={"size": 10}
                    ))
                    
                    fig_matrix.update_layout(
                        title='Matriz de Transiciones entre Zonas',
                        xaxis_title='Zona Destino',
                        yaxis_title='Zona Origen',
                        height=600
                    )
                    
                    st.plotly_chart(fig_matrix, use_container_width=True)
        else:
            st.info("No hay transiciones disponibles para analizar")
    
    with zone_tab4:
        st.subheader("👤 Perfiles de Jugadores por Zona")
        
        # Selector de jugadores
        players_list = df['playerName'].dropna().unique().tolist()
        selected_players = st.multiselect(
            "Seleccionar jugadores para comparar (máx. 5)",
            players_list,
            default=players_list[:3] if len(players_list) >= 3 else players_list,
            max_selections=5
        )
        
        if selected_players:
            # Obtener perfiles
            profiles = []
            for player in selected_players:
                profile = zones.get_player_zone_profile(df, player)
                if profile:
                    profiles.append(profile)
            
            if profiles:
                # Comparación de zonas principales
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Gráfico de radar para comparación
                    import plotly.graph_objects as go
                    
                    fig_radar = go.Figure()
                    
                    # Categorías para el radar
                    categories = ['Defensiva %', 'Mediocampo %', 'Ofensiva %', 
                                 'Diversidad', 'Zonas Cubiertas']
                    
                    for profile in profiles:
                        values = [
                            profile.get('defensive_percentage', 0),
                            profile.get('midfield_percentage', 0),
                            profile.get('offensive_percentage', 0),
                            profile.get('zone_diversity', 0) * 20,  # Escalar para visualización
                            profile.get('zones_covered', 0) * 5    # Escalar para visualización
                        ]
                        
                        fig_radar.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name=profile['player_name']
                        ))
                    
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100]
                            )
                        ),
                        showlegend=True,
                        title="Comparación de Perfiles por Zona"
                    )
                    
                    st.plotly_chart(fig_radar, use_container_width=True)
                
                with col2:
                    st.markdown("### Resumen de Perfiles")
                    
                    for profile in profiles:
                        with st.expander(f"📊 {profile['player_name']}"):
                            st.write(f"**Zona Principal:** {profile['main_zone']}")
                            st.write(f"**% en Zona Principal:** {profile['main_zone_percentage']:.1f}%")
                            st.write(f"**Posición Típica:** {profile['typical_position']}")
                            st.write(f"**Zonas Cubiertas:** {profile['zones_covered']}")
                            st.write(f"**Diversidad:** {profile['zone_diversity']:.2f}")
                
                # Distribución detallada por jugador
                st.markdown("### Distribución Detallada por Zonas")
                
                # Crear DataFrame para comparación
                comparison_data = []
                all_zones = set()
                
                for profile in profiles:
                    for zone, pct in profile['zone_distribution'].items():
                        all_zones.add(zone)
                        comparison_data.append({
                            'Jugador': profile['player_name'],
                            'Zona': zone.replace('Zona ', ''),
                            'Porcentaje': pct
                        })
                
                if comparison_data:
                    comp_df = pd.DataFrame(comparison_data)
                    
                    # Gráfico de barras agrupadas
                    fig_grouped = px.bar(
                        comp_df,
                        x='Zona',
                        y='Porcentaje',
                        color='Jugador',
                        title='Distribución de Eventos por Zona y Jugador',
                        barmode='group',
                        labels={'Porcentaje': '% de Eventos'}
                    )
                    fig_grouped.update_layout(height=500)
                    st.plotly_chart(fig_grouped, use_container_width=True)
                    
                    # Tabla pivotada
                    pivot_table = comp_df.pivot(index='Zona', columns='Jugador', values='Porcentaje').fillna(0)
                    
                    st.markdown("### Tabla Comparativa")
                    st.dataframe(
                        pivot_table.style.background_gradient(
                            cmap='Blues',
                            axis=1
                        ).format("{:.1f}%"),
                        height=400
                    )
        else:
            st.info("Selecciona jugadores para ver sus perfiles por zona")


# ======================================
# FUNCIÓN PARA INTEGRAR EN APP PRINCIPAL
# ======================================

def integrate_zones_in_main_app():
    """
    Código para integrar en tu app.py principal
    Añadir esta función y llamarla desde main()
    """
    
    # En la sección de tabs principales, añadir una nueva:
    # tab1, tab2, tab_carries, tab_zones, tab3, tab4, tab5 = st.tabs([
    #     "📊 Resumen", 
    #     "🏟️ Visualización en Cancha",
    #     "🏃 Análisis de Carries",
    #     "⚡ Zonas Tácticas",  # NUEVA TAB
    #     "👤 Perfiles de Jugadores",
    #     "📈 Análisis Temporal",
    #     "🎯 Análisis Avanzado"
    # ])
    
    # with tab_zones:
    #     add_tactical_zones_tab(df)
    
    pass


# ======================================
# EJEMPLO DE USO STANDALONE
# ======================================

if __name__ == "__main__":
    # Prueba del módulo
    import pandas as pd
    import matplotlib.pyplot as plt
    
    # Crear datos de ejemplo
    sample_data = pd.DataFrame({
        'x': np.random.uniform(0, 120, 1000),
        'y': np.random.uniform(0, 80, 1000),
        'end_x': np.random.uniform(0, 120, 1000),
        'end_y': np.random.uniform(0, 80, 1000),
        'type': np.random.choice(['Pass', 'Carry', 'Shot'], 1000),
        'playerName': np.random.choice(['Jugador A', 'Jugador B', 'Jugador C'], 1000),
        'teamName': np.random.choice(['Equipo 1', 'Equipo 2'], 1000),
        'outcomeType': np.random.choice(['Successful', 'Unsuccessful'], 1000, p=[0.7, 0.3])
    })
    
    # Inicializar sistema de zonas
    zones = TacticalZones()
    
    # Añadir zonas al DataFrame
    data_with_zones = zones.add_zones_to_dataframe(sample_data)
    
    # Visualizar zonas
    fig, ax = plt.subplots(figsize=(14, 9))
    ax = zones.visualize_zones(ax, show_labels=True)
    plt.title("Sistema de Zonas Tácticas", color='white', fontsize=16)
    plt.show()
    
    # Analizar distribución
    zone_stats = zones.analyze_zone_distribution(data_with_zones)
    print("\n=== Distribución de Eventos por Zona ===")
    print(zone_stats[['events_count', 'success_rate', 'zone_type']])
    
    # Analizar transiciones
    transitions = zones.analyze_zone_transitions(data_with_zones)
    print("\n=== Top 10 Transiciones ===")
    print(transitions.head(10))
    
    # Perfil de jugador
    profile = zones.get_player_zone_profile(data_with_zones, 'Jugador A')
    print(f"\n=== Perfil de {profile['player_name']} ===")
    print(f"Zona Principal: {profile['main_zone']} ({profile['main_zone_percentage']:.1f}%)")
    print(f"Posición Típica: {profile['typical_position']}")
    print(f"Diversidad de Zonas: {profile['zone_diversity']:.2f}")