@echo off
echo ================================================================
echo    ACTUALIZAR A SIDEBAR (PANEL LATERAL)
echo ================================================================
echo.

cd /d "%~dp0"

echo Este script actualizara la interfaz para usar SIDEBAR.
echo.
echo Ventajas del SIDEBAR:
echo  - Filtros siempre visibles
echo  - Mas espacio para visualizaciones
echo  - Diseno profesional
echo  - Cambios instantaneos de partido
echo.
echo Se creara un backup antes de actualizar.
echo.
pause

echo.
echo ================================================================
echo Actualizando interfaz a SIDEBAR...
echo ================================================================
echo.
python update_to_sidebar.py
if errorlevel 1 (
    echo.
    echo ERROR: Fallo en actualizacion
    pause
    exit /b 1
)

echo.
echo ================================================================
echo ACTUALIZACION COMPLETADA
echo ================================================================
echo.
echo Proximos pasos:
echo   1. Ejecuta: streamlit run streamlit_app.py
echo   2. Los filtros ahora estan en el panel izquierdo!
echo.
echo Diseno:
echo   SIDEBAR (izquierda): Filtros y configuracion
echo   AREA PRINCIPAL (derecha): Visualizaciones
echo.
echo Si quieres volver al diseno anterior:
echo   Ejecuta: copy passing_network_tab_BACKUP_SIDEBAR.py passing_network_tab.py
echo.
pause
