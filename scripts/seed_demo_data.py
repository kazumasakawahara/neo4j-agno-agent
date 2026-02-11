"""
デモデータ投入スクリプト

3名のデモクライアントをNeo4jグラフデータベースに登録する。
冪等性を担保するため、投入前に既存のデモデータを削除する。

使用方法:
    uv run python scripts/seed_demo_data.py
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加し lib/ からインポート可能にする
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.db_operations import run_query, is_db_available


# =============================================================================
# デモクライアント定義
# =============================================================================

DEMO_CLIENT_NAMES = ["山田健太", "鈴木美咲", "田中大輝"]


def clear_demo_data() -> None:
    """既存のデモデータを削除（冪等性の担保）"""
    print("--- 既存デモデータの削除 ---")
    for name in DEMO_CLIENT_NAMES:
        # クライアントに紐づくSupportLogを削除（Supporter経由）
        run_query(
            """
            MATCH (c:Client {name: $name})
            OPTIONAL MATCH (c)<-[:ABOUT]-(log:SupportLog)<-[:LOGGED]-(s:Supporter)
            DETACH DELETE log
            """,
            {"name": name},
        )
        # Supporter -> Client の SUPPORTED_BY 関係とSupporterノード削除
        # (他クライアントに紐づかないSupporterのみ削除)
        run_query(
            """
            MATCH (s:Supporter)-[:LOGGED]->(:SupportLog)-[:ABOUT]->(:Client {name: $name})
            WHERE NOT EXISTS {
                MATCH (s)-[:LOGGED]->(:SupportLog)-[:ABOUT]->(other:Client)
                WHERE other.name <> $name
            }
            DETACH DELETE s
            """,
            {"name": name},
        )
        # クライアントと全関連ノードを削除
        run_query(
            """
            MATCH (c:Client {name: $name})
            OPTIONAL MATCH (c)-[]->(related)
            DETACH DELETE related, c
            """,
            {"name": name},
        )
        print(f"  削除完了: {name}")
    print()


# =============================================================================
# クライアント1: 山田健太
# =============================================================================

def seed_yamada_kenta() -> dict:
    """山田健太のデモデータを投入"""
    name = "山田健太"
    counts = {
        "Condition": 0,
        "NgAction": 0,
        "CarePreference": 0,
        "KeyPerson": 0,
        "Guardian": 0,
        "Hospital": 0,
        "Certificate": 0,
        "PublicAssistance": 0,
        "Supporter": 0,
        "SupportLog": 0,
    }

    print(f"--- {name} の登録開始 ---")

    # クライアント基本情報
    run_query(
        """
        MERGE (c:Client {name: $name})
        SET c.dob = date('1997-03-15'),
            c.bloodType = 'A'
        """,
        {"name": name},
    )
    print(f"  クライアント基本情報を登録")

    # 特性・診断
    conditions = [
        {"name": "自閉スペクトラム症", "status": "active"},
        {"name": "聴覚過敏", "status": "active"},
    ]
    for cond in conditions:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (con:Condition {name: $cond_name, status: $status})
            CREATE (c)-[:HAS_CONDITION]->(con)
            """,
            {"client": name, "cond_name": cond["name"], "status": cond["status"]},
        )
        counts["Condition"] += 1
    print(f"  特性・診断: {counts['Condition']}件")

    # 禁忌事項（NgAction）
    ng_actions = [
        {
            "action": "後ろから突然声をかける",
            "reason": "パニックを起こし自傷行為に至る可能性",
            "riskLevel": "LifeThreatening",
        },
        {
            "action": "食事中にテレビをつける",
            "reason": "食事に集中できず誤嚥のリスク",
            "riskLevel": "Panic",
        },
        {
            "action": "予定の急な変更",
            "reason": "強い不安からパニック",
            "riskLevel": "Panic",
        },
    ]
    for ng in ng_actions:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (ng:NgAction {action: $action, reason: $reason, riskLevel: $riskLevel})
            CREATE (c)-[:MUST_AVOID]->(ng)
            """,
            {
                "client": name,
                "action": ng["action"],
                "reason": ng["reason"],
                "riskLevel": ng["riskLevel"],
            },
        )
        counts["NgAction"] += 1
    print(f"  禁忌事項: {counts['NgAction']}件")

    # 推奨ケア（CarePreference）
    care_prefs = [
        {
            "category": "パニック時対応",
            "instruction": "静かな部屋に誘導し背中をゆっくりさする（5分程度で落ち着く）",
            "priority": 10,
        },
        {
            "category": "日常支援",
            "instruction": "イヤーマフを常備し騒がしい環境では装着を促す",
            "priority": 8,
        },
        {
            "category": "コミュニケーション",
            "instruction": "視覚的スケジュール表を使い事前に予定を伝える",
            "priority": 7,
        },
    ]
    for cp in care_prefs:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (cp:CarePreference {category: $category, instruction: $instruction, priority: $priority})
            CREATE (c)-[:REQUIRES]->(cp)
            """,
            {
                "client": name,
                "category": cp["category"],
                "instruction": cp["instruction"],
                "priority": cp["priority"],
            },
        )
        counts["CarePreference"] += 1
    print(f"  推奨ケア: {counts['CarePreference']}件")

    # キーパーソン
    key_persons = [
        {"name": "山田花子", "relationship": "母", "phone": "090-1234-5678", "role": "主介護者", "rank": 1},
        {"name": "山田一郎", "relationship": "弟", "phone": "090-8765-4321", "role": "緊急時連絡先", "rank": 2},
    ]
    for kp in key_persons:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (kp:KeyPerson {name: $kp_name, relationship: $rel, phone: $phone, role: $role})
            CREATE (c)-[r:HAS_KEY_PERSON {rank: $rank}]->(kp)
            """,
            {
                "client": name,
                "kp_name": kp["name"],
                "rel": kp["relationship"],
                "phone": kp["phone"],
                "role": kp["role"],
                "rank": kp["rank"],
            },
        )
        counts["KeyPerson"] += 1
    print(f"  キーパーソン: {counts['KeyPerson']}件")

    # 後見人
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (g:Guardian {name: '山田花子', type: '保佐人', phone: '090-1234-5678'})
        CREATE (c)-[:HAS_LEGAL_REP]->(g)
        """,
        {"client": name},
    )
    counts["Guardian"] += 1
    print(f"  後見人: {counts['Guardian']}件")

    # 医療機関
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (h:Hospital {name: '北九州総合病院', specialty: '精神科', phone: '093-555-0001', doctor: '中村先生'})
        CREATE (c)-[:TREATED_AT]->(h)
        """,
        {"client": name},
    )
    counts["Hospital"] += 1
    print(f"  医療機関: {counts['Hospital']}件")

    # 手帳・受給者証
    # 療育手帳: 30日後に更新期限
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (cert:Certificate {type: '療育手帳', grade: 'A判定', nextRenewalDate: date() + duration({days: 30})})
        CREATE (c)-[:HAS_CERTIFICATE]->(cert)
        """,
        {"client": name},
    )
    counts["Certificate"] += 1

    # 障害基礎年金証書
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (cert:Certificate {type: '障害基礎年金証書', grade: '1級', nextRenewalDate: date('2027-03-31')})
        CREATE (c)-[:HAS_CERTIFICATE]->(cert)
        """,
        {"client": name},
    )
    counts["Certificate"] += 1
    print(f"  手帳・受給者証: {counts['Certificate']}件")

    # 公的扶助
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (pa:PublicAssistance {type: '障害基礎年金', grade: '1級'})
        CREATE (c)-[:RECEIVES]->(pa)
        """,
        {"client": name},
    )
    counts["PublicAssistance"] += 1
    print(f"  公的扶助: {counts['PublicAssistance']}件")

    # 支援者
    run_query(
        """
        MERGE (s:Supporter {name: '佐藤美穂'})
        SET s.role = 'ヘルパー',
            s.organization = 'あおぞら福祉サービス'
        WITH s
        MATCH (c:Client {name: $client})
        MERGE (c)-[:SUPPORTED_BY]->(s)
        """,
        {"client": name},
    )
    counts["Supporter"] += 1
    print(f"  支援者: {counts['Supporter']}件")

    # 支援記録
    support_logs = [
        {
            "supporter": "佐藤美穂",
            "days_ago": 7,
            "situation": "公園で犬の鳴き声にパニック",
            "response": "イヤーマフ装着し静かなベンチへ誘導、5分で落ち着いた",
            "effectiveness": "effective",
        },
        {
            "supporter": "佐藤美穂",
            "days_ago": 3,
            "situation": "新しいお菓子（抹茶クッキー）を気に入った様子",
            "response": "笑顔で完食した",
            "effectiveness": "positive",
        },
    ]
    for sl in support_logs:
        run_query(
            """
            MATCH (c:Client {name: $client})
            MATCH (s:Supporter {name: $supporter})
            CREATE (log:SupportLog {
                date: date() - duration({days: $days_ago}),
                situation: $situation,
                response: $response,
                effectiveness: $effectiveness
            })
            CREATE (s)-[:LOGGED]->(log)
            CREATE (log)-[:ABOUT]->(c)
            """,
            {
                "client": name,
                "supporter": sl["supporter"],
                "days_ago": sl["days_ago"],
                "situation": sl["situation"],
                "response": sl["response"],
                "effectiveness": sl["effectiveness"],
            },
        )
        counts["SupportLog"] += 1
    print(f"  支援記録: {counts['SupportLog']}件")

    print(f"  >>> {name} 登録完了\n")
    return counts


