@echo off
echo ================================================================
echo    SOLUCION FINAL: SIN xT (por ahora)
echo ================================================================
echo.

cd /d "%~dp0"

echo El archivo passing_network_tab.py se corrompio al integrar xT.
echo.
echo Solucion: Restaurar backup SIN xT
echo Subir solo xt_calculator.py para futuros experimentos
echo.
pause

echo.
echo ================================================================
echo Restaurando backup limpio...
echo ================================================================
echo.

if exist "passing_network_tab.py.backup" (
    copy /Y "passing_network_tab.py.backup" "passing_network_tab.py"
    echo ✅ Restaurado desde passing_network_tab.py.backup
) else (
    echo ❌ No existe backup
    echo.
    echo Tienes que revertir manualmente con Git:
    echo git checkout HEAD~1 passing_network_tab.py
    pause
    exit /b 1
)

echo.
echo ================================================================
echo Verificando archivos...
echo ================================================================
echo.

if exist "xt_calculator.py" (
    echo ✅ xt_calculator.py existe
) else (
    echo ⚠️  xt_calculator.py no existe (opcional)
)

echo.
echo ================================================================
echo Proximo paso: GitHub Desktop
echo ================================================================
echo.
echo 1. Abre GitHub Desktop
echo 2. Veras cambios en:
echo    - passing_network_tab.py (restaurado)
echo    - xt_calculator.py (nuevo, opcional)
echo.
echo 3. Commit: "fix: Restaurar passing_network_tab sin xT"
echo 4. Push
echo.
echo 5. Espera 2-3 minutos
echo 6. App funcionara sin xT
echo.
pause
