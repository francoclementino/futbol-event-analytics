#!/usr/bin/env python3
"""
Script para generar archivos matches_metadata.json desde los JSONs organizados.
Escanea la estructura de carpetas País/Competición/Temporada y genera metadata en cada nivel.

Uso: python generate_metadata.py
"""

import json
from pathlib import Path
import sys

def generate_metadata_from_jsons(raw_dir):
    """
    Genera archivos matches_metadata.json para cada nivel de la jerarquía.
    
    Estructura esperada:
    data/raw/
        ├── País/
        │   ├── Competición/
        │   │   ├── Temporada/
        │   │   │   ├── match1.json
        │   │   │   └── match2.json
        │   │   └── matches_metadata.json
        │   └── matches_metadata.json
        └── matches_metadata.json
    """
    raw_path = Path(raw_dir)
    
    if not raw_path.exists():
        print(f"❌ Error: La carpeta {raw_dir} no existe")
        return False
    
    # Metadata global
    global_metadata = []
    
    print("🔍 Escaneando estructura de carpetas...")
    
    # Recorrer países
    for country_dir in sorted(raw_path.iterdir()):
        if not country_dir.is_dir() or country_dir.name.startswith('.'):
            continue
        
        country_name = country_dir.name
        country_metadata = []
        
        print(f"\n📂 {country_name}")
        
        # Recorrer competiciones
        for comp_dir in sorted(country_dir.iterdir()):
            if not comp_dir.is_dir() or comp_dir.name.startswith('.'):
                continue
            
            comp_name = comp_dir.name
            comp_metadata = []
            
            print(f"  📁 {comp_name}")
            
            # Recorrer temporadas
            for season_dir in sorted(comp_dir.iterdir()):
                if not season_dir.is_dir() or season_dir.name.startswith('.'):
                    continue
                
                season_name = season_dir.name
                json_count = 0
                
                # Procesar JSONs en esta temporada
                for json_file in sorted(season_dir.glob('*.json')):
                    if json_file.name == 'matches_metadata.json':
                        continue
                    
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        match_info = data.get('matchInfo', {})
                        
                        # Extraer información relevante
                        match_data = {
                            'id': match_info.get('id', ''),
                            'filename': json_file.name,
                            'filepath': str(json_file.relative_to(raw_path)),
                            'country': country_name,
                            'competition': comp_name,
                            'competition_full_name': match_info.get('competition', {}).get('name', comp_name),
                            'competition_code': match_info.get('competition', {}).get('competitionCode', ''),
                            'season': season_name,
                            'date': match_info.get('localDate', ''),
                            'time': match_info.get('localTime', ''),
                            'description': match_info.get('description', ''),
                            'stage': match_info.get('stage', {}).get('name', ''),
                            'week': match_info.get('week', '')
                        }
                        
                        # Agregar a todos los niveles
                        comp_metadata.append(match_data)
                        country_metadata.append(match_data)
                        global_metadata.append(match_data)
                        
                        json_count += 1
                        
                    except Exception as e:
                        print(f"    ⚠️  Error procesando {json_file.name}: {e}")
                        continue
                
                if json_count > 0:
                    print(f"    ✅ {season_name}: {json_count} partidos")
            
            # Guardar metadata de competición
            if comp_metadata:
                comp_metadata_file = comp_dir / 'matches_metadata.json'
                with open(comp_metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(comp_metadata, f, ensure_ascii=False, indent=2)
                print(f"  💾 Generado: {comp_metadata_file.relative_to(raw_path)}")
        
        # Guardar metadata de país
        if country_metadata:
            country_metadata_file = country_dir / 'matches_metadata.json'
            with open(country_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(country_metadata, f, ensure_ascii=False, indent=2)
            print(f"💾 Generado: {country_metadata_file.relative_to(raw_path)}")
    
    # Guardar metadata global
    if global_metadata:
        global_metadata_file = raw_path / 'matches_metadata.json'
        with open(global_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(global_metadata, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Generado: matches_metadata.json (GLOBAL)")
        print(f"\n✅ Total de partidos procesados: {len(global_metadata)}")
        
        # Estadísticas
        print("\n📊 Resumen:")
        countries = {}
        for match in global_metadata:
            country = match['country']
            if country not in countries:
                countries[country] = 0
            countries[country] += 1
        
        for country, count in sorted(countries.items()):
            print(f"  🌎 {country}: {count} partidos")
        
        return True
    else:
        print("\n⚠️  No se encontraron archivos JSON para procesar")
        print("💡 Asegúrate de tener JSONs en la estructura: País/Competición/Temporada/")
        return False

def main():
    # Determinar la ruta base del proyecto
    script_dir = Path(__file__).parent
    raw_dir = script_dir / 'data' / 'raw'
    
    print("=" * 60)
    print("🏆 GENERADOR DE METADATA PARA PASSING NETWORK ANALYZER")
    print("=" * 60)
    print(f"\n📁 Carpeta base: {raw_dir}")
    
    success = generate_metadata_from_jsons(raw_dir)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print("\n💡 Ahora puedes usar Streamlit para analizar los partidos")
        print("   Ejecuta: streamlit run streamlit_app.py")
    else:
        print("\n" + "=" * 60)
        print("❌ PROCESO COMPLETADO CON ERRORES")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
