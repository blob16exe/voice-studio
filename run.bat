@echo off
chcp 65001 >nul
title Voice Studio
cd /d "%~dp0"
echo ================================================
echo   VOICE STUDIO - tool tao giong doc cho video
echo ================================================
echo.

REM Tim Python: uu tien "py" (Python Launcher), khong thay moi thu "python"
set PY=
py --version >nul 2>&1 && set PY=py
if not defined PY python --version >nul 2>&1 && set PY=python
if not defined PY (
  echo [LOI] Chua thay Python tren may nay.
  echo Hay cai Python 3 tu trang python.org, nho tick chon "Add python.exe to PATH"
  echo o man hinh cai dat, roi chay lai file nay. Xem them README-HUONG-DAN.md.
  pause
  exit /b 1
)
echo Da thay Python, dang dung lenh: %PY%
echo.

REM Chi cai goi khi con thieu (kiem tra bang cach thu import)
%PY% -c "import edge_tts, pyttsx3, sherpa_onnx, numpy, soundfile" >nul 2>&1
if errorlevel 1 (
  echo Dang cai cac goi can thiet con thieu... buoc nay can mang Internet, cho vai phut.
  %PY% -m pip install --disable-pip-version-check edge-tts pyttsx3 sherpa-onnx numpy soundfile
  if errorlevel 1 (
    echo.
    echo [LOI] Cai goi that bai. Kiem tra lai mang Internet roi chay lai file nay.
    pause
    exit /b 1
  )
  echo Cai xong.
  echo.
)

echo Khoi dong Voice Studio...
%PY% app.py
if errorlevel 1 (
  echo.
  echo [LOI] Tool gap loi khi chay. Xem muc "Gap loi thi sao" trong README-HUONG-DAN.md.
  pause
)
