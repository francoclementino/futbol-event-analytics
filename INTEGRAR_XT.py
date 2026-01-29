"""
Script para integrar Expected Threat (xT) en passing_network_tab.py
"""

from pathlib import Path
import re

print("=" * 70)
print("🎯 INTEGRACIÓN DE xT EN PASSING NETWORK")
print("=" * 70)
print()

file_path = Path(r"C:\Users\frank\ANALISIS DE DATOS\FUTBOL\futbol-event-analytics\passing_network_tab.py")

# Leer archivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
backup_path = file_path.with_suffix('.py.xt_backup')
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✅ Backup: {backup_path.name}")

# ============================================
# 1. AGREGAR IMPORT DE xT
# ============================================

import_marker = "import tempfile"
new_import = """import tempfile
from xt_calculator import (
    calculate_player_xt,
    calculate_connection_xt,
    add_xt_to_passes,
    get_xt_color_intensity
)"""

if import_marker in content and "from xt_calculator import" not in content:
    content = content.replace(import_marker, new_import)
    print("✅ 1. Import de xt_calculator agregado")

# ============================================
# 2. MODIFICAR calculate_pass_network_positions
# ============================================

# Buscar el final de la función (antes del return)
marker_return = "return avg_positions, connections"

if marker_return in content:
    new_return = """
    # Calcular xT por jugador
    passes_data = []
    for p in passes:
        if p['outcome'] and p.get('end_x') is not None:
            passes_data.append({
                'player_id': p['player_id'],
                'x': p['x'],
                'y': p['y'],
                'end_x': p['end_x'],
                'end_y': p['end_y'],
                'outcome': p['outcome'],
                'receiver_id': None  # Se llenará después
            })
    
    passes_df = pd.DataFrame(passes_data) if passes_data else pd.DataFrame()
    
    if not passes_df.empty:
        player_xt_dict = calculate_player_xt(passes_df)
        
        # Agregar xT a avg_positions
        for player_id in avg_positions:
            avg_positions[player_id]['xt'] = player_xt_dict.get(player_id, 0.0)
    else:
        for player_id in avg_positions:
            avg_positions[player_id]['xt'] = 0.0
    
    # Calcular xT por conexión
    connection_xt = {}
    for (p1, p2), count in connections.items():
        if not passes_df.empty:
            # Aproximar receptor basado en posición final
            connection_passes = [p for p in passes if p['player_id'] == p1 and p['outcome']]
            xt_total = 0
            for cp in connection_passes:
                if cp.get('end_x') is not None:
                    # Calcular distancia a posición promedio del receptor
                    if p2 in avg_positions:
                        dist = ((avg_positions[p2]['x'] - cp['end_x'])**2 + 
                               (avg_positions[p2]['y'] - cp['end_y'])**2)**0.5
                        if dist < 25:  # Umbral de proximidad
                            from xt_calculator import calculate_pass_xt
                            xt = calculate_pass_xt(cp['x'], cp['y'], cp['end_x'], cp['end_y'])
                            xt_total += xt
            connection_xt[(p1, p2)] = xt_total
        else:
            connection_xt[(p1, p2)] = 0.0
    
    return avg_positions, connections, connection_xt"""
    
    content = content.replace(marker_return, new_return)
    print("✅ 2. Cálculo de xT agregado a calculate_pass_network_positions")

# ============================================
# 3. MODIFICAR plot_passing_network
# ============================================

# Buscar donde se definen los colores
color_marker = "    # Colores por equipo"
if color_marker in content:
    new_color_code = """    # Colores por equipo
    
    # Calcular xT máximo para normalizar colores
    max_xt = max([pos.get('xt', 0) for pos in avg_positions.values()])
    if max_xt == 0:
        max_xt = 1  # Evitar división por cero"""
    
    content = content.replace(color_marker, new_color_code)
    print("✅ 3. Preparación de max_xt agregada")

# Modificar scatter de nodos
scatter_marker = "        ax.scatter(x, y, s=size, c=color, edgecolors='white'"

if scatter_marker in content:
    # Buscar todo el bloque scatter y reemplazarlo
    pattern = r"ax\.scatter\(x, y, s=size, c=color, edgecolors='white'[^)]+\)"
    
    new_scatter = """ax.scatter(x, y, s=size, c=color, edgecolors='white',
                   linewidths=3, zorder=2, marker='o',
                   alpha=get_xt_color_intensity(pos.get('xt', 0), max_xt))"""
    
    content = re.sub(pattern, new_scatter, content)
    print("✅ 4. Alpha basado en xT aplicado a nodos")

# ============================================
# 4. AGREGAR COLUMNA xT A TABLAS
# ============================================

# Tabla de jugadores
table_marker = """player_pass_data1.append({
                    'Jugador': pos['name'],
                    'Pases': pos['passes']
                })"""

new_table = """player_pass_data1.append({
                    'Jugador': pos['name'],
                    'Pases': pos['passes'],
                    'xT': pos.get('xt', 0)
                })"""

