#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 親亡き後支援データベース - セットアップスクリプト
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# このスクリプトは以下を実行します:
#   1. Neo4j コンテナの起動
#   2. Claude Desktop Skills のインストール（シンボリックリンク）
#   3. Claude Desktop 設定ファイルのガイダンス表示
#
# 使い方:
#   chmod +x setup.sh
#   ./setup.sh           # 全セットアップ（推奨）
#   ./setup.sh --skills  # Skills のみインストール
#   ./setup.sh --neo4j   # Neo4j のみ起動
#   ./setup.sh --uninstall # Skills のアンインストール
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -euo pipefail

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# プロジェクトルート（このスクリプトのあるディレクトリ）
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SOURCE_DIR="${PROJECT_DIR}/claude-skills"

# Skills インストール先
SKILLS_TARGET_DIR="${HOME}/.claude/skills"

# Skills 一覧
SKILLS=(
    "neo4j-support-db"
    "livelihood-support"
    "provider-search"
    "emergency-protocol"
    "ecomap-generator"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ヘルパー関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print_header() {
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}  親亡き後支援データベース - セットアップ${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 前提条件チェック
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

check_prerequisites() {
    info "前提条件を確認中..."
    local missing=0

    # Docker チェック
    if command -v docker &>/dev/null; then
        success "Docker: $(docker --version | head -1)"
    else
        error "Docker がインストールされていません"
        echo "  インストール: https://docs.docker.com/get-docker/"
        missing=1
    fi

    # Docker Compose チェック
    if docker compose version &>/dev/null 2>&1; then
        success "Docker Compose: $(docker compose version --short 2>/dev/null || echo 'available')"
    elif command -v docker-compose &>/dev/null; then
        success "Docker Compose (legacy): $(docker-compose --version | head -1)"
    else
        error "Docker Compose がインストールされていません"
        missing=1
    fi

    # Node.js / npx チェック（Skills方式で必要）
    if command -v npx &>/dev/null; then
        success "npx: $(npx --version 2>/dev/null || echo 'available')"
    else
        warn "npx が見つかりません（Skills方式を使う場合に必要）"
        echo "  インストール: https://nodejs.org/"
    fi

    # claude-skills ディレクトリの存在確認
    if [ -d "${SKILLS_SOURCE_DIR}" ]; then
        success "Skills ソース: ${SKILLS_SOURCE_DIR}"
    else
        error "claude-skills/ ディレクトリが見つかりません"
        echo "  プロジェクトルートで実行してください"
        missing=1
    fi

    if [ $missing -eq 1 ]; then
        echo ""
        error "前提条件が満たされていません。上記を解決してから再実行してください。"
        exit 1
    fi

    echo ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Neo4j セットアップ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

setup_neo4j() {
    info "Neo4j コンテナを起動中..."

    cd "${PROJECT_DIR}"

    # docker compose を使用（v2優先）
    if docker compose version &>/dev/null 2>&1; then
        docker compose up -d
    else
        docker-compose up -d
    fi

    # 起動待ち
    info "Neo4j の起動を待機中（最大60秒）..."
    local retries=0
    local max_retries=12
    while [ $retries -lt $max_retries ]; do
        if curl -s http://localhost:7474 &>/dev/null; then
            success "Neo4j が起動しました"
            echo "  ブラウザUI: http://localhost:7474"
            echo "  Bolt接続: bolt://localhost:7687"
            echo "  認証: neo4j / password"
            return 0
        fi
        retries=$((retries + 1))
        sleep 5
    done

    warn "Neo4j の起動確認がタイムアウトしました"
    echo "  docker logs support-db-neo4j で状態を確認してください"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Skills インストール
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

install_skills() {
    info "Claude Desktop Skills をインストール中..."

    # ターゲットディレクトリ作成
    mkdir -p "${SKILLS_TARGET_DIR}"

    local installed=0
    local skipped=0

    for skill in "${SKILLS[@]}"; do
        local source="${SKILLS_SOURCE_DIR}/${skill}"
        local target="${SKILLS_TARGET_DIR}/${skill}"

        if [ ! -d "${source}" ]; then
            warn "スキップ: ${skill}（ソースが見つかりません）"
            skipped=$((skipped + 1))
            continue
        fi

        if [ -L "${target}" ]; then
            # 既存のシンボリックリンクを確認
            local current_target
            current_target=$(readlink "${target}")
            if [ "${current_target}" = "${source}" ]; then
                info "既にインストール済み: ${skill}"
                installed=$((installed + 1))
                continue
            else
                warn "既存のリンクを更新: ${skill}"
                rm "${target}"
            fi
        elif [ -d "${target}" ]; then
            warn "既存のディレクトリをバックアップ: ${skill}"
            mv "${target}" "${target}.backup.$(date +%Y%m%d%H%M%S)"
        fi

        # シンボリックリンク作成
        ln -s "${source}" "${target}"
        success "インストール: ${skill} -> ${target}"
        installed=$((installed + 1))
    done

    echo ""
    info "インストール結果: ${installed} 成功, ${skipped} スキップ"

    # インストール済みSkills一覧
    echo ""
    info "インストール済み Skills:"
    for skill in "${SKILLS[@]}"; do
        local target="${SKILLS_TARGET_DIR}/${skill}"
        if [ -L "${target}" ] || [ -d "${target}" ]; then
            echo -e "  ${GREEN}✓${NC} ${skill}"
        else
            echo -e "  ${RED}✗${NC} ${skill}"
        fi
    done
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Skills アンインストール
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

uninstall_skills() {
    info "Claude Desktop Skills をアンインストール中..."

    for skill in "${SKILLS[@]}"; do
        local target="${SKILLS_TARGET_DIR}/${skill}"

        if [ -L "${target}" ]; then
            rm "${target}"
            success "削除: ${skill}"
        elif [ -d "${target}" ]; then
            warn "シンボリックリンクではないため、手動で削除してください: ${target}"
        else
            info "未インストール: ${skill}"
        fi
    done

    success "アンインストール完了"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 設定ガイダンス
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

show_config_guidance() {
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}  次のステップ: Claude Desktop の設定${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Claude Desktop の設定ファイルを編集して Neo4j MCP を追加してください。"
    echo ""

    # OS判定
    if [[ "$OSTYPE" == "darwin"* ]]; then
        local config_path="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
        echo "設定ファイル:"
        echo -e "  ${BLUE}${config_path}${NC}"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "設定ファイル:"
        echo -e "  ${BLUE}%APPDATA%\\Claude\\claude_desktop_config.json${NC}"
    else
        echo "設定ファイル:"
        echo -e "  Mac: ${BLUE}~/Library/Application Support/Claude/claude_desktop_config.json${NC}"
        echo -e "  Win: ${BLUE}%APPDATA%\\Claude\\claude_desktop_config.json${NC}"
    fi

    echo ""
    echo "テンプレートファイルが用意されています:"
    echo -e "  Skills方式（推奨）: ${GREEN}configs/claude_desktop_config.skills.json${NC}"
    echo -e "  MCP方式（レガシー）: ${YELLOW}configs/claude_desktop_config.mcp.json${NC}"
    echo ""
    echo "詳細は docs/QUICK_START.md を参照してください。"
    echo ""
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン処理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

main() {
    print_header

    case "${1:-all}" in
        --skills|-s)
            check_prerequisites
            install_skills
            show_config_guidance
            ;;
        --neo4j|-n)
            check_prerequisites
            setup_neo4j
            ;;
        --uninstall|-u)
            uninstall_skills
            ;;
        --help|-h)
            echo "使い方: ./setup.sh [オプション]"
            echo ""
            echo "オプション:"
            echo "  (なし)        全セットアップ（Neo4j起動 + Skills インストール）"
            echo "  --skills, -s  Skills のみインストール"
            echo "  --neo4j, -n   Neo4j のみ起動"
            echo "  --uninstall, -u  Skills のアンインストール"
            echo "  --help, -h    このヘルプを表示"
            ;;
        all|"")
            check_prerequisites
            setup_neo4j
            echo ""
            install_skills
            show_config_guidance
            success "セットアップが完了しました！"
            ;;
        *)
            error "不明なオプション: $1"
            echo "  ./setup.sh --help でヘルプを表示"
            exit 1
            ;;
    esac
}

main "$@"
