#!/bin/bash
# =============================================================================
# 親亡き後支援DB - リストアスクリプト
# 使用方法: ./scripts/restore.sh [backup_file.tar.gz]
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/neo4j_backup"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 引数チェック: なければバックアップ一覧を表示
if [ -z "$1" ]; then
    echo -e "${YELLOW}利用可能なバックアップ:${NC}"
    echo ""
    if ls "${BACKUP_DIR}"/backup_*_data.tar.gz 1> /dev/null 2>&1; then
        ls -lth "${BACKUP_DIR}"/backup_*_data.tar.gz | head -10 | while read -r line; do
            echo "  $line"
        done
    else
        echo -e "  ${RED}バックアップファイルが見つかりません${NC}"
    fi
    echo ""
    echo "使用方法: $0 <backup_file.tar.gz>"
    echo "例: $0 backup_20260211_data.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

# フルパスでない場合はBACKUP_DIRからの相対パスとして扱う
if [[ "$BACKUP_FILE" != /* ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}エラー: ${BACKUP_FILE} が見つかりません${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}⚠️  警告: 現在のデータベースを上書きします。${NC}"
echo "  バックアップファイル: $(basename "$BACKUP_FILE")"
echo "  サイズ: $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""
read -p "続行しますか？ (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "中止しました"
    exit 0
fi

# [1/3] Neo4jコンテナ停止
echo ""
echo -e "${YELLOW}[1/3] Neo4jを停止中...${NC}"
docker-compose -f "${PROJECT_DIR}/docker-compose.yml" stop neo4j

# [2/3] データ差し替え
echo -e "${YELLOW}[2/3] データを復元中...${NC}"
rm -rf "${PROJECT_DIR}/neo4j_data"
tar -xzf "$BACKUP_FILE" -C "$PROJECT_DIR"
echo -e "  復元完了: neo4j_data/"

# [3/3] Neo4j再起動
echo -e "${YELLOW}[3/3] Neo4jを再起動中...${NC}"
docker-compose -f "${PROJECT_DIR}/docker-compose.yml" up -d neo4j

# 起動待機
echo "  データベース起動待機中..."
for i in $(seq 1 30); do
    if docker exec support-db-neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ リストア完了！データベースが起動しました。${NC}"
        exit 0
    fi
    sleep 1
done

echo ""
echo -e "${YELLOW}⚠️  データベースの起動に時間がかかっています。しばらくお待ちください。${NC}"
