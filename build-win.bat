@echo off
rem Kompilieren der EXE-Datei
call nuitka --standalone --enable-plugin=tk-inter --enable-plugin=matplotlib --enable-plugin=no-qt --windows-console-mode=disable --windows-icon-from-ico=bitcoin.ico --output-dir=dist main.py 

rem Überprüfen, ob die Kompilierung erfolgreich war
if %errorlevel% neq 0 (
    echo Kompilierung fehlgeschlagen!
    exit /b %errorlevel%
)

rem Zusätzliche Datei kopieren
copy Bitcoin.ico dist\main.dist

rem Benennen der EXE-Datei um
ren "dist\main.dist\main.exe" "Bitcoin de Assistent.exe"

rem Löschen des dist\main.build Verzeichnisses, falls es existiert
if exist dist\main.build (
    rmdir /s /q dist\main.build
    echo Verzeichnis dist\main.build wurde gelöscht.
) else (
    echo Verzeichnis dist\main.build nicht gefunden.
)

echo Fertig!
pause