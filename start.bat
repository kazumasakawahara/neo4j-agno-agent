@echo off
cd /d "%~dp0"

echo 🚀 Starting Post-Parent Support System...

REM Check uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing 'uv' package manager...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo [IMPORTANT] uv installed. Please close this window and run start.bat again to refresh path.
    pause
    exit
)

echo 📦 Installing dependencies...
uv sync

if not exist .env (
    echo ⚠️  Configuration not found. Launching Setup Wizard...
    uv run python setup_wizard.py
)

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop.
    pause
    exit
)

echo 🗄️  Starting Database...
docker-compose up -d neo4j

echo 📊 Starting Dashboard...
REM Start Streamlit in a new minimized window
start "Post-Parent Dashboard" /min uv run streamlit run app_narrative.py

echo 🤖 Starting Agent Team...
uv run python main.py

pause
