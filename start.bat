@echo off
cd /d "%~dp0"
docker info >nul 2>&1
if errorlevel 1 (
  echo Docker Desktop chalu nei. Age Docker Desktop open koro, tarpor abar try koro.
  pause & exit /b 1
)
echo Container build o start hocche...
docker compose up -d --build --wait
if errorlevel 1 (
  echo Start hoy ni. Error dekhte: docker compose logs
  pause & exit /b 1
)
echo Ready! Browser khulche: http://localhost:8080
start http://localhost:8080
