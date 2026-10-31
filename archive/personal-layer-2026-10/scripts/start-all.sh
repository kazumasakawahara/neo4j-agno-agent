#!/bin/bash
# =============================================================================
# 親なき後支援DB — ワンクリック起動スクリプト
# Neo4j (Docker) + FastAPI + Next.js を一括起動し、ブラウザを開く
# =============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 色付きログ
info()  { printf '\033[1;36m[INFO]\033[0m  %s\n' "$1"; }
ok()    { printf '\033[1;32m[OK]\033[0m    %s\n' "$1"; }
warn()  { printf '\033[1;33m[WARN]\033[0m  %s\n' "$1"; }
fail()  { printf '\033[1;31m[FAIL]\033[0m  %s\n' "$1"; }

# ---------------------------------------------------------------------------
# 前提条件チェック
# ---------------------------------------------------------------------------
info "前提条件をチェック中..."

missing=()
command -v docker  >/dev/null 2>&1 || missing+=("docker")
command -v uv      >/dev/null 2>&1 || missing+=("uv")
command -v pnpm    >/dev/null 2>&1 || missing+=("pnpm")

if [ ${#missing[@]} -ne 0 ]; then
    fail "以下のコマンドが見つかりません: ${missing[*]}"
    echo "  brew install ${missing[*]}"
    exit 1
fi
ok "docker / uv / pnpm を確認"

# ---------------------------------------------------------------------------
# 1. Neo4j (Docker)
# ---------------------------------------------------------------------------
info "Neo4j コンテナを起動中..."
if docker compose ps --format '{{.Status}}' 2>/dev/null | grep -q "Up"; then
    ok "Neo4j は既に起動済み"
else
    docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null
    ok "Neo4j コンテナを起動しました"
fi

# Neo4j の準備を待つ（最大30秒）
info "Neo4j の接続を待機中..."
for i in $(seq 1 15); do
    if docker compose exec -T neo4j cypher-shell -u neo4j -p password "RETURN 1" >/dev/null 2>&1; then
        ok "Neo4j 接続OK (bolt://localhost:7687)"
        break
    fi
    if [ "$i" -eq 15 ]; then
        warn "Neo4j の応答が遅いです（バックグラウンドで起動継続）"
    fi
    sleep 2
done

# ---------------------------------------------------------------------------
# 2. Python 依存関係
# ---------------------------------------------------------------------------
info "Python 依存関係を確認中..."
if [ ! -d ".venv" ]; then
    uv sync
    ok "仮想環境を作成しました"
else
    ok "仮想環境は既に存在"
fi

# ---------------------------------------------------------------------------
# 3. Node.js 依存関係
# ---------------------------------------------------------------------------
info "Node.js 依存関係を確認中..."
if [ ! -d "frontend/node_modules" ]; then
    (cd frontend && pnpm install)
    ok "node_modules をインストールしました"
else
    ok "node_modules は既に存在"
fi

# ---------------------------------------------------------------------------
# 4. API サーバー起動（バックグラウンド）
# ---------------------------------------------------------------------------
API_PORT=8001
if lsof -i :$API_PORT >/dev/null 2>&1; then
    ok "API サーバーは既にポート $API_PORT で起動済み"
else
    info "API サーバーを起動中 (port $API_PORT)..."
    cd "$PROJECT_DIR/api"
    uv run uvicorn app.main:app --reload --port $API_PORT &
    API_PID=$!
    cd "$PROJECT_DIR"
    sleep 2
    if kill -0 $API_PID 2>/dev/null; then
        ok "API サーバー起動 (PID: $API_PID, port: $API_PORT)"
    else
        fail "API サーバーの起動に失敗"
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# 5. フロントエンド起動（バックグラウンド）
# ---------------------------------------------------------------------------
FRONT_PORT=3001
if lsof -i :$FRONT_PORT >/dev/null 2>&1; then
    ok "フロントエンドは既にポート $FRONT_PORT で起動済み"
else
    info "フロントエンドを起動中 (port $FRONT_PORT)..."
    cd "$PROJECT_DIR/frontend"
    pnpm dev --port $FRONT_PORT &
    FRONT_PID=$!
    cd "$PROJECT_DIR"
    ok "フロントエンド起動 (PID: $FRONT_PID, port: $FRONT_PORT)"
fi

# ---------------------------------------------------------------------------
# 6. ブラウザで開く（3秒後）
# ---------------------------------------------------------------------------
sleep 3
info "ブラウザを開いています..."
open "http://localhost:$FRONT_PORT"

# ---------------------------------------------------------------------------
# 完了メッセージ
# ---------------------------------------------------------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  親なき後支援DB が起動しました"
echo ""
echo "  フロントエンド : http://localhost:$FRONT_PORT"
echo "  API サーバー   : http://localhost:$API_PORT/docs"
echo "  Neo4j Browser  : http://localhost:7474"
echo ""
echo "  停止するには: Ctrl+C または このウィンドウを閉じる"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# フォアグラウンドで待機（Ctrl+C で停止可能）
wait