if table_marker in content:
    content = content.replace(table_marker, new_table)
    print("✅ 5. Columna xT agregada a tabla de jugadores (equipo 1)")

# Repetir para equipo 2
table_marker2 = """player_pass_data2.append({
                    'Jugador': pos['name'],
                    'Pases': pos['passes']
                })"""

new_table2 = """player_pass_data2.append({
                    'Jugador': pos['name'],
                    'Pases': pos['passes'],
                    'xT': pos.get('xt', 0)
                })"""

if table_marker2 in content:
    content = content.replace(table_marker2, new_table2)
    print("✅ 6. Columna xT agregada a tabla de jugadores (equipo 2)")

# Formatear columna xT
format_marker = "            df_passes1 = pd.DataFrame(player_pass_data1)"
new_format = """            df_passes1 = pd.DataFrame(player_pass_data1)
            if 'xT' in df_passes1.columns:
                df_passes1['xT'] = df_passes1['xT'].apply(lambda x: f"{x:.3f}")"""

if format_marker in content:
    content = content.replace(format_marker, new_format)
    print("✅ 7. Formato de xT agregado (3 decimales)")

# Repetir para equipo 2
format_marker2 = "            df_passes2 = pd.DataFrame(player_pass_data2)"
new_format2 = """            df_passes2 = pd.DataFrame(player_pass_data2)
            if 'xT' in df_passes2.columns:
                df_passes2['xT'] = df_passes2['xT'].apply(lambda x: f"{x:.3f}")"""

if format_marker2 in content:
    content = content.replace(format_marker2, new_format2)

# ============================================
# 5. AGREGAR xT A TABLA DE COMBINACIONES
# ============================================

combo_marker = """conn_data1.append({
                        '#': rank,
                        'Combinación': f"{name1} → {name2}",
                        'Pases': count
                    })"""

new_combo = """conn_data1.append({
                        '#': rank,
                        'Combinación': f"{name1} → {name2}",
                        'Pases': count,
                        'xT': connection_xt.get((p1, p2), 0)
                    })"""

if combo_marker in content:
    content = content.replace(combo_marker, new_combo)
    print("✅ 8. Columna xT agregada a tabla de combinaciones (equipo 1)")

# Repetir para equipo 2
combo_marker2 = """conn_data2.append({
                        '#': rank,
                        'Combinación': f"{name1} → {name2}",
                        'Pases': count
                    })"""

new_combo2 = """conn_data2.append({
                        '#': rank,
                        'Combinación': f"{name1} → {name2}",
                        'Pases': count,
                        'xT': connection_xt.get((p1, p2), 0)
                    })"""

if combo_marker2 in content:
    content = content.replace(combo_marker2, new_combo2)
    print("✅ 9. Columna xT agregada a tabla de combinaciones (equipo 2)")

# Formatear xT en combinaciones
combo_format = "            df_conn1 = pd.DataFrame(conn_data1)"
new_combo_format = """            df_conn1 = pd.DataFrame(conn_data1)
            if 'xT' in df_conn1.columns:
                df_conn1['xT'] = df_conn1['xT'].apply(lambda x: f"{x:.3f}")"""

if combo_format in content:
    content = content.replace(combo_format, new_combo_format)
    print("✅ 10. Formato xT en combinaciones aplicado")

# Repetir para equipo 2
combo_format2 = "            df_conn2 = pd.DataFrame(conn_data2)"
new_combo_format2 = """            df_conn2 = pd.DataFrame(conn_data2)
            if 'xT' in df_conn2.columns:
                df_conn2['xT'] = df_conn2['xT'].apply(lambda x: f"{x:.3f}")"""

if combo_format2 in content:
    content = content.replace(combo_format2, new_combo_format2)

# ============================================
# 6. ACTUALIZAR LLAMADAS A calculate_pass_network_positions
# ============================================

# Buscar todas las llamadas y agregar connection_xt al unpacking
old_call = "avg_pos_team1, connections_team1 = calculate_pass_network_positions"
new_call = "avg_pos_team1, connections_team1, connection_xt = calculate_pass_network_positions"

content = content.replace(old_call, new_call)

old_call2 = "avg_pos_team2, connections_team2 = calculate_pass_network_positions"
new_call2 = "avg_pos_team2, connections_team2, connection_xt = calculate_pass_network_positions"

content = content.replace(old_call2, new_call2)
print("✅ 11. Llamadas a función actualizadas")

# Guardar
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print()
print("=" * 70)
print("✅ INTEGRACIÓN DE xT COMPLETADA")
print("=" * 70)
print()
print("Características agregadas:")
print("  🎨 Colores por xT (más intenso = más xT)")
print("  📊 Columna 'xT' en tabla de jugadores")
print("  📊 Columna 'xT' en tabla de combinaciones")
print("  🔢 Formato con 3 decimales")
print()
print("Próximos pasos:")
print("  1. Ejecuta: streamlit run app.py")
print("  2. Selecciona un partido")
print("  3. ¡Verás xT en todo!")
print()

input("Presiona Enter para continuar...")
