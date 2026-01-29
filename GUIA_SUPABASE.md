# 🚀 GUÍA COMPLETA: MIGRAR A SUPABASE

## 🎯 **POR QUÉ SUPABASE:**

- ✅ **500 MB gratis** (~333 partidos completos)
- ✅ **PostgreSQL real** (consultas SQL completas)
- ✅ **API REST automática** (sin backend)
- ✅ **Filtros super rápidos** con índices
- ✅ **Escalable** a millones de registros

---

## 📋 **PASO 1: CREAR CUENTA EN SUPABASE**

1. Ve a: https://supabase.com
2. Click en "Start your project"
3. Sign up con GitHub (gratis)
4. Crear nuevo proyecto:
   - **Name**: `football-analytics`
   - **Database Password**: [guarda esto!]
   - **Region**: South America (más cercano)
   - **Plan**: Free

---

## 🗄️ **PASO 2: CREAR TABLA**

En el dashboard de Supabase:

1. Ve a **SQL Editor**
2. Pega este código:

```sql
-- Crear tabla de partidos
CREATE TABLE matches (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  match_id TEXT UNIQUE NOT NULL,
  country TEXT NOT NULL,
  competition TEXT NOT NULL,
  competition_full TEXT,
  competition_code TEXT,
  season TEXT NOT NULL,
  date DATE,
  time TIME,
  description TEXT,
  stage TEXT,
  week INTEGER,
  data JSONB NOT NULL,  -- JSON completo del partido
  created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para búsquedas rápidas
CREATE INDEX idx_country ON matches(country);
CREATE INDEX idx_competition ON matches(competition);
CREATE INDEX idx_competition_full ON matches(competition_full);
CREATE INDEX idx_season ON matches(season);
CREATE INDEX idx_date ON matches(date DESC);
CREATE INDEX idx_description_gin ON matches USING GIN (to_tsvector('spanish', description));

-- Permitir búsquedas ILIKE rápidas
CREATE INDEX idx_description_lower ON matches(LOWER(description));

-- Comentarios
COMMENT ON TABLE matches IS 'Partidos de fútbol con datos OPTA completos';
COMMENT ON COLUMN matches.data IS 'JSON completo del partido (matchInfo + liveData)';
```

3. Click **Run**

---

## 🔑 **PASO 3: OBTENER CREDENCIALES**

1. Ve a **Settings** → **API**
2. Copia:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGc...` (clave pública)

---

## 🐍 **PASO 4: INSTALAR LIBRERÍA**

Agrega a `requirements.txt`:

```txt
supabase==2.9.1
```

Instala localmente:

```bash
pip install supabase
```

---

## 📤 **PASO 5: SUBIR PARTIDOS**

### **Opción A: Subir 10 partidos de prueba**

```bash
cd C:\Users\frank\ANALISIS DE DATOS\FUTBOL\futbol-event-analytics

# Configurar variables de entorno
set SUPABASE_URL=https://xxxxx.supabase.co
set SUPABASE_KEY=eyJhbGc...

# Subir 10 partidos
python upload_to_supabase.py
```

### **Opción B: Subir todos (~333 con plan gratuito)**

Edita `upload_to_supabase.py`:

```python
upload_to_supabase(
    raw_dir=r"C:\...\data\raw",
    max_files=333  # Máximo para plan gratuito (500 MB)
)
```

---

## 🌐 **PASO 6: CONFIGURAR STREAMLIT CLOUD**

1. Ve a: https://share.streamlit.io
2. Selecciona tu app
3. Settings → **Secrets**
4. Agrega:

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGc..."
```

5. Save

---

## 🔧 **PASO 7: ACTUALIZAR CÓDIGO**

Abre `app.py` y en la sección de imports agrega:

```python
from passing_network_supabase import show_passing_network_tab_supabase
```

Reemplaza en la función principal:

```python
# ANTES:
if selected_tab == "Passing Network":
    show_passing_network_tab()

# DESPUÉS:
if selected_tab == "Passing Network":
    show_passing_network_tab_supabase()
```

---

## 🚀 **PASO 8: COMMIT Y PUSH**

```bash
git add .
git commit -m "feat: Integración con Supabase para 333 partidos en cloud

- Tabla matches en PostgreSQL
- Filtros por competición/temporada/equipo
- Búsquedas con índices optimizados
- API REST automática
- 500 MB gratis (333 partidos)
"
git push
```

---

## ✅ **VERIFICAR QUE FUNCIONA:**

1. Abre tu app: `futbol-event-analytics-opta.streamlit.app`
2. Verás el **SIDEBAR** con filtros
3. Selecciona competición/temporada
4. ¡Los partidos se cargan desde Supabase!

---

## 📊 **MONITOREAR USO:**

En Supabase dashboard:

1. **Database** → Size: Ver cuánto espacio usas
2. **API** → Request count: Ver número de consultas
3. **Table Editor** → `matches`: Ver partidos subidos

---

## 🎯 **VENTAJAS OBTENIDAS:**

✅ **Antes (File Uploader)**:
- Usuario sube archivo cada vez
- No hay filtros
- No hay búsqueda

✅ **Después (Supabase)**:
- 333 partidos disponibles instantáneamente
- Filtros por país/competición/temporada/equipo
- Búsqueda rápida
- Sidebar profesional
- Cambio instantáneo de partidos

---

## 💰 **PLANES SI NECESITAS MÁS:**

| Plan | Precio | Storage | Partidos |
|------|--------|---------|----------|
| Free | $0 | 500 MB | ~333 |
| Pro | $25/mes | 8 GB | ~5,333 |
| Team | $599/mes | 100 GB | ~66,666 |

Para 1841 partidos necesitarías **Pro** ($25/mes = 8 GB)

---

## 🔮 **BONUS: QUERIES SQL ÚTILES**

### **Contar partidos por país:**
```sql
SELECT country, COUNT(*) 
FROM matches 
GROUP BY country 
ORDER BY COUNT(*) DESC;
```

### **Buscar partidos de Boca:**
```sql
SELECT date, description 
FROM matches 
WHERE description ILIKE '%boca%' 
ORDER BY date DESC 
LIMIT 10;
```

### **Partidos más recientes:**
```sql
SELECT date, competition_full, description 
FROM matches 
ORDER BY date DESC 
LIMIT 20;
```

---

## 🆘 **TROUBLESHOOTING:**

### **Error: "relation matches does not exist"**
→ No creaste la tabla. Vuelve al PASO 2.

### **Error: "insufficient_privilege"**
→ La key es incorrecta. Usa la **anon public** key, NO la service_role.

### **Error: "row is too big"**
→ Un JSON es muy grande (>1 MB). Divide en partes o usa Storage.

### **Consultas lentas**
→ Verifica que los índices estén creados (PASO 2).

---

## 🎉 **¡LISTO!**

Ahora tienes:
- ✅ Base de datos profesional en la nube
- ✅ Filtros avanzados en Streamlit Cloud
- ✅ 333 partidos accesibles instantáneamente
- ✅ Escalable a miles de partidos
- ✅ Costo: $0 (hasta 500 MB)

**Próximo paso:** Ejecuta `upload_to_supabase.py` para migrar tus partidos! 🚀