# =============================================================================
# クライアント2: 鈴木美咲
# =============================================================================

def seed_suzuki_misaki() -> dict:
    """鈴木美咲のデモデータを投入"""
    name = "鈴木美咲"
    counts = {
        "Condition": 0,
        "NgAction": 0,
        "CarePreference": 0,
        "KeyPerson": 0,
        "Guardian": 0,
        "Hospital": 0,
        "Certificate": 0,
        "PublicAssistance": 0,
        "Supporter": 0,
        "SupportLog": 0,
    }

    print(f"--- {name} の登録開始 ---")

    # クライアント基本情報
    run_query(
        """
        MERGE (c:Client {name: $name})
        SET c.dob = date('2003-07-22'),
            c.bloodType = 'O'
        """,
        {"name": name},
    )
    print(f"  クライアント基本情報を登録")

    # 特性・診断
    conditions = [
        {"name": "ダウン症", "status": "active"},
        {"name": "先天性心疾患", "status": "active"},
    ]
    for cond in conditions:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (con:Condition {name: $cond_name, status: $status})
            CREATE (c)-[:HAS_CONDITION]->(con)
            """,
            {"client": name, "cond_name": cond["name"], "status": cond["status"]},
        )
        counts["Condition"] += 1
    print(f"  特性・診断: {counts['Condition']}件")

    # 禁忌事項
    ng_actions = [
        {
            "action": "激しい運動（全力疾走や階段の駆け上がり）",
            "reason": "心臓への過度な負荷",
            "riskLevel": "LifeThreatening",
        },
        {
            "action": "急な予定変更",
            "reason": "強い混乱と泣き続ける",
            "riskLevel": "Panic",
        },
    ]
    for ng in ng_actions:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (ng:NgAction {action: $action, reason: $reason, riskLevel: $riskLevel})
            CREATE (c)-[:MUST_AVOID]->(ng)
            """,
            {
                "client": name,
                "action": ng["action"],
                "reason": ng["reason"],
                "riskLevel": ng["riskLevel"],
            },
        )
        counts["NgAction"] += 1
    print(f"  禁忌事項: {counts['NgAction']}件")

    # 推奨ケア
    care_prefs = [
        {
            "category": "コミュニケーション",
            "instruction": "絵カードを使って選択肢を提示する",
            "priority": 10,
        },
        {
            "category": "日常支援",
            "instruction": "スケジュールを視覚化して朝に確認する習慣をつける",
            "priority": 9,
        },
        {
            "category": "運動管理",
            "instruction": "軽い散歩は可。心拍数が上がる活動は避ける",
            "priority": 8,
        },
    ]
    for cp in care_prefs:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (cp:CarePreference {category: $category, instruction: $instruction, priority: $priority})
            CREATE (c)-[:REQUIRES]->(cp)
            """,
            {
                "client": name,
                "category": cp["category"],
                "instruction": cp["instruction"],
                "priority": cp["priority"],
            },
        )
        counts["CarePreference"] += 1
    print(f"  推奨ケア: {counts['CarePreference']}件")

    # キーパーソン
    key_persons = [
        {"name": "鈴木太郎", "relationship": "父", "phone": "090-2222-3333", "role": "主介護者", "rank": 1},
        {"name": "鈴木恵", "relationship": "姉", "phone": "090-4444-5555", "role": "緊急時連絡先", "rank": 2},
    ]
    for kp in key_persons:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (kp:KeyPerson {name: $kp_name, relationship: $rel, phone: $phone, role: $role})
            CREATE (c)-[r:HAS_KEY_PERSON {rank: $rank}]->(kp)
            """,
            {
                "client": name,
                "kp_name": kp["name"],
                "rel": kp["relationship"],
                "phone": kp["phone"],
                "role": kp["role"],
                "rank": kp["rank"],
            },
        )
        counts["KeyPerson"] += 1
    print(f"  キーパーソン: {counts['KeyPerson']}件")

    # 医療機関
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (h:Hospital {name: '北九州市立医療センター', specialty: '循環器科', phone: '093-555-0002', doctor: '高橋先生'})
        CREATE (c)-[:TREATED_AT]->(h)
        """,
        {"client": name},
    )
    counts["Hospital"] += 1
    print(f"  医療機関: {counts['Hospital']}件")

    # 手帳・受給者証: 60日後に更新期限
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (cert:Certificate {type: '療育手帳', grade: 'B1判定', nextRenewalDate: date() + duration({days: 60})})
        CREATE (c)-[:HAS_CERTIFICATE]->(cert)
        """,
        {"client": name},
    )
    counts["Certificate"] += 1
    print(f"  手帳・受給者証: {counts['Certificate']}件")

    # 公的扶助
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (pa:PublicAssistance {type: '特別障害者手当', grade: '該当'})
        CREATE (c)-[:RECEIVES]->(pa)
        """,
        {"client": name},
    )
    counts["PublicAssistance"] += 1
    print(f"  公的扶助: {counts['PublicAssistance']}件")

    # 支援者
    run_query(
        """
        MERGE (s:Supporter {name: '田中裕子'})
        SET s.role = '生活支援員',
            s.organization = 'ひまわり園'
        WITH s
        MATCH (c:Client {name: $client})
        MERGE (c)-[:SUPPORTED_BY]->(s)
        """,
        {"client": name},
    )
    counts["Supporter"] += 1
    print(f"  支援者: {counts['Supporter']}件")

    # 支援記録
    run_query(
        """
        MATCH (c:Client {name: $client})
        MATCH (s:Supporter {name: '田中裕子'})
        CREATE (log:SupportLog {
            date: date() - duration({days: 5}),
            situation: '絵カードで「散歩」を選び30分公園を楽しんだ',
            response: '本人の希望を尊重し見守り',
            effectiveness: 'positive'
        })
        CREATE (s)-[:LOGGED]->(log)
        CREATE (log)-[:ABOUT]->(c)
        """,
        {"client": name},
    )
    counts["SupportLog"] += 1
    print(f"  支援記録: {counts['SupportLog']}件")

    print(f"  >>> {name} 登録完了\n")
    return counts


# =============================================================================
# クライアント3: 田中大輝
# =============================================================================

def seed_tanaka_daiki() -> dict:
    """田中大輝のデモデータを投入"""
    name = "田中大輝"
    counts = {
        "Condition": 0,
        "NgAction": 0,
        "CarePreference": 0,
        "KeyPerson": 0,
        "Guardian": 0,
        "Hospital": 0,
        "Certificate": 0,
        "PublicAssistance": 0,
        "Supporter": 0,
        "SupportLog": 0,
    }

    print(f"--- {name} の登録開始 ---")

    # クライアント基本情報
    run_query(
        """
        MERGE (c:Client {name: $name})
        SET c.dob = date('1990-11-08'),
            c.bloodType = 'B'
        """,
        {"name": name},
    )
    print(f"  クライアント基本情報を登録")

    # 特性・診断
    conditions = [
        {"name": "重度知的障害", "status": "active"},
        {"name": "てんかん", "status": "active"},
    ]
    for cond in conditions:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (con:Condition {name: $cond_name, status: $status})
            CREATE (c)-[:HAS_CONDITION]->(con)
            """,
            {"client": name, "cond_name": cond["name"], "status": cond["status"]},
        )
        counts["Condition"] += 1
    print(f"  特性・診断: {counts['Condition']}件")

    # 禁忌事項
    ng_actions = [
        {
            "action": "点滅する光やストロボライト",
            "reason": "てんかん発作を誘発する危険性",
            "riskLevel": "LifeThreatening",
        },
        {
            "action": "入浴中の一人放置",
            "reason": "発作時の溺水リスク",
            "riskLevel": "LifeThreatening",
        },
        {
            "action": "長時間の空腹状態",
            "reason": "低血糖による発作リスク増大",
            "riskLevel": "Panic",
        },
    ]
    for ng in ng_actions:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (ng:NgAction {action: $action, reason: $reason, riskLevel: $riskLevel})
            CREATE (c)-[:MUST_AVOID]->(ng)
            """,
            {
                "client": name,
                "action": ng["action"],
                "reason": ng["reason"],
                "riskLevel": ng["riskLevel"],
            },
        )
        counts["NgAction"] += 1
    print(f"  禁忌事項: {counts['NgAction']}件")

    # 推奨ケア
    care_prefs = [
        {
            "category": "発作時対応",
            "instruction": "安全な場所に横たえ頭部を保護。発作が5分以上続けば救急車を呼ぶ",
            "priority": 10,
        },
        {
            "category": "入浴",
            "instruction": "必ず支援者が付き添い浴室のドアは開けておく",
            "priority": 10,
        },
        {
            "category": "食事管理",
            "instruction": "3食+間食を規則正しく提供。空腹時間を4時間以上空けない",
            "priority": 9,
        },
    ]
    for cp in care_prefs:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (cp:CarePreference {category: $category, instruction: $instruction, priority: $priority})
            CREATE (c)-[:REQUIRES]->(cp)
            """,
            {
                "client": name,
                "category": cp["category"],
                "instruction": cp["instruction"],
                "priority": cp["priority"],
            },
        )
        counts["CarePreference"] += 1
    print(f"  推奨ケア: {counts['CarePreference']}件")

    # キーパーソン
    key_persons = [
        {"name": "田中和子", "relationship": "母", "phone": "090-6666-7777", "role": "主介護者", "rank": 1},
        {"name": "やまびこ荘", "relationship": "グループホーム", "phone": "093-555-0003", "role": "緊急受入先", "rank": 2},
    ]
    for kp in key_persons:
        run_query(
            """
            MATCH (c:Client {name: $client})
            CREATE (kp:KeyPerson {name: $kp_name, relationship: $rel, phone: $phone, role: $role})
            CREATE (c)-[r:HAS_KEY_PERSON {rank: $rank}]->(kp)
            """,
            {
                "client": name,
                "kp_name": kp["name"],
                "rel": kp["relationship"],
                "phone": kp["phone"],
                "role": kp["role"],
                "rank": kp["rank"],
            },
        )
        counts["KeyPerson"] += 1
    print(f"  キーパーソン: {counts['KeyPerson']}件")

    # 後見人
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (g:Guardian {name: '中島法律事務所', type: '成年後見人', phone: '093-555-0004'})
        CREATE (c)-[:HAS_LEGAL_REP]->(g)
        """,
        {"client": name},
    )
    counts["Guardian"] += 1
    print(f"  後見人: {counts['Guardian']}件")

    # 医療機関
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (h:Hospital {name: '九州労災病院', specialty: '神経内科', phone: '093-555-0005', doctor: '小林先生'})
        CREATE (c)-[:TREATED_AT]->(h)
        """,
        {"client": name},
    )
    counts["Hospital"] += 1
    print(f"  医療機関: {counts['Hospital']}件")

    # 手帳・受給者証
    # 療育手帳: 15日後に更新期限（緊急アラートデモ用）
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (cert:Certificate {type: '療育手帳', grade: 'A判定', nextRenewalDate: date() + duration({days: 15})})
        CREATE (c)-[:HAS_CERTIFICATE]->(cert)
        """,
        {"client": name},
    )
    counts["Certificate"] += 1

    # 自立支援医療受給者証: 45日後
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (cert:Certificate {type: '自立支援医療受給者証', grade: '該当', nextRenewalDate: date() + duration({days: 45})})
        CREATE (c)-[:HAS_CERTIFICATE]->(cert)
        """,
        {"client": name},
    )
    counts["Certificate"] += 1
    print(f"  手帳・受給者証: {counts['Certificate']}件")

    # 公的扶助
    run_query(
        """
        MATCH (c:Client {name: $client})
        CREATE (pa:PublicAssistance {type: '障害基礎年金', grade: '1級'})
        CREATE (c)-[:RECEIVES]->(pa)
        """,
        {"client": name},
    )
    counts["PublicAssistance"] += 1
    print(f"  公的扶助: {counts['PublicAssistance']}件")

    # 支援者
    run_query(
        """
        MERGE (s:Supporter {name: '木村誠'})
        SET s.role = '世話人',
            s.organization = 'やまびこ荘'
        WITH s
        MATCH (c:Client {name: $client})
        MERGE (c)-[:SUPPORTED_BY]->(s)
        """,
        {"client": name},
    )
    counts["Supporter"] += 1
    print(f"  支援者: {counts['Supporter']}件")

    # 支援記録
    support_logs = [
        {
            "supporter": "木村誠",
            "days_ago": 10,
            "situation": "夕食後にてんかん発作（約2分間）",
            "response": "ソファに横たえ頭部保護。発作後20分間安静確認",
            "effectiveness": "effective",
        },
        {
            "supporter": "木村誠",
            "days_ago": 2,
            "situation": "昼食時にカレーを完食。機嫌よく過ごした",
            "response": "食事量と時間を記録",
            "effectiveness": "positive",
        },
    ]
    for sl in support_logs:
        run_query(
            """
            MATCH (c:Client {name: $client})
            MATCH (s:Supporter {name: $supporter})
            CREATE (log:SupportLog {
                date: date() - duration({days: $days_ago}),
                situation: $situation,
                response: $response,
                effectiveness: $effectiveness
            })
            CREATE (s)-[:LOGGED]->(log)
            CREATE (log)-[:ABOUT]->(c)
            """,
            {
                "client": name,
                "supporter": sl["supporter"],
                "days_ago": sl["days_ago"],
                "situation": sl["situation"],
                "response": sl["response"],
                "effectiveness": sl["effectiveness"],
            },
        )
        counts["SupportLog"] += 1
    print(f"  支援記録: {counts['SupportLog']}件")

    print(f"  >>> {name} 登録完了\n")
    return counts


