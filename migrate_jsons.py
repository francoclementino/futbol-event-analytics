#!/usr/bin/env python3
"""
Script para migrar y organizar JSONs existentes de SCORESWAY BD Eventing
a la nueva estructura jerárquica.
"""

import json
import shutil
from pathlib import Path
import sys

def normalize_name(name):
    """Normaliza nombres de carpetas: elimina espacios, paréntesis, etc."""
    # Reemplazar espacios con guiones bajos
    name = name.replace(' ', '_')
    # Eliminar paréntesis y contenido
    name = name.split('(')[0].strip('_')
    # Capitalizar apropiadamente
    return name

def map_country_name(old_name):
    """Mapea nombres de países antiguos a nuevos."""
    mapping = {
        'ARGENTINA': 'Argentina',
        'CHILE': 'Chile',
        'COLOMBIA': 'Colombia',
        'ECUADOR': 'Ecuador',
        'PARAGUAY': 'Paraguay',
        'PERU': 'Peru',
        'MEXICO': 'Mexico',
        'BRASIL': 'Brasil',
        'BRAZIL': 'Brasil'
    }
    return mapping.get(old_name.upper(), old_name.title())

def map_competition_name(old_name):
    """Mapea nombres de competiciones antiguos a nuevos."""
    mapping = {
        'PRIMERA DIVISION': 'Liga_Profesional',
        'PRIMERA DIVISIÓN': 'Liga_Profesional',
        'LIGA PROFESIONAL': 'Liga_Profesional',
        'COPA ARGENTINA': 'Copa_Argentina',
        'PRIMERA A': 'Primera_Division',
        'LIGA BETPLAY': 'Liga_BetPlay',
        'SERIE A': 'Serie_A',
        'LIGA MX': 'Liga_MX',
        'MLS': 'MLS'
    }
    return mapping.get(old_name.upper(), normalize_name(old_name))

def migrate_jsons(source_dir, target_dir):
    """
    Migra JSONs desde SCORESWAY BD Eventing a la nueva estructura.
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        print(f"❌ Error: La carpeta origen no existe: {source_dir}")
        return False
    
    print("=" * 70)
    print("🔄 MIGRACIÓN DE JSONs A NUEVA ESTRUCTURA")
    print("=" * 70)
    print(f"\n📂 Origen: {source_path}")
    print(f"📁 Destino: {target_path}")
    print()
    
    total_copied = 0
    total_errors = 0
    
    # Recorrer países
    for country_dir in source_path.iterdir():
        if not country_dir.is_dir():
            continue
        
        # Ignorar carpetas especiales (Copas internacionales por ahora)
        if 'COPA' in country_dir.name.upper() or 'MUNDIAL' in country_dir.name.upper():
            print(f"⏭️  Ignorando: {country_dir.name} (copas internacionales)")
            continue
        
        country_name = map_country_name(country_dir.name)
        print(f"\n🌎 Procesando: {country_dir.name} → {country_name}")
        
        # Recorrer competiciones
        for comp_dir in country_dir.iterdir():
            if not comp_dir.is_dir():
                continue
            
            comp_name = map_competition_name(comp_dir.name)
            print(f"  🏆 {comp_dir.name} → {comp_name}")
            
            # Recorrer temporadas
            for season_dir in comp_dir.iterdir():
                if not season_dir.is_dir():
                    continue
                
                # Extraer solo el año de la temporada
                season_name = season_dir.name.split()[0]  # Tomar solo "2024" o "2025"
                
                print(f"    📅 {season_dir.name} → {season_name}")
                
                # Crear carpeta destino
                target_season_dir = target_path / country_name / comp_name / season_name
                target_season_dir.mkdir(parents=True, exist_ok=True)
                
                # Copiar JSONs
                json_count = 0
                for json_file in season_dir.glob('*.json'):
                    try:
                        target_file = target_season_dir / json_file.name
                        
                        # Si el archivo ya existe, no sobreescribir
                        if target_file.exists():
                            print(f"      ⏭️  Ya existe: {json_file.name}")
                            continue
                        
                        shutil.copy2(json_file, target_file)
                        json_count += 1
                        total_copied += 1
                        
                    except Exception as e:
                        print(f"      ❌ Error copiando {json_file.name}: {e}")
                        total_errors += 1
                
                if json_count > 0:
                    print(f"      ✅ Copiados: {json_count} archivos")
    
    print("\n" + "=" * 70)
    print(f"✅ MIGRACIÓN COMPLETADA")
    print("=" * 70)
    print(f"\n📊 Resumen:")
    print(f"  • Archivos copiados: {total_copied}")
    print(f"  • Errores: {total_errors}")
    print()
    
    if total_copied > 0:
        print("💡 Próximo paso:")
        print("   Ejecuta: python generate_metadata.py")
        return True
    else:
        print("⚠️  No se copiaron archivos (posiblemente ya existían)")
        return False

def main():
    # Rutas
    source_dir = r"C:\Users\frank\ANALISIS DE DATOS\FUTBOL\PROYECTO DATA EVENTING SCORESWAY\SCORESWAY BD Eventing"
    target_dir = Path(__file__).parent / 'data' / 'raw'
    
    success = migrate_jsons(source_dir, target_dir)
    
    if success:
        print("\n✅ Listo para generar metadata!")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
