import os
import json
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini
from neo4j import GraphDatabase
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

load_dotenv()

# --- 1. データモデル (変更なし) ---
class CareKnowledge(BaseModel):
    client_name: str = Field(..., description="対象者の名前")
    preference: Optional[str] = Field(None, description="本人が好むケア、落ち着く方法、こだわり (CarePreference)")
    condition: str = Field(..., description="そのケアが必要な理由、医学的特性、文脈 (Condition)")
    ng_action: Optional[str] = Field(None, description="【重要】絶対にしてはいけないこと、パニックを誘発する行動 (NgAction)")

    model_config = ConfigDict(description="支援記録から抽出された、構造化されたケアの知識")

# --- 2. Neo4j 接続ツール (修正版) ---
class Neo4jTools:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, user, password]):
            raise ValueError("❌ Neo4jの接続情報が.envに設定されていません。")
            
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def register_knowledge(self, knowledge_list: List[CareKnowledge]):
        print(f"🛠️ [Tool実行] {len(knowledge_list)} 件のデータを登録プロセスに入ります...")
        
        # ★修正ポイント: NgActionとConditionを繋ぐリレーションを追加
        query = """
        MERGE (c:Client {name: $client_name})
        MERGE (con:Condition {name: $condition})
        MERGE (c)-[:HAS_CONDITION]->(con)
        
        // Preferenceがある場合
        FOREACH (ignoreMe IN CASE WHEN $preference IS NOT NULL THEN [1] ELSE [] END |
            MERGE (cp:CarePreference {instruction: $preference})
            MERGE (c)-[:REQUIRES]->(cp)
            MERGE (cp)-[:ADDRESSES]->(con)
        )
        
        // NgActionがある場合 (最優先)
        FOREACH (ignoreMe IN CASE WHEN $ng_action IS NOT NULL THEN [1] ELSE [] END |
            MERGE (ng:NgAction {action: $ng_action})
            MERGE (c)-[:MUST_AVOID]->(ng)
            MERGE (ng)-[:IN_CONTEXT]->(con)  // ★ここを追加！(文脈への紐付け)
        )
        """
        
        with self.driver.session() as session:
            for item in knowledge_list:
                if not item.preference and not item.ng_action:
                    continue
                try:
                    session.run(query, 
                                client_name=item.client_name,
                                preference=item.preference,
                                condition=item.condition,
                                ng_action=item.ng_action)
                    print(f"  ✅ 登録成功: {item.condition} -> Pref:{item.preference} / NG:{item.ng_action}")
                except Exception as e:
                    print(f"  ❌ エラー: {e}")
        return "処理完了"

# --- 3. Agno エージェント定義 (変更なし) ---
neo4j_tools = Neo4jTools()
agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
    tools=[neo4j_tools.register_knowledge],
    description="親亡き後支援DBの構築エンジニア",
    instructions=[
        "与えられたテキストは、障害のある当事者の支援記録（日記）である。",
        "ここから支援に必要な『事実』を抽出し、ナレッジグラフに登録せよ。",
        "",
        "【抽出ルール】",
        "1. 文脈を読み解き、'CareKnowledge' オブジェクトのリストを作成すること。",
        "2. 1つの文章に複数の要素が含まれる場合は、無理にまとめず、複数のオブジェクトに分割すること。",
        "3. **NgAction（禁忌）は最も重要である。** 『してはいけない』『パニックになる』等の記述には敏感に反応し、漏らさず抽出せよ。",
        "4. Condition（理由・特性）は必ず推測し、すべての項目に紐付けること。",
        "",
        "【禁止事項】",
        "・元のテキストにない情報を創作（ハルシネーション）しないこと。",
        "・NgActionをCarePreferenceと混同しないこと。"
    ],
    markdown=True
)

if __name__ == "__main__":
    diary_text = """
    【2024/12/15 記録者: 母】
    息子の健太は、急な予定変更があるとフリーズします。
    その時は5分ほど静かに待ってあげると落ち着きます。
    絶対に大声で急かしたり腕を引っ張ったりしないでください。パニックが悪化して自傷につながります。
    あと、食事の時は必ずテレビを消してください。気が散って食べなくなります。
    """
    print("🚀 データベース構築エージェントを起動します...")
    agent.print_response(f"以下の記録をデータベース化してください:\n\n{diary_text}")