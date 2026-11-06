@echo off
chcp 65001 > nul
echo ========================================
echo Spustavam aktualizaciu a odoslanie na GitHub...
echo ========================================
git add .
git commit -m "Automaticka aktualizacia z terenu: %date% %time%"
git push origin main
echo ========================================
echo Hotovo! Zmeny boli odoslane na GitHub.
echo ========================================
pause