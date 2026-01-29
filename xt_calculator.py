"""
Expected Threat (xT) Calculator
Basado en Karun Singh's xT model
"""

import numpy as np
import pandas as pd

# Matriz xT precalculada (12x8 grid)
XT_MATRIX = np.array([
    [0.00442, 0.00529, 0.00637, 0.00775, 0.00942, 0.01142, 0.01382, 0.01654, 0.01982, 0.02383, 0.02875, 0.03461],
    [0.00473, 0.00566, 0.00681, 0.00825, 0.01003, 0.01213, 0.01466, 0.01758, 0.02108, 0.02532, 0.03050, 0.03672],
    [0.00486, 0.00584, 0.00702, 0.00847, 0.01028, 0.01240, 0.01496, 0.01792, 0.02146, 0.02577, 0.03104, 0.03737],
    [0.00488, 0.00586, 0.00705, 0.00852, 0.01033, 0.01247, 0.01504, 0.01801, 0.02156, 0.02589, 0.03118, 0.03754],
    [0.00487, 0.00585, 0.00703, 0.00849, 0.01029, 0.01242, 0.01497, 0.01793, 0.02147, 0.02578, 0.03105, 0.03739],
    [0.00481, 0.00577, 0.00693, 0.00837, 0.01015, 0.01226, 0.01478, 0.01770, 0.02119, 0.02544, 0.03064, 0.03690],
    [0.00448, 0.00537, 0.00645, 0.00780, 0.00946, 0.01142, 0.01377, 0.01649, 0.01975, 0.02372, 0.02857, 0.03440],
    [0.00361, 0.00433, 0.00520, 0.00629, 0.00763, 0.00921, 0.01111, 0.01331, 0.01594, 0.01915, 0.02306, 0.02776]
]).T

def get_xt_value(x, y, grid_width=12, grid_height=8):
    """Obtiene el valor xT para una coordenada"""
    grid_x = int(np.clip(x / 100 * grid_width, 0, grid_width - 1))
    grid_y = int(np.clip(y / 100 * grid_height, 0, grid_height - 1))
    return XT_MATRIX[grid_x, grid_y]

def calculate_pass_xt(start_x, start_y, end_x, end_y):
    """Calcula el xT generado por un pase"""
    if pd.isna(end_x) or pd.isna(end_y):
        return 0.0
    xt_start = get_xt_value(start_x, start_y)
    xt_end = get_xt_value(end_x, end_y)
    return xt_end - xt_start

def calculate_player_xt(passes_df):
    """Calcula el xT total generado por cada jugador"""
    player_xt = {}
    for idx, pass_row in passes_df.iterrows():
        if not pass_row['outcome']:
            continue
        if pd.isna(pass_row['end_x']) or pd.isna(pass_row['end_y']):
            continue
        player_id = pass_row['player_id']
        xt = calculate_pass_xt(
            pass_row['x'], pass_row['y'],
            pass_row['end_x'], pass_row['end_y']
        )
        player_xt[player_id] = player_xt.get(player_id, 0) + xt
    return player_xt

def calculate_connection_xt(passes_df, passer_id, receiver_id):
    """Calcula el xT total de una conexión específica"""
    connection_passes = passes_df[
        (passes_df['player_id'] == passer_id) &
        (passes_df['receiver_id'] == receiver_id) &
        (passes_df['outcome'] == True)
    ]
    total_xt = 0
    for idx, pass_row in connection_passes.iterrows():
        if pd.isna(pass_row['end_x']) or pd.isna(pass_row['end_y']):
            continue
        xt = calculate_pass_xt(
            pass_row['x'], pass_row['y'],
            pass_row['end_x'], pass_row['end_y']
        )
        total_xt += xt
    return total_xt

def add_xt_to_passes(passes_list):
    """Agrega el valor xT a cada pase en una lista"""
    for pass_dict in passes_list:
        if pass_dict['outcome'] and pass_dict['end_x'] is not None:
            xt = calculate_pass_xt(
                pass_dict['x'], pass_dict['y'],
                pass_dict['end_x'], pass_dict['end_y']
            )
            pass_dict['xt'] = xt
        else:
            pass_dict['xt'] = 0.0
    return passes_list

def get_xt_color_intensity(xt_value, max_xt):
    """Convierte un valor xT a intensidad de color"""
    if max_xt == 0:
        return 0.5
    normalized = xt_value / max_xt
    return 0.3 + (normalized * 0.7)