# =============================================================================
# メイン処理
# =============================================================================

def print_summary(all_counts: list[dict]) -> None:
    """登録結果のサマリーを表示"""
    totals: dict[str, int] = {}
    for counts in all_counts:
        for key, value in counts.items():
            totals[key] = totals.get(key, 0) + value

    print("=" * 50)
    print("デモデータ投入 サマリー")
    print("=" * 50)
    print(f"  クライアント数: {len(all_counts)}名")
    for node_type, count in sorted(totals.items()):
        print(f"  {node_type}: {count}件")

    total_nodes = sum(totals.values())
    print(f"  ---")
    print(f"  関連ノード合計: {total_nodes}件")
    print("=" * 50)


def main() -> None:
    """デモデータ投入のメインエントリポイント"""
    print("=" * 50)
    print("親亡き後支援データベース - デモデータ投入")
    print("=" * 50)
    print()

    # データベース接続確認
    print("Neo4jデータベースへの接続を確認中...")
    if not is_db_available():
        print("エラー: Neo4jデータベースに接続できません。")
        print("以下を確認してください:")
        print("  1. docker-compose up -d でNeo4jコンテナが起動しているか")
        print("  2. .env に NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD が設定されているか")
        sys.exit(1)
    print("接続確認完了\n")

    # 既存デモデータの削除
    clear_demo_data()

    # 各クライアントのデモデータ投入
    all_counts = []
    all_counts.append(seed_yamada_kenta())
    all_counts.append(seed_suzuki_misaki())
    all_counts.append(seed_tanaka_daiki())

    # サマリー表示
    print_summary(all_counts)
    print("\nデモデータの投入が完了しました。")


if __name__ == "__main__":
    main()
