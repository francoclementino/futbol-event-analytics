# 🎯 Expected Threat (xT) - Documentación

## 📊 **¿Qué es Expected Threat?**

Expected Threat (xT) es una métrica que mide cuánta **amenaza de gol** genera una acción (típicamente un pase).

### **Concepto:**
- Cada zona del campo tiene un **valor xT** basado en la probabilidad histórica de que una posesión desde esa zona termine en gol
- Un pase que mueve el balón a una zona más peligrosa **añade xT**
- Un pase hacia atrás **resta xT**

### **Ejemplo:**
```
Pase desde mediocampo (xT = 0.005) → Área rival (xT = 0.035)
xT añadido = 0.035 - 0.005 = 0.030
```

---

## 🗺️ **Mapa de Calor xT:**

```
┌────────────────────────────────────────────┐
│ PORTERÍA PROPIA                    RIVAL   │
│                                            │
│  0.004  0.005  0.007  0.010  0.015  0.025 │ ← Banda superior
│  0.005  0.006  0.008  0.012  0.018  0.030 │
│  0.005  0.006  0.009  0.013  0.020  0.035 │ ← Centro
│  0.005  0.006  0.008  0.012  0.018  0.030 │
│  0.004  0.005  0.007  0.010  0.015  0.025 │ ← Banda inferior
│                                            │
└────────────────────────────────────────────┘
     ZONA DEFENSIVA    MEDIOCAMPO    ATAQUE
```

**Interpretación:**
- 🔴 Rojo (0.025-0.050): Zona ultra peligrosa (área rival)
- 🟠 Naranja (0.015-0.025): Zona peligrosa (borde del área)
- 🟡 Amarillo (0.010-0.015): Zona moderada (último tercio)
- 🟢 Verde (0.004-0.010): Zona baja amenaza

---

## 📈 **Implementación en el Dashboard:**

### **1. Colores en la Red de Pases:**

Los nodos (jugadores) tienen **alpha (transparencia)** proporcional a su xT:

```python
# Jugador con más xT → Alpha = 1.0 (opaco)
# Jugador con menos xT → Alpha = 0.3 (transparente)

alpha = 0.3 + (xT_jugador / xT_maximo) * 0.7
```

**Resultado visual:**
- Jugadores que generan más amenaza se ven **más sólidos**
- Jugadores con menos xT se ven **más transparentes**

### **2. Tabla de Jugadores:**

| # | Jugador | Pases | xT |
|---|---------|-------|----|
| 1 | L. Messi | 85 | **0.245** |
| 2 | S. Busquets | 102 | 0.087 |
| 3 | J. Alba | 67 | 0.156 |

**Columna xT:**
- Suma total del xT generado por ese jugador en el partido
- Formato: 3 decimales (ej: 0.245)

### **3. Tabla de Combinaciones:**

| # | Combinación | Pases | xT |
|---|-------------|-------|----|
| 1 | L. Messi → J. Alba | 12 | **0.089** |
| 2 | S. Busquets → L. Messi | 18 | 0.067 |

**Columna xT:**
- xT acumulado en esa conexión específica
- Ayuda a identificar **duplas peligrosas**

---

## 🎨 **Interpretación Visual:**

### **Ejemplo: Deportivo Pasto vs Millonarios**

**Deportivo Pasto:**
- E. Velasco: Alpha = 1.0 (más opaco) → Alto xT
- J. Herreri: Alpha = 0.4 (más transparente) → Bajo xT

**Millonarios:**
- S. Martín: Alpha = 1.0 → Generó más amenaza
- D. Novoa: Alpha = 0.3 → Generó poca amenaza

**Insight:**
Los jugadores más opacos son los que **movieron el balón a zonas más peligrosas**.

---

## 📊 **Casos de Uso:**

### **1. Identificar Progresores:**
Jugadores con alto xT son **buenos en pases progresivos** (rompen líneas).

### **2. Evaluar Conexiones:**
Duplas con alto xT son **sociedades peligrosas** que generan chances.

### **3. Comparar Estilos:**
- **xT alto**: Equipo que progresa rápido
- **xT bajo**: Equipo que circula en zonas seguras

---

## 🧮 **Fórmula Completa:**

```python
# 1. Obtener valor xT de cada zona
XT_MATRIX[12x8]  # Grilla precalculada

# 2. Para un pase:
xt_start = XT_MATRIX[zona_inicio]
xt_end = XT_MATRIX[zona_fin]
xt_added = xt_end - xt_start

# 3. xT total del jugador:
xT_jugador = sum(xt_added para todos sus pases exitosos)

# 4. xT de una conexión:
xT_conexion = sum(xt_added para pases P1 → P2)
```

---

## 🔍 **Limitaciones:**

1. **No considera presión:** Un pase bajo presión vale igual que uno libre
2. **No valora regates:** Solo mide pases
3. **No considera velocidad:** Pase rápido = pase lento
4. **Grilla estática:** No se adapta a contextos específicos

---

## 📚 **Referencias:**

- **Karun Singh** (2019): "Introducing Expected Threat (xT)"
  - https://karun.in/blog/expected-threat.html
- **Futbolística** (YouTube): Explicaciones visuales de xT
- **Friends of Tracking**: Tutoriales de implementación

---

## 🚀 **Archivos del Proyecto:**

```
xt_calculator.py       # Motor de cálculo
passing_network_tab.py # Integración en visualizaciones
AGREGAR_XT.bat         # Script de instalación
```

---

## ✅ **Verificar que Funciona:**

1. Ejecuta: `streamlit run app.py`
2. Selecciona un partido
3. **Verifica:**
   - ✅ Nodos tienen diferentes transparencias
   - ✅ Tabla de jugadores tiene columna "xT"
   - ✅ Tabla de combinaciones tiene columna "xT"
   - ✅ Jugadores con más pases progresivos tienen mayor alpha

---

**¡xT añadido con éxito! 🎯**
