import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini
from neo4j import GraphDatabase

load_dotenv()

# --- 検索用ツール ---
class KnowledgeRetriever:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"), 
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )

    def search_graph(self, search_query: str):
        """
        自然言語の質問に基づいてナレッジグラフを検索するためのCypherクエリを実行します。
        """
        print(f"\n🔍 [DB検索実行] Cypher生成中...")
        try:
            with self.driver.session() as session:
                # エラーハンドリング: クエリが間違っている場合に内容を表示する
                try:
                    result = session.run(search_query)
                    data = [record.data() for record in result]
                    print(f"   ▶ ヒット件数: {len(data)}件")
                    return str(data) if data else "該当する情報は見つかりませんでした。"
                except Exception as db_err:
                    print(f"   ❌ Cypher実行エラー: {db_err}")
                    return f"クエリエラー: {db_err}"
        except Exception as e:
            return f"接続エラー: {e}"

# --- 検索エージェント ---
retriever = KnowledgeRetriever()

search_agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
    tools=[retriever.search_graph],
    description="親亡き後支援データベースの検索担当",
    instructions=[
        "あなたは障害のある方の支援情報を検索するアシスタントです。",
        "ユーザーの質問に対し、Neo4jデータベースから適切な情報を取得して回答してください。",
        "",
        "【重要：データベースのスキーマ定義】",
        "以下のプロパティ名を厳格に使用すること（勝手な推測は禁止）:",
        "1. Node `Client`: プロパティ `name` (例: 健太)",
        "2. Node `Condition`: プロパティ `name` (例: 食事中, 急な予定変更)",
        "3. Node `NgAction`: プロパティ `action` (例: テレビをつける)",
        "   - ❌ `description` や `content` は存在しない。",
        "4. Node `CarePreference`: プロパティ `instruction` (例: 静かに待つ)",
        "",
        "【検索戦略】",
        "1. ユーザーの質問から、関連しそうな `Client`, `Condition`, `NgAction`, `CarePreference` を検索するCypherクエリを組み立てなさい。",
        "2. **最優先事項:** 必ず `NgAction` (禁忌) を検索に含めること。検索結果に `NgAction` がある場合は、回答の冒頭で赤文字または強調表示で警告すること。",
        "3. 関連する `Condition` (文脈) も必ず確認すること。",
        "",
        "【正しいCypherクエリの例】",
        "MATCH (c:Client)-[:HAS_CONDITION]->(con:Condition)<-[:IN_CONTEXT]-(ng:NgAction)",
        "WHERE c.name CONTAINS '健太' AND con.name CONTAINS '食事'",
        "RETURN con.name AS Scene, ng.action AS Taboo",
        "",
        "【回答スタイル】",
        "・支援者が現場ですぐ動けるよう、簡潔かつ具体的に。",
        "・推測や嘘は厳禁。"
    ],
    markdown=True
)

if __name__ == "__main__":
    # 検証シナリオ
    questions = [
        "健太くんの食事介助で気をつけることはありますか？",
        "急に予定が変わって健太くんがパニックになりそうです。どうすればいい？やってはいけないことは？"
    ]

    print("🤖 検索システムの検証を開始します...\n")
    
    for q in questions:
        print(f"\n{'='*60}")
        print(f"🗣️ 質問: {q}")
        print(f"{'='*60}")
        search_agent.print_response(q)