#!/bin/bash
#
# 親亡き後支援データベース - バックアップスクリプト
#
# 使用方法:
#   ./scripts/backup.sh
#
# cronで定期実行する場合（毎日AM3時）:
#   0 3 * * * cd /path/to/neo4j-agno-agent && ./scripts/backup.sh
#

set -e

# --- 設定 ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/neo4j_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"
KEEP_DAYS=30  # バックアップ保持日数

# 色付き出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "📦 親亡き後支援DB バックアップ"
echo "=========================================="
echo "日時: $(date)"
echo ""

# バックアップディレクトリ作成
mkdir -p "${BACKUP_DIR}"

# --- 方法1: Dockerコンテナのデータをtarで圧縮 ---
echo -e "${YELLOW}[1/3]${NC} Neo4jデータディレクトリをバックアップ中..."

DATA_DIR="${PROJECT_DIR}/neo4j_data"
if [ -d "$DATA_DIR" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_data.tar.gz" -C "$PROJECT_DIR" neo4j_data
    echo -e "${GREEN}✅${NC} データバックアップ完了: ${BACKUP_NAME}_data.tar.gz"
else
    echo -e "${RED}⚠️${NC} neo4j_dataディレクトリが見つかりません"
fi

# --- 方法2: Cypherダンプ（全ノード・リレーション） ---
echo -e "${YELLOW}[2/3]${NC} Cypherエクスポート中..."

# Neo4jが起動しているか確認
if docker ps --format '{{.Names}}' | grep -q "support-db-neo4j"; then
    # APOCを使用したエクスポート（JSON形式）
    docker exec support-db-neo4j cypher-shell -u neo4j -p password \
        "CALL apoc.export.json.all('/backup/${BACKUP_NAME}.json', {useTypes: true})" \
        2>/dev/null || echo -e "${YELLOW}⚠️${NC} APOCエクスポートはスキップ（APOCプラグイン要確認）"

    # 基本的なノードカウント情報を保存
    docker exec support-db-neo4j cypher-shell -u neo4j -p password \
        "MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY label" \
        > "${BACKUP_DIR}/${BACKUP_NAME}_stats.txt" 2>/dev/null

    echo -e "${GREEN}✅${NC} 統計情報保存完了: ${BACKUP_NAME}_stats.txt"
else
    echo -e "${YELLOW}⚠️${NC} Neo4jコンテナが起動していません（データディレクトリのみバックアップ）"
fi

# --- 古いバックアップの削除 ---
echo -e "${YELLOW}[3/3]${NC} ${KEEP_DAYS}日以上前のバックアップを削除中..."

find "${BACKUP_DIR}" -name "backup_*" -type f -mtime +${KEEP_DAYS} -delete 2>/dev/null || true
echo -e "${GREEN}✅${NC} クリーンアップ完了"

# --- 完了 ---
echo ""
echo "=========================================="
echo -e "${GREEN}✅ バックアップ完了${NC}"
echo "=========================================="
echo "保存先: ${BACKUP_DIR}"
echo ""
ls -lh "${BACKUP_DIR}/${BACKUP_NAME}"* 2>/dev/null || echo "(ファイルなし)"
echo ""

# バックアップサイズ合計
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1)
echo "バックアップ合計サイズ: ${TOTAL_SIZE}"
