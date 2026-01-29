"""
Script para actualizar passing_network_tab.py con SIDEBAR (panel lateral)
"""

import shutil
from pathlib import Path

# Rutas
original_file = Path(r"C:\Users\frank\ANALISIS DE DATOS\FUTBOL\futbol-event-analytics\passing_network_tab.py")
backup_file = Path(r"C:\Users\frank\ANALISIS DE DATOS\FUTBOL\futbol-event-analytics\passing_network_tab_BACKUP_SIDEBAR.py")
sidebar_function_file = Path(r"C:\Users\frank\ANALISIS DE DATOS\FUTBOL\futbol-event-analytics\SIDEBAR_show_passing_network_tab.txt")

print("=" * 70)
print("🎨 ACTUALIZACIÓN A SIDEBAR (PANEL LATERAL)")
print("=" * 70)
print()

# Crear backup
if original_file.exists():
    shutil.copy2(original_file, backup_file)
    print(f"✅ Backup creado: {backup_file.name}")
else:
    print(f"❌ ERROR: No se encontró el archivo original")
    input("\nPresiona Enter para salir...")
    exit(1)

# Leer archivo original
with open(original_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar inicio de show_passing_network_tab
marker = 'def show_passing_network_tab():'
idx = content.rfind(marker)

if idx == -1:
    print(f"❌ ERROR: No se encontró la función show_passing_network_tab()")
    input("\nPresiona Enter para salir...")
    exit(1)

# Mantener todo hasta la función
before_function = content[:idx]

# Leer la nueva función con SIDEBAR
if not sidebar_function_file.exists():
    print(f"❌ ERROR: No se encontró el archivo con la nueva función")
    print(f"   Ruta esperada: {sidebar_function_file}")
    input("\nPresiona Enter para salir...")
    exit(1)

with open(sidebar_function_file, 'r', encoding='utf-8') as f:
    new_show_function = f.read()

# Combinar todo
final_content = before_function + new_show_function

# Escribir archivo actualizado
with open(original_file, 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"✅ Archivo actualizado correctamente")
print()
print("=" * 70)
print("✅ ACTUALIZACIÓN A SIDEBAR COMPLETADA")
print("=" * 70)
print()
print("🎨 NUEVO DISEÑO:")
print("   ┌─────────────────┬────────────────────────┐")
print("   │ SIDEBAR         │ ÁREA PRINCIPAL         │")
print("   │                 │                        │")
print("   │ ⚙️ Config       │ 🕸️ Passing Network    │")
print("   │ ───────────     │ ────────────────       │")
print("   │ 🏆 Competición  │                        │")
print("   │ [Liga Prof ▼]   │ [VISUALIZACIÓN]        │")
print("   │                 │                        │")
print("   │ 📅 Temporada    │ [Gráficos de red]      │")
print("   │ [2025 ▼]        │                        │")
print("   │                 │ [Tablas]               │")
print("   │ ⚽ Equipo        │                        │")
print("   │ [Boca ▼]        │                        │")
print("   │                 │                        │")
print("   │ 🎯 Tipo         │                        │")
print("   │ ● Más reciente  │                        │")
print("   │ ○ Específico    │                        │")
print("   │                 │                        │")
print("   │ Partidos: 5     │                        │")
print("   └─────────────────┴────────────────────────┘")
print()
print("📋 Próximos pasos:")
print("   1. Ejecuta: streamlit run streamlit_app.py")
print("   2. ¡Disfruta el nuevo diseño con sidebar!")
print()

input("\nPresiona Enter para salir...")
