"""
Módulo de Expected Threat (xT) para Passing Network Analysis
Basado en la grilla de xT de Karun Singh

Integrar este código en passing_network_tab.py
"""

import numpy as np
import pandas as pd

# ============================================
# GRILLA DE xT (valores precalculados)
# ============================================
# Basado en datos de 12x8 grid de Karun Singh
# https://karun.in/blog/expected-threat.html

XT_GRID_12x8 = np.array([
    [0.00126, 0.00126, 0.00126, 0.00163, 0.00204, 0.00204, 0.00163, 0.00126],
    [0.00140, 0.00140, 0.00163, 0.00204, 0.00265, 0.00265, 0.00204, 0.00163],
    [0.00163, 0.00163, 0.00204, 0.00265, 0.00348, 0.00348, 0.00265, 0.00204],
    [0.00204, 0.00204, 0.00265, 0.00348, 0.00470, 0.00470, 0.00348, 0.00265],
    [0.00265, 0.00265, 0.00348, 0.00470, 0.00632, 0.00632, 0.00470, 0.00348],
    [0.00348, 0.00348, 0.00470, 0.00632, 0.00849, 0.00849, 0.00632, 0.00470],
    [0.00470, 0.00470, 0.00632, 0.00849, 0.01142, 0.01142, 0.00849, 0.00632],
    [0.00632, 0.00632, 0.00849, 0.01142, 0.01536, 0.01536, 0.01142, 0.00849],
    [0.00849, 0.00849, 0.01142, 0.01536, 0.02065, 0.02065, 0.01536, 0.01142],
    [0.01142, 0.01142, 0.01536, 0.02065, 0.02776, 0.02776, 0.02065, 0.01536],
    [0.01536, 0.01536, 0.02065, 0.02776, 0.03729, 0.03729, 0.02776, 0.02065],
    [0.02065, 0.02065, 0.02776, 0.03729, 0.05008, 0.05008, 0.03729, 0.02776]
])

def get_xt_value(x, y, pitch_length=105, pitch_width=68):
    """
    Obtiene el valor de xT para una coordenada del campo.
    
    Args:
        x: Coordenada X (0-100 en formato OPTA, o 0-105 en metros)
        y: Coordenada Y (0-100 en formato OPTA, o 0-68 en metros)
        pitch_length: Longitud del campo (default: 105m)
        pitch_width: Ancho del campo (default: 68m)
    
    Returns:
        float: Valor de xT en esa ubicación
    """
    
    # Normalizar a 0-100 si es necesario
    if x > 100:
        x = (x / pitch_length) * 100
    if y > 100:
        y = (y / pitch_width) * 100
    
    # Convertir a índices de la grilla (12x8)
    grid_x = int(min(x / 100 * 12, 11))  # 0-11
    grid_y = int(min(y / 100 * 8, 7))    # 0-7
    
    return XT_GRID_12x8[grid_x, grid_y]


def calculate_xt_for_pass(start_x, start_y, end_x, end_y, pitch_length=105, pitch_width=68):
    """
    Calcula el xT ganado/perdido en un pase.
    
    Args:
        start_x, start_y: Coordenadas de inicio del pase
        end_x, end_y: Coordenadas de fin del pase
    
    Returns:
        float: Delta xT (positivo = ganó amenaza, negativo = perdió)
    """
    
    start_xt = get_xt_value(start_x, start_y, pitch_length, pitch_width)
    end_xt = get_xt_value(end_x, end_y, pitch_length, pitch_width)
    
    return end_xt - start_xt


def calculate_player_xt(passes, player_names):
    """
    Calcula xT acumulado por cada jugador.
    
    Args:
        passes: Lista de diccionarios con pases (debe incluir x, y, end_x, end_y, player_id, outcome)
        player_names: Diccionario {player_id: name}
    
    Returns:
        dict: {player_id: {'name': str, 'xt_total': float, 'passes': int}}
    """
    
    player_xt = {}
    
    for p in passes:
        # Solo pases exitosos
        if not p.get('outcome', False):
            continue
        
        # Solo si tiene coordenadas finales
        if p.get('end_x') is None or p.get('end_y') is None:
            continue
        
        player_id = p['player_id']
        
        # Calcular xT ganado en este pase
        xt_gained = calculate_xt_for_pass(
            p['x'], p['y'],
            p['end_x'], p['end_y']
        )
        
        # Solo contar si ganó amenaza (pases progresivos)
        if xt_gained > 0:
            if player_id not in player_xt:
                player_xt[player_id] = {
                    'name': player_names.get(player_id, f'Player {player_id}'),
                    'xt_total': 0.0,
                    'passes': 0
                }
            
            player_xt[player_id]['xt_total'] += xt_gained
            player_xt[player_id]['passes'] += 1
    
    return player_xt


