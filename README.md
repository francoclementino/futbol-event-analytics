# ⚽ Football Event Analytics - Passing Network Analyzer

## 🎯 **Análisis avanzado de datos de fútbol con OPTA F24**

Dashboard interactivo para analizar redes de pases y estadísticas avanzadas de partidos de fútbol usando datos OPTA.

---

## 🚀 **USO EN STREAMLIT CLOUD:**

### **Cómo analizar un partido:**

1. **Sube tu archivo JSON** (formato OPTA F24 o Stats Perform)
2. La app detecta automáticamente el formato
3. Selecciona filtros (período, rango de minutos, pases mínimos)
4. ¡Disfruta las visualizaciones estilo The Athletic!

### **Características:**

✅ **Redes de Pases lado a lado** (ambos equipos)
✅ **Visualizaciones profesionales** (estilo The Athletic)
✅ **Análisis comparativo** (Top 10 combinaciones, Top 10 jugadores)
✅ **Filtros avanzados** (período, rango de minutos, conexiones mínimas)
✅ **Formato condicional** (verde → rojo según rendimiento)
✅ **Detección automática de formato** (F24 / Stats Perform / Genérico)

---

## 📊 **PARA USO LOCAL CON BASE DE DATOS:**

Si tienes una colección grande de JSONs organizados:

### **1. Estructura de carpetas:**

```
data/raw/
├── Argentina/
│   ├── Liga_Profesional/
│   │   ├── 2024/
│   │   │   ├── match1.json
│   │   │   └── match2.json
│   │   ├── 2025/
│   │   └── matches_metadata.json
│   └── matches_metadata.json
└── matches_metadata.json
```

### **2. Generar metadata:**

```bash
python generate_metadata.py
```

Esto crea archivos `matches_metadata.json` con información indexada de todos los partidos.

### **3. Usar interfaz con filtros:**

Con metadata generada, la interfaz mostrará:
- 🌎 Filtros por País / Competición / Temporada
- 🔍 Búsqueda por equipo
- 📅 Selección de partido específico o más reciente
- ⚙️ Sidebar con configuración

### **4. Ejecutar localmente:**

```bash
streamlit run app.py
```

---

## 🛠️ **SCRIPTS INCLUIDOS:**

- `generate_metadata.py` - Genera metadata de todos los JSONs organizados
- `migrate_jsons.py` - Migra JSONs desde carpetas antiguas a nueva estructura
- `update_to_sidebar.py` - Actualiza interfaz para usar sidebar (panel lateral)

---

## 📦 **REQUISITOS:**

```
streamlit
pandas
matplotlib
mplsoccer
numpy
```

Ver `requirements.txt` para versiones específicas.

---

## 🎨 **VISUALIZACIONES:**

### **Red de Pases:**
- Círculos proporcionales al número de pases
- Líneas proporcionales a conexiones entre jugadores
- Colores diferenciados por equipo
- Nombres posicionados inteligentemente

### **Tablas Comparativas:**
- Top 10 combinaciones (pasador → receptor)
- Top 10 jugadores por pases
- Formato condicional (verde = mejor, rojo = peor)

---

## 📝 **FORMATOS SOPORTADOS:**

### **OPTA F24:**
```json
{
  "Event": [
    {
      "type_id": 1,
      "team_id": "123",
      "player_id": "456",
      "x": 50.5,
      "y": 30.2
    }
  ]
}
```

### **Stats Perform / Opta API:**
```json
{
  "matchInfo": {
    "id": "abc123",
    "contestant": [...]
  },
  "liveData": {
    "event": [...]
  }
}
```

---

## 🔧 **CONFIGURACIÓN AVANZADA:**

### **Sidebar (Panel Lateral):**

Para habilitar el diseño con sidebar (filtros en panel izquierdo):

```bash
python update_to_sidebar.py
```

Esto actualiza la interfaz para un diseño más profesional tipo dashboard.

---

## 📖 **DOCUMENTACIÓN ADICIONAL:**

- `README_SISTEMA_COMPLETO.md` - Guía completa del sistema
- `README_SIDEBAR.md` - Documentación del diseño con sidebar
- `INSTRUCCIONES_FINALES.md` - Pasos de instalación y uso

---

## 🤝 **CONTRIBUCIONES:**

Este proyecto está en desarrollo activo. Sugerencias y mejoras son bienvenidas.

---

## 📄 **LICENCIA:**

MIT License - Uso libre para análisis de fútbol.

---

## 🎯 **PRÓXIMAS CARACTERÍSTICAS:**

- [ ] Análisis de xT (Expected Threat)
- [ ] Heatmaps de posiciones
- [ ] Análisis de presión
- [ ] Exportación a PDF
- [ ] Comparación entre múltiples partidos
- [ ] Integración con más fuentes de datos

---

**Desarrollado con ❤️ para analistas de fútbol**
