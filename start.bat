@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   親亡き後支援データベース - 起動スクリプト
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM ──────────────────────────────────────────────────
REM 1. uv パッケージマネージャの確認
REM ──────────────────────────────────────────────────
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] uv パッケージマネージャをインストールしています...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    echo [重要] uv がインストールされました。
    echo        このウィンドウを閉じて、start.bat をもう一度実行してください。
    pause
    exit
)

REM ──────────────────────────────────────────────────
REM 2. Python 依存パッケージのインストール
REM ──────────────────────────────────────────────────
echo [SETUP] 依存パッケージをインストールしています...
uv sync

REM ──────────────────────────────────────────────────
REM 3. Claude Desktop Skills のインストール
REM ──────────────────────────────────────────────────
echo [SETUP] Claude Desktop Skills を確認しています...

set "SKILLS_SOURCE=%~dp0claude-skills"
set "SKILLS_TARGET=%USERPROFILE%\.claude\skills"

REM Skills 一覧
set SKILLS=neo4j-support-db livelihood-support provider-search emergency-protocol ecomap-generator html-to-pdf inheritance-calculator wamnet-provider-sync

if not exist "%SKILLS_SOURCE%" (
    echo [WARN] claude-skills フォルダが見つかりません。スキルのインストールをスキップします。
    goto :skills_done
)

REM ターゲットディレクトリの作成
if not exist "%SKILLS_TARGET%" (
    mkdir "%SKILLS_TARGET%"
    echo [OK] %SKILLS_TARGET% を作成しました
)

set SKILLS_INSTALLED=0
set SKILLS_SKIPPED=0

for %%S in (%SKILLS%) do (
    if exist "%SKILLS_SOURCE%\%%S\SKILL.md" (
        REM スキルが更新されているかチェック（SKILL.md の比較）
        if exist "%SKILLS_TARGET%\%%S\SKILL.md" (
            fc /b "%SKILLS_SOURCE%\%%S\SKILL.md" "%SKILLS_TARGET%\%%S\SKILL.md" >nul 2>&1
            if !errorlevel! equ 0 (
                set /a SKILLS_SKIPPED+=1
            ) else (
                echo [UPDATE] %%S を更新しています...
                rmdir /s /q "%SKILLS_TARGET%\%%S" 2>nul
                xcopy /e /i /q /y "%SKILLS_SOURCE%\%%S" "%SKILLS_TARGET%\%%S" >nul
                set /a SKILLS_INSTALLED+=1
            )
        ) else (
            echo [INSTALL] %%S をインストールしています...
            xcopy /e /i /q /y "%SKILLS_SOURCE%\%%S" "%SKILLS_TARGET%\%%S" >nul
            set /a SKILLS_INSTALLED+=1
        )
    ) else (
        echo [WARN] %%S のソースが見つかりません。スキップします。
        set /a SKILLS_SKIPPED+=1
    )
)

echo [OK] Skills インストール完了
echo.

:skills_done

REM ──────────────────────────────────────────────────
REM 4. 初回設定ウィザード
REM ──────────────────────────────────────────────────
if not exist .env (
    echo [SETUP] 初回設定ウィザードを起動します...
    uv run python setup_wizard.py
)

REM ──────────────────────────────────────────────────
REM 5. Docker / Neo4j の起動
REM ──────────────────────────────────────────────────
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Docker が起動していません。
    echo         Docker Desktop を起動してから、もう一度 start.bat を実行してください。
    echo         https://docs.docker.com/get-docker/
    pause
    exit
)

echo [START] データベースを起動しています...
docker-compose up -d neo4j

REM ──────────────────────────────────────────────────
REM 6. アプリケーションの起動
REM ──────────────────────────────────────────────────
echo [START] ダッシュボードを起動しています...
start "Post-Parent Dashboard" /min uv run streamlit run app.py

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   起動完了！ブラウザで http://localhost:8501 を開いてください
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

pause
