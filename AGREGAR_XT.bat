@echo off
echo ================================================================
echo    INTEGRACIÓN DE xT (EXPECTED THREAT)
echo ================================================================
echo.

cd /d "%~dp0"

echo Este script integra Expected Threat (xT) en el analisis:
echo.
echo Caracteristicas:
echo  - Colores proporcionales a xT generado
echo  - Columna xT en tabla de jugadores
echo  - Columna xT en tabla de combinaciones
echo  - Alpha/transparencia basada en xT
echo.
pause

echo.
echo ================================================================
echo Integrando xT en passing_network_tab.py...
echo ================================================================
echo.

python INTEGRAR_XT.py

if errorlevel 1 (
    echo.
    echo ❌ ERROR: Fallo la integracion
    pause
    exit /b 1
)

echo.
echo ================================================================
echo ✅ INTEGRACIÓN COMPLETADA
echo ================================================================
echo.
echo Archivos modificados:
echo  ✅ passing_network_tab.py (con xT integrado)
echo  ✅ Backup: passing_network_tab.py.xt_backup
echo.
echo Archivos nuevos:
echo  ✅ xt_calculator.py (motor de xT)
echo.
echo Probar ahora:
echo  streamlit run app.py
echo.
echo Que veras:
echo  - Jugadores con mas xT tendran colores mas intensos
echo  - Tabla de jugadores tendra columna 'xT'
echo  - Tabla de combinaciones tendra columna 'xT'
echo.
pause
