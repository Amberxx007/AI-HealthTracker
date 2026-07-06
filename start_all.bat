@echo off
setlocal

set "ROOT=%~dp0"
set "LLAMA_CPP=C:\dev\llama.cpp"
set "MODEL=C:\dev\llama.cpp\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
set "CUDA_X64=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\x64"

set "LLAMA_PORT="
for %%P in (8080 8081 8082 8083 8084 8085) do (
  netstat -ano | findstr ":%%P" | findstr "LISTENING" >nul
  if errorlevel 1 if not defined LLAMA_PORT set "LLAMA_PORT=%%P"
)
if not defined LLAMA_PORT (
  echo [ERROR] Could not find a free LLM port in range 8080-8085.
  pause
  exit /b 1
)
set "LLAMA_BASE_URL=http://localhost:%LLAMA_PORT%"

echo =============================================================
echo  AI Doctor v3 - One Click Startup
echo =============================================================
echo.

if not exist "%LLAMA_CPP%\build\bin\Release\llama-server.exe" (
  echo [ERROR] llama-server.exe not found at:
  echo         %LLAMA_CPP%\build\bin\Release\llama-server.exe
  pause
  exit /b 1
)

if not exist "%MODEL%" (
  echo [ERROR] GGUF model not found at:
  echo         %MODEL%
  pause
  exit /b 1
)

if not exist "%ROOT%venv\Scripts\activate.bat" (
  echo [ERROR] Python venv not found at:
  echo         %ROOT%venv\Scripts\activate.bat
  pause
  exit /b 1
)

if not exist "%ROOT%frontend\package.json" (
  echo [ERROR] Frontend package.json not found at:
  echo         %ROOT%frontend\package.json
  pause
  exit /b 1
)

echo [0/3] Clearing busy ports (%LLAMA_PORT%, 8000, 3001)...
for %%P in (%LLAMA_PORT% 8000 3001) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%A >nul 2>&1
  )
)
timeout /t 1 >nul

echo [1/3] Starting llama-server on port %LLAMA_PORT% (GPU)...
start "LLAMA-SERVER (%LLAMA_PORT% GPU)" powershell -NoExit -ExecutionPolicy Bypass -Command "$env:Path='%CUDA_X64%;' + $env:Path; & '%LLAMA_CPP%\build\bin\Release\llama-server.exe' -m '%MODEL%' -c 4096 --host 0.0.0.0 --port %LLAMA_PORT% -ngl 33 --threads 8 -b 512"

echo [2/3] Starting FastAPI on port 8000...
start "FASTAPI (8000)" cmd /k "cd /d %ROOT% && set \"LLAMA_BASE_URL=%LLAMA_BASE_URL%\" && call venv\Scripts\activate.bat && uvicorn enhanced_api:app --host 0.0.0.0 --port 8000"

echo [3/3] Starting Next.js on port 3001...
start "NEXT DEV (3001)" cmd /k "cd /d %ROOT%frontend && npx next dev -p 3001"

echo.
echo All services launched in separate windows.
echo - llama-server: %LLAMA_BASE_URL%
echo - backend API : http://localhost:8000
echo - frontend    : http://localhost:3001
echo.
echo Close each service window to stop that service.
echo.
pause