def calculate_combination_xt(connections, passes, avg_positions):
    """
    Calcula xT para cada combinación de pases entre dos jugadores.
    
    Args:
        connections: dict {(player1_id, player2_id): count}
        passes: Lista de pases
        avg_positions: dict {player_id: {'x': float, 'y': float}}
    
    Returns:
        dict: {(player1_id, player2_id): {'count': int, 'xt_total': float}}
    """
    
    combination_xt = {}
    
    # Inicializar
    for (p1, p2) in connections.keys():
        combination_xt[(p1, p2)] = {
            'count': connections[(p1, p2)],
            'xt_total': 0.0
        }
    
    # Calcular xT para cada pase exitoso
    for p in passes:
        if not p.get('outcome', False):
            continue
        
        if p.get('end_x') is None or p.get('end_y') is None:
            continue
        
        passer_id = p['player_id']
        end_x = p['end_x']
        end_y = p['end_y']
        
        # Encontrar receptor más cercano
        min_distance = float('inf')
        receiver_id = None
        
        for player_id, pos in avg_positions.items():
            if player_id == passer_id:
                continue
            
            distance = ((pos['x'] - end_x)**2 + (pos['y'] - end_y)**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
                receiver_id = player_id
        
        # Si encontramos receptor y la combinación existe
        if receiver_id and min_distance < 25:
            key = (passer_id, receiver_id)
            
            if key in combination_xt:
                xt_gained = calculate_xt_for_pass(
                    p['x'], p['y'],
                    p['end_x'], p['end_y']
                )
                
                if xt_gained > 0:
                    combination_xt[key]['xt_total'] += xt_gained
    
    return combination_xt


# ============================================
# FUNCIÓN PARA COLORES BASADOS EN xT
# ============================================

def get_color_intensity_for_xt(xt_value, max_xt, base_color='cyan'):
    """
    Devuelve un color con intensidad proporcional al xT.
    
    Args:
        xt_value: Valor de xT del jugador
        max_xt: Valor máximo de xT en el equipo
        base_color: 'cyan', 'red', u 'orange'
    
    Returns:
        tuple: (color_rgb, alpha)
    """
    
    # Normalizar entre 0.3 (mínimo visible) y 1.0 (máximo)
    if max_xt == 0:
        intensity = 0.5
    else:
        intensity = 0.3 + (xt_value / max_xt) * 0.7
    
    # Colores base
    colors = {
        'cyan': (0, 217, 255),
        'red': (231, 76, 60),
        'orange': (255, 149, 0)
    }
    
    rgb = colors.get(base_color, colors['cyan'])
    
    return rgb, intensity


# ============================================
# INSTRUCCIONES DE INTEGRACIÓN
# ============================================

"""
PASO 1: Agregar al inicio de passing_network_tab.py (después de imports):

from xt_module import (
    calculate_player_xt,
    calculate_combination_xt,
    get_color_intensity_for_xt
)

PASO 2: Modificar calculate_pass_network_positions() para calcular xT:

def calculate_pass_network_positions(passes, player_names, invert_coords=False):
    # ... código existente ...
    
    # AGREGAR AL FINAL (antes del return):
    
    # Calcular xT por jugador
    player_xt_data = calculate_player_xt(passes, player_names)
    
    # Agregar xT a avg_positions
    for player_id, data in player_xt_data.items():
        if player_id in avg_positions:
            avg_positions[player_id]['xt_total'] = data['xt_total']
    
    # Asegurar que todos tengan xT (0 si no generaron)
    for player_id in avg_positions:
        if 'xt_total' not in avg_positions[player_id]:
            avg_positions[player_id]['xt_total'] = 0.0
    
    # Calcular xT por combinación
    combination_xt_data = calculate_combination_xt(connections, passes, avg_positions)
    
    return avg_positions, connections, combination_xt_data


PASO 3: Modificar plot_passing_network() para usar colores basados en xT:

def plot_passing_network(avg_positions, connections, team_name, ax, min_passes=3, team_color='cyan'):
    # ... código existente hasta dibujar nodos ...
    
    # Calcular max_xt para normalizar colores
    max_xt = max([pos.get('xt_total', 0) for pos in avg_positions.values()])
    
    # En el loop de scatter (jugadores):
    for player_id, pos in avg_positions.items():
        x = pos['x'] * scale_x
        y = pos['y'] * scale_y
        
        # NUEVO: Color basado en xT
        xt_value = pos.get('xt_total', 0)
        color_rgb, alpha = get_color_intensity_for_xt(xt_value, max_xt, team_color)
        color_hex = '#{:02x}{:02x}{:02x}'.format(*color_rgb)
        
        # Tamaño proporcional a pases
        size = max(400, min((passes / max_passes) * 2000, 2500))
        
        # MODIFICAR: Usar color calculado
        ax.scatter(x, y, s=size, c=color_hex, edgecolors='white', 
                  linewidths=3, zorder=2, marker='o', alpha=alpha)


PASO 4: Agregar columna xT a tablas:

# En la sección de "Top 10 Jugadores por Pases":

player_pass_data1.append({
    'Jugador': pos['name'],
    'Pases': pos['passes'],
    'xT': pos.get('xt_total', 0)  # NUEVO
})

# Formatear xT con 3 decimales
df_passes1['xT'] = df_passes1['xT'].apply(lambda x: f"{x:.3f}")


PASO 5: Agregar columna xT a combinaciones:

# En la sección de "Top 10 Combinaciones":

for rank, ((p1, p2), count) in enumerate(top_conn1, 1):
    name1 = players_team1.get(p1, f'P{p1}')
    name2 = players_team1.get(p2, f'P{p2}')
    
    # Obtener xT de esta combinación
    combo_xt = combination_xt_data.get((p1, p2), {}).get('xt_total', 0)
    
    conn_data1.append({
        '#': rank,
        'Combinación': f"{name1} → {name2}",
        'Pases': count,
        'xT': combo_xt  # NUEVO
    })

# Formatear
df_conn1['xT'] = df_conn1['xT'].apply(lambda x: f"{x:.3f}")
"""
