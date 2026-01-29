"""
Script para subir todos los JSONs a Supabase Storage
"""

import os
import json
from pathlib import Path
import requests
from tqdm import tqdm

# ==========================================
# CONFIGURACIÓN - EDITA ESTOS VALORES
# ==========================================

SUPABASE_URL = "https://[TU-PROYECTO].supabase.co"
SUPABASE_KEY = "[TU-API-KEY-AQUI]"  # Copia desde Supabase Dashboard → Settings → API
BUCKET_NAME = "matches"

# ==========================================
# NO EDITES DEBAJO DE ESTA LÍNEA
# ==========================================

def upload_to_supabase(file_path, storage_path):
    """Sube un archivo a Supabase Storage"""
    
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{storage_path}"
    
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, headers=headers, files=files)
    
    return response.status_code == 200

def main():
    raw_dir = Path("data/raw")
    
    print("=" * 70)
    print("📤 SUBIENDO JSONs A SUPABASE STORAGE")
    print("=" * 70)
    print()
    
    # Verificar configuración
    if "[TU-PROYECTO]" in SUPABASE_URL or "[TU-API-KEY" in SUPABASE_KEY:
        print("❌ ERROR: Debes editar SUPABASE_URL y SUPABASE_KEY en este script")
        print()
        print("1. Ve a tu proyecto en Supabase")
        print("2. Settings → API")
        print("3. Copia 'Project URL' y 'anon/public key'")
        input("\nPresiona Enter para salir...")
        return
    
    # Recopilar todos los JSONs
    all_jsons = []
    for json_file in raw_dir.rglob('*.json'):
        if json_file.name == 'matches_metadata.json':
            continue
        
        # Ruta relativa desde raw/
        rel_path = json_file.relative_to(raw_dir)
        all_jsons.append((json_file, str(rel_path).replace('\\', '/')))
    
    print(f"📊 Total de archivos a subir: {len(all_jsons)}")
    print()
    
    # Confirmar
    response = input("¿Continuar con la subida? (s/n): ")
    if response.lower() != 's':
        print("❌ Cancelado")
        return
    
    print()
    print("🚀 Subiendo archivos...")
    print()
    
    success = 0
    failed = 0
    
    for local_path, storage_path in tqdm(all_jsons, desc="Subiendo"):
        if upload_to_supabase(local_path, storage_path):
            success += 1
        else:
            failed += 1
            print(f"\n⚠️  Error subiendo: {storage_path}")
    
    print()
    print("=" * 70)
    print("✅ SUBIDA COMPLETADA")
    print("=" * 70)
    print()
    print(f"📊 Exitosos: {success}")
    print(f"❌ Fallidos: {failed}")
    print()
    print("🌐 Tus archivos están en:")
    print(f"   {SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/")
    print()
    print("💡 Ejemplo de URL:")
    print(f"   {SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/Argentina/Liga_Profesional/2025/abc123.json")
    print()
    input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
