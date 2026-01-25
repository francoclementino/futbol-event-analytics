# ⚽ Football Analytics Dashboard

Sistema completo de análisis de fútbol con datos OPTA F24, incluyendo procesamiento por lotes y aplicación web interactiva con Streamlit.

---

## 📋 Contenido

- **`main.py`** - Procesador por lotes para análisis masivo de partidos
- **`streamlit_app.py`** - Aplicación web interactiva
- **`passing_network_tab.py`** - Módulo de análisis de redes de pases
- **`config.py`** - Configuración centralizada
- **`opta_events.json`** - Diccionario de 75 tipos de eventos OPTA
- **`opta_qualifiers.json`** - Diccionario de 311 qualifiers OPTA

---

## 🚀 Instalación Rápida

### 1. Estructura de carpetas

```
tu-proyecto/
├── main.py                     # Procesador por lotes
├── streamlit_app.py            # App web
├── passing_network_tab.py      # Módulo de redes
├── config.py                   # Configuración
├── opta_events.json            # Eventos OPTA
├── opta_qualifiers.json        # Qualifiers OPTA
├── requirements.txt            # Dependencias
├── data/                       # CREAR ESTA CARPETA
│   ├── raw/                    # Archivos F24 JSON aquí
│   └── processed/              # Salida del procesador
└── README.md
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

O manualmente:

```bash
pip install pandas numpy pyarrow openpyxl streamlit matplotlib mplsoccer
```

### 3. Preparar datos

```bash
# Crear carpeta de datos
mkdir -p data/raw
mkdir -p data/processed

# Copiar tus archivos F24 JSON a data/raw/
cp tus_archivos_f24/*.json data/raw/
```

---

## 🎯 Uso

### Opción 1: Aplicación Web (Streamlit)

**Para análisis interactivo y visualizaciones:**

```bash
streamlit run streamlit_app.py
```

Se abrirá en `http://localhost:8501`

**Funcionalidades:**
- 🕸️ **Passing Network**: Comparación lado a lado de redes de pases
- 📊 **Match Stats**: (Próximamente)
- 📈 **xT Analysis**: (Próximamente)
- 🎯 **Shot Analysis**: (Próximamente)
- 🏃 **Carry Analysis**: (Próximamente)

---

### Opción 2: Procesador por Lotes (main.py)

**Para procesamiento masivo de múltiples partidos:**

```bash
python main.py
```

**Menú interactivo:**

```
1. Procesar UN partido específico
2. Procesar TODOS los partidos en carpeta principal
3. Procesar TODOS (incluir subcarpetas)
4. Ver configuración actual
5. Salir
```

**Salida:**
- Archivos `.parquet` o `.csv` en `data/processed/`
- Resumen de estadísticas
- Detecta carries automáticamente
- Calcula posesiones

---

## 📊 Datos de Salida

### Columnas principales generadas:

**Eventos básicos:**
- `match_id`, `team_id`, `player_id`
- `type`, `type_name` (ej: "Pass", "Shot")
- `x`, `y` (coordenadas OPTA 0-100)
- `period_id`, `min`, `sec`
- `outcome` (1=exitoso, 0=fallido)

**Carries detectados:**
- `carry_distance` (metros)
- `carry_duration` (segundos)
- `carry_end_x`, `carry_end_y`
- `take_ons_during` (regates en el carry)

**Análisis avanzado:**
- `possession_id`
- `xT` (Expected Threat - próximamente)
- Zonas tácticas

---

## ⚙️ Configuración

### Archivo `config.py`

```python
# Detección de Carries
CARRY_CONFIG = {
    'min_length': 3.0,    # Metros mínimos
    'max_length': 70.0,   # Metros máximos
    'max_time_gap': 10.0, # Segundos máximos
}

# Formato de salida
OUTPUT_CONFIG = {
    'format': 'parquet',           # 'parquet' o 'csv'
    'compression': 'gzip',         # Compresión
    'save_by_match': False,        # Archivo por partido
    'save_consolidated': True,     # Archivo único
}
```

---

## 📖 Diccionarios OPTA

### `opta_events.json`

75 tipos de eventos mapeados:

```json
{
  "1": {"name": "Pass", "description": "Any pass attempt"},
  "3": {"name": "Take On", "description": "Attempt to dribble past opponent"},
  "7": {"name": "Tackle", "description": "A tackle attempt"},
  "16": {"name": "Goal", "description": "Goal scored"},
  ...
}
```

### `opta_qualifiers.json`

311 qualifiers mapeados:

```json
{
  "1": {"name": "Long ball", "description": "Pass over 32 metres"},
  "2": {"name": "Cross", "description": "Ball played into the box"},
  "140": {"name": "Pass End X", "description": "End point x coordinate"},
  ...
}
```

---

## 🛠️ Personalización

### Agregar nueva pestaña en Streamlit

1. Crear nuevo archivo: `nueva_tab.py`

```python
import streamlit as st

def show_nueva_tab():
    st.header("Mi Nueva Pestaña")
    # Tu código aquí
```

2. Modificar `streamlit_app.py`:

```python
from nueva_tab import show_nueva_tab

tabs = st.tabs(["🕸️ Passing Network", "🆕 Nueva Tab", ...])

with tabs[1]:
    show_nueva_tab()
```

---

## 🔍 Ejemplos de Uso

### Streamlit: Analizar red de pases

1. Ejecutar: `streamlit run streamlit_app.py`
2. Seleccionar archivo F24 del dropdown
3. Elegir periodo (completo/1°T/2°T)
4. Ajustar mínimo de pases con slider
5. Ver comparación lado a lado

### Python: Procesar datos

```python
from main import FootballAnalyzer

analyzer = FootballAnalyzer()

# Procesar un partido
df = analyzer.process_single_match(Path("data/raw/partido.json"))

# Guardar resultados
analyzer.save_results(df, filename="mi_analisis")
```

---

## 📚 Recursos

### Documentación OPTA
- **F24 Event Details**: Definiciones de eventos
- **F24 Appendices**: Qualifiers y coordenadas

### Bibliotecas usadas
- **pandas**: Procesamiento de datos
- **mplsoccer**: Visualizaciones de fútbol
- **streamlit**: Aplicación web
- **matplotlib**: Gráficos

### Referencias académicas
- Expected Threat (xT): Karun Singh
- VAEP: KU Leuven
- Friends of Tracking: Tutoriales de análisis

---

## 🐛 Solución de Problemas

### Error: "No se encuentra carpeta 'data'"
```bash
mkdir data
```

### Error: "ModuleNotFoundError: No module named 'mplsoccer'"
```bash
pip install mplsoccer
```

### Error: "No JSON files found"
- Verificar que los archivos estén en `data/` o `data/raw/`
- Confirmar que el nombre contenga "f24" o "F24"

### Streamlit no muestra gráficos
- Verificar instalación: `pip install matplotlib --upgrade`
- Revisar permisos de carpeta `data/`

---

## 📄 Licencia

Este proyecto usa datos OPTA bajo licencia apropiada.  
Código desarrollado para análisis académico/profesional de fútbol.

---

## 🤝 Contribuciones

Para agregar nuevas funcionalidades:

1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Pull Request

---

## 📞 Contacto

Para consultas sobre el sistema de análisis o datos OPTA.

---

**Versión:** 1.0  
**Última actualización:** Enero 2025  
**Compatibilidad:** Python 3.8+
