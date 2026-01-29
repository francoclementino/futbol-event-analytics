# 📁 Estructura de Carpetas para JSONs de Partidos

## 🎯 Organización

Los archivos JSON de partidos deben organizarse en la siguiente estructura:

```
data/raw/
├── País/
│   ├── Competición/
│   │   ├── Temporada/
│   │   │   ├── match_id_1.json
│   │   │   ├── match_id_2.json
│   │   │   └── ...
│   │   └── matches_metadata.json
│   └── matches_metadata.json
└── matches_metadata.json
```

## 📂 Ejemplo Concreto

```
data/raw/
├── Argentina/
│   ├── Liga_Profesional/
│   │   ├── 2024/
│   │   │   ├── 1a6frpeulm8etpskntuyhh3pw.json
│   │   │   └── 2b7gsqnfzmxfty2r5ukzm9abc.json
│   │   ├── 2025/
│   │   │   └── 3c8htroglanyuz3s6vlano1cd.json
│   │   └── matches_metadata.json
│   │
│   ├── Copa_Argentina/
│   │   ├── 2024/
│   │   ├── 2025/
│   │   └── matches_metadata.json
│   │
│   └── matches_metadata.json
│
├── Chile/
│   ├── Primera_Division/
│   │   ├── 2024/
│   │   ├── 2025/
│   │   └── matches_metadata.json
│   └── matches_metadata.json
│
└── matches_metadata.json
```

## 🚀 Cómo Usar

### 1️⃣ Organizar tus JSONs

Coloca tus archivos JSON en la estructura de carpetas apropiada:
- **País**: Nombre del país (sin espacios, use mayúsculas)
- **Competición**: Nombre de la liga/torneo (use guiones bajos en lugar de espacios)
- **Temporada**: Año de la temporada (ej: 2024, 2025)

**Ejemplos de nombres correctos:**
- ✅ `Argentina/Liga_Profesional/2025/`
- ✅ `Chile/Primera_Division/2024/`
- ✅ `Colombia/Liga_BetPlay/2025/`
- ✅ `Brasil/Serie_A/2024/`

**Evitar:**
- ❌ `argentina/liga profesional/2025/` (minúsculas y espacios)
- ❌ `Argentina/Liga-Profesional/2025/` (guiones en lugar de guiones bajos)

### 2️⃣ Generar Metadata

Una vez que hayas organizado tus JSONs, ejecuta el script generador:

```bash
python generate_metadata.py
```

Este script:
- Escanea automáticamente todas las carpetas
- Lee cada archivo JSON
- Extrae información relevante (equipos, fecha, competición, etc.)
- Genera archivos `matches_metadata.json` en cada nivel

### 3️⃣ Usar en Streamlit

Después de generar la metadata, abre la aplicación:

```bash
streamlit run streamlit_app.py
```

La interfaz te permitirá:
- Filtrar por país
- Filtrar por competición  
- Filtrar por temporada
- Buscar por nombre de equipo
- Ver todos los partidos disponibles

## 📊 Archivos de Metadata

El script genera 3 niveles de archivos `matches_metadata.json`:

1. **Global** (`data/raw/matches_metadata.json`):
   - Contiene TODOS los partidos de todos los países
   
2. **Por País** (`data/raw/Argentina/matches_metadata.json`):
   - Contiene todos los partidos de ese país
   
3. **Por Competición** (`data/raw/Argentina/Liga_Profesional/matches_metadata.json`):
   - Contiene solo partidos de esa competición específica

## 🔄 Actualizar Metadata

Cada vez que agregues nuevos JSONs, simplemente vuelve a ejecutar:

```bash
python generate_metadata.py
```

El script regenerará todos los archivos de metadata automáticamente.

## ⚠️ Importante

- **NO** modifiques manualmente los archivos `matches_metadata.json`
- Los archivos JSON originales deben mantener su ID como nombre
- Asegúrate de que los JSONs estén en el formato correcto de Stats Perform/Opta

## 💡 Países Sudamericanos Soportados

Estructura ya creada para:
- 🇦🇷 Argentina (Liga Profesional, Copa Argentina)
- 🇨🇱 Chile (Primera División)
- 🇨🇴 Colombia (Liga BetPlay)
- 🇧🇷 Brasil (Serie A)

Puedes agregar más países y competiciones simplemente creando las carpetas correspondientes.
