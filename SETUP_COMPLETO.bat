@echo off
echo ================================================================
echo    SETUP COMPLETO - PASSING NETWORK ANALYZER
echo ================================================================
echo.

cd /d "%~dp0"

echo [1/4] Migrando JSONs existentes de SCORESWAY BD...
echo.
python migrate_jsons.py
if errorlevel 1 (
    echo.
    echo ERROR: Fallo en migracion de JSONs
    echo Puedes continuar si no tienes JSONs que migrar
    echo.
    pause
)

echo.
echo ================================================================
echo [2/4] Generando metadata de todos los partidos...
echo ================================================================
echo.
python generate_metadata.py
if errorlevel 1 (
    echo.
    echo ERROR: Fallo en generacion de metadata
    pause
    exit /b 1
)

echo.
echo ================================================================
echo [3/4] Actualizando interfaz de Streamlit...
echo ================================================================
echo.
python update_passing_network.py
if errorlevel 1 (
    echo.
    echo ERROR: Fallo en actualizacion de interfaz
    pause
    exit /b 1
)

echo.
echo ================================================================
echo [4/4] SETUP COMPLETADO
echo ================================================================
echo.
echo Proximos pasos:
echo   1. Ejecuta: streamlit run streamlit_app.py
echo   2. Usa los filtros para buscar partidos
echo   3. Analiza Passing Networks!
echo.
echo Para agregar mas partidos:
echo   - Coloca JSONs en data/raw/[Pais]/[Competicion]/[Temporada]/
echo   - Ejecuta: python generate_metadata.py
echo.
pause
