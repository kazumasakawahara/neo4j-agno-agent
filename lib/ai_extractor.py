"""
親亡き後支援データベース - AI構造化モジュール
テキストからの情報抽出、JSON構造化処理
"""

import os
import re
import json
import sys
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini

load_dotenv()


# --- ログ出力 ---
def log(message: str, level: str = "INFO"):
    """ログ出力（標準エラー出力）"""
    sys.stderr.write(f"[AI_Extractor:{level}] {message}\n")
    sys.stderr.flush()

# =============================================================================
# AI抽出用プロンプト（マニフェスト準拠）
# =============================================================================

EXTRACTION_PROMPT = """
あなたは「親亡き後支援データベース」のデータ抽出専門家です。
提供されたテキストから、支援に必要な情報を**JSON形式で**抽出してください。

【重要な姿勢】
- 暗黙知を見逃さない：「〜すると落ち着く」「〜は嫌がる」を必ず拾う
- 禁忌事項（NgAction）は最優先：「絶対に〜しないで」「〜するとパニック」を漏らさない
- 推測で創作しない：テキストにない情報は出力しない
- 支援記録（日報・レポート）も抽出：「今日〜した」「〜の対応で落ち着いた」

【日付の変換ルール - 重要】
元号（和暦）で入力された日付は必ず西暦（YYYY-MM-DD形式）に変換してください：
- 明治元年=1868年、大正元年=1912年、昭和元年=1926年、平成元年=1989年、令和元年=2019年
- 例: 「昭和50年3月15日」→「1975-03-15」
- 例: 「平成7年12月1日」→「1995-12-01」
- 例: 「令和5年1月10日」→「2023-01-10」
- 例: 「S50.3.15」→「1975-03-15」
- 例: 「H7/12/1」→「1995-12-01」

【出力形式】
必ず以下のJSON構造で出力してください。該当がない項目は空配列[]としてください。

```json
{
  "client": {
    "name": "氏名（必須）",
    "dob": "生年月日（YYYY-MM-DD形式、不明なら null）",
    "bloodType": "血液型（不明なら null）"
  },
  "conditions": [
    {
      "name": "特性・診断名",
      "status": "Active"
    }
  ],
  "ngActions": [
    {
      "action": "絶対にしてはいけないこと",
      "reason": "その理由（なぜ危険か）",
      "riskLevel": "LifeThreatening または Panic または Discomfort",
      "relatedCondition": "関連する特性名（あれば）"
    }
  ],
  "carePreferences": [
    {
      "category": "食事/入浴/パニック時/移動/睡眠/服薬/コミュニケーション/その他",
      "instruction": "具体的な手順・方法",
      "priority": "High または Medium または Low",
      "relatedCondition": "関連する特性名（あれば）"
    }
  ],
  "supportLogs": [
    {
      "date": "記録日（YYYY-MM-DD形式、テキストから推定）",
      "supporter": "記録者・支援者名",
      "situation": "状況（パニック時/食事時/入浴時/外出時/コミュニケーション/その他）",
      "action": "実施した対応の具体的内容",
      "effectiveness": "Effective（効果的）/Neutral（変化なし）/Ineffective（逆効果）",
      "note": "詳細メモ・気づき"
    }
  ],
  "certificates": [
    {
      "type": "療育手帳/精神障害者保健福祉手帳/身体障害者手帳/障害福祉サービス受給者証/自立支援医療受給者証",
      "grade": "等級（A1, 2級, 区分5 など）",
      "nextRenewalDate": "更新日（YYYY-MM-DD形式）"
    }
  ],
  "keyPersons": [
    {
      "name": "氏名",
      "relationship": "続柄（母, 叔父, 姉 など）",
      "phone": "電話番号",
      "role": "役割（緊急連絡先, 医療同意, 金銭管理 など）",
      "rank": 1
    }
  ],
  "guardians": [
    {
      "name": "氏名または法人名",
      "type": "成年後見/保佐/補助/任意後見",
      "phone": "連絡先",
      "organization": "所属（法人の場合）"
    }
  ],
  "hospitals": [
    {
      "name": "病院名",
      "specialty": "診療科",
      "phone": "電話番号",
      "doctor": "担当医名"
    }
  ],
  "lifeHistories": [
    {
      "era": "時期（幼少期/学齢期/青年期/成人後）",
      "episode": "エピソード内容",
      "emotion": "その時の感情・反応"
    }
  ],
  "wishes": [
    {
      "content": "願いの内容",
      "date": "記録日（YYYY-MM-DD形式、今日なら今日の日付）"
    }
  ]
}
```

【抽出ルール】
1. 「〜すると落ち着く」「〜が好き」→ carePreferences
2. 「〜は嫌がる」「〜するとパニック」「絶対に〜しないで」→ ngActions（最重要！）
3. 「今日〜した」「〜の対応で効果があった」→ supportLogs（日報・支援記録）
4. 「〜に連絡して」「〜が後見人」→ keyPersons または guardians
5. 「来年の○月に更新」→ certificates（日付は2025年12月現在として推定）
6. 「かかりつけは○○病院」→ hospitals

【supportLogs抽出の重要ポイント】
- 「今日」「昨日」などの日付表現から実際の日付を推定
- 「効果的だった」「うまくいった」→ Effective
- 「変化なし」「いつも通り」→ Neutral
- 「悪化した」「逆効果」→ Ineffective
- 記録者名（田中ヘルパー、佐藤施設長など）を必ず抽出
- 対応の具体的内容を詳細に記録

【禁止事項】
- JSON以外のテキストを出力しない
- ```json と ``` で囲んで出力する
- テキストにない情報を創作しない
"""

# --- AIエージェント ---
_agent = None

def get_agent():
    """AIエージェントを取得（シングルトン）"""
    global _agent
    if _agent is None:
        _agent = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description="ナラティブから構造化データを抽出する専門家",
            instructions=[EXTRACTION_PROMPT],
            markdown=True
        )
    return _agent


def parse_json_from_response(response_text: str) -> dict | None:
    """
    AIレスポンスからJSONを抽出
    
    Args:
        response_text: AIからのレスポンステキスト
        
    Returns:
        パースされたdict、または失敗時はNone
    """
    try:
        # ```json ... ``` を抽出
        pattern = r'```json\s*(.*?)\s*```'
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # そのままJSONとしてパース試行
        return json.loads(response_text)
    except json.JSONDecodeError:
        return None


def extract_from_text(text: str, client_name: str = None) -> dict | None:
    """
    テキストから構造化データを抽出
    
    Args:
        text: 入力テキスト（ナラティブ、面談記録など）
        client_name: 既存クライアント名（追記モードの場合）
        
    Returns:
        構造化されたdict、または失敗時はNone
    """
    agent = get_agent()
    
    # 追記モードの場合、クライアント名を追加
    prompt_text = text
    if client_name:
        prompt_text = f"【対象クライアント: {client_name}】\n\n{text}"
    
    try:
        log(f"テキスト抽出開始（{len(text)}文字）")
        response = agent.run(
            f"以下のテキストから情報を抽出してJSON形式で出力してください：\n\n{prompt_text}"
        )

        extracted = parse_json_from_response(response.content)

        if extracted:
            # 追記モードの場合、クライアント名を設定
            if client_name and extracted.get('client'):
                extracted['client']['name'] = client_name
            log(f"抽出成功: クライアント={extracted.get('client', {}).get('name', '不明')}")
            return extracted

        log("JSONパース失敗: AIレスポンスからJSONを抽出できませんでした", "WARN")
        return None

    except Exception as e:
        log(f"抽出エラー: {type(e).__name__}: {e}", "ERROR")
        return None
