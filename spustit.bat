<<<<<<< HEAD
@echo off
chcp 65001 > nul
echo ========================================
echo Spustavam aktualizaciu a odoslanie na GitHub...
echo ========================================

REM Pridanie vsetkych zmenenych suborov
git add .

REM Vytvorenie zaznamu o zmene s casovou vzorkou
git commit -m "Automaticka aktualizacia z terenu: %date% %time%"

REM Odoslanie zmien do repozitara na GitHub
git push origin main

echo ========================================
echo Hotovo! Zmeny boli odoslane na GitHub.
echo Streamlit Cloud aplikaciu automaticky aktualizuje.
echo ========================================
pause







=======
@echo off
cd /d "%~dp0"
streamlit run asistent.py --server.address 0.0.0.0
pause





>>>>>>> 45be3a5cc69bcf74f51d884a4d4b686c95c1beec
