"""
Script simple para actualizar passing_network_tab.py con el sistema de metadata.
Ejecuta este script después de migrate_jsons.py y generate_metadata.py
"""

import shutil
from pathlib import Path

# Hacer backup del archivo original
original_file = Path(r"C:\Users\frank\ANALISIS DE DATOS\FUTBOL\futbol-event-analytics\passing_network_tab.py")
backup_file = Path(r"C:\Users\frank\ANALISIS DE DATOS\FUTBOL\futbol-event-analytics\passing_network_tab_BACKUP.py")

print("=" * 70)
print("🔄 ACTUALIZACIÓN DE PASSING_NETWORK_TAB.PY")
print("=" * 70)
print()

# Crear backup
if original_file.exists():
    shutil.copy2(original_file, backup_file)
    print(f"✅ Backup creado: {backup_file.name}")
else:
    print(f"❌ ERROR: No se encontró el archivo original")
    print(f"   Ruta esperada: {original_file}")
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

# Nueva función load_matches_metadata
new_load_metadata = '''
def load_matches_metadata(raw_dir, scope='global', country=None, competition=None):
    """
    Carga metadata de partidos según el nivel de scope solicitado.
    
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
                return df.sort_values('date', ascending=False)
        except Exception as e:
            st.error(f"Error cargando metadata: {e}")
    
    return None

'''

# Leer la nueva función show_passing_network_tab desde el archivo txt
new_function_file = Path(r"C:\Users\frank\ANALISIS DE DATOS\FUTBOL\futbol-event-analytics\NEW_show_passing_network_tab.txt")

if not new_function_file.exists():
    print(f"❌ ERROR: No se encontró el archivo con la nueva función")
    print(f"   Ruta esperada: {new_function_file}")
    input("\nPresiona Enter para salir...")
    exit(1)

with open(new_function_file, 'r', encoding='utf-8') as f:
    new_show_function = f.read()

# Combinar todo
final_content = before_function + new_load_metadata + new_show_function

# Escribir archivo actualizado
with open(original_file, 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"✅ Archivo actualizado correctamente")
print()
print("=" * 70)
print("✅ ACTUALIZACIÓN COMPLETADA")
print("=" * 70)
print()
print("📋 Próximos pasos:")
print("   1. Ejecuta: python migrate_jsons.py")
print("   2. Ejecuta: python generate_metadata.py")
print("   3. Prueba Streamlit: streamlit run streamlit_app.py")
print()

input("\nPresiona Enter para salir...")
