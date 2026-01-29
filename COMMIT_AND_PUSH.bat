@echo off
echo ================================================================
echo    COMMIT Y PUSH A GITHUB
echo ================================================================
echo.

cd /d "%~dp0"

echo Este script preparara y hara commit de todos los cambios.
echo.
echo QUE SE INCLUIRA:
echo  - Codigo actualizado (sidebar, filtros avanzados)
echo  - Scripts de metadata y migracion
echo  - Archivos de metadata (pequenos, ~2 MB total)
echo  - Estructura de carpetas vacia
echo  - Documentacion completa
echo.
echo QUE NO SE INCLUIRA (gitignored):
echo  - Archivos JSON de partidos (demasiado grandes)
echo  - Archivos de backup
echo  - Cache de Python
echo.
pause

echo.
echo ================================================================
echo 1. Verificando estado de Git...
echo ================================================================
echo.
git status

echo.
echo ================================================================
echo 2. Agregando archivos...
echo ================================================================
echo.
git add .
git add data/raw/matches_metadata.json
git add data/raw/Argentina/matches_metadata.json
git add data/raw/Argentina/Liga_Profesional/matches_metadata.json
git add -f .gitignore

echo.
echo ================================================================
echo 3. Verificando que hacer commit...
echo ================================================================
echo.
git status

echo.
echo ================================================================
echo 4. Haciendo commit...
echo ================================================================
echo.
git commit -m "feat: Sistema completo con sidebar y metadata (1841 partidos indexados)

SISTEMA COMPLETO IMPLEMENTADO:

📁 ESTRUCTURA JERARQUICA:
- Pais/Competicion/Temporada
- 1841 partidos indexados (1091 ARG + 750 ECU)
- Metadata generada en 3 niveles

🎨 INTERFAZ CON SIDEBAR:
- Panel lateral con filtros
- Competicion / Temporada / Equipo
- Partido mas reciente vs especifico
- Contador de partidos

🔧 SCRIPTS AUTOMATIZADOS:
- generate_metadata.py - Indexa todos los partidos
- migrate_jsons.py - Migra desde carpetas antiguas
- update_to_sidebar.py - Actualiza interfaz

📊 VISUALIZACIONES MEJORADAS:
- Redes de pases estilo The Athletic
- Formato condicional verde-rojo
- Comparativas lado a lado
- Proporciones dinamicas

📖 DOCUMENTACION:
- README.md completo
- README_SIDEBAR.md
- README_SISTEMA_COMPLETO.md
- DEPLOYMENT.md

⚙️ CONFIGURACION:
- .gitignore actualizado (excluye JSONs grandes)
- requirements.txt
- Estructura preparada para Streamlit Cloud

🎯 LISTO PARA PRODUCCION
"

if errorlevel 1 (
    echo.
    echo ERROR: Fallo en commit
    pause
    exit /b 1
)

echo.
echo ================================================================
echo 5. Haciendo push a GitHub...
echo ================================================================
echo.
git push

if errorlevel 1 (
    echo.
    echo ERROR: Fallo en push
    echo.
    echo Posibles causas:
    echo  - No estas autenticado en GitHub
    echo  - Archivos demasiado grandes (verifica .gitignore)
    echo  - Problemas de red
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo COMMIT Y PUSH COMPLETADOS
echo ================================================================
echo.
echo Proximos pasos:
echo   1. Ve a Streamlit Cloud: https://share.streamlit.io/
echo   2. La app se actualizara automaticamente
echo   3. Espera 2-3 minutos para el deployment
echo   4. Prueba subiendo un JSON de partido
echo.
echo URL de tu app:
echo   futbol-event-analytics-opta.streamlit.app
echo.
echo NOTA: Los JSONs NO estan en el repo (demasiado grandes)
echo       Los usuarios deben subir archivos manualmente
echo       O usar metadata si corren localmente
echo.
pause
