"""
親亡き後支援データベース - データベース操作モジュール
Neo4j接続、クエリ実行、データ登録処理
"""

import os
from datetime import date
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# --- Neo4j 接続 ---
_driver = None

def get_driver():
    """Neo4jドライバーを取得（シングルトン）"""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"), 
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )
    return _driver


def run_query(query, params=None):
    """Cypherクエリ実行ヘルパー"""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]


def register_to_database(data: dict) -> None:
    """
    構造化データをNeo4jに登録
    
    Args:
        data: AI構造化されたクライアントデータ（dict）
    """
    client_name = data['client']['name']
    
    # 1. クライアント基本情報
    run_query("""
        MERGE (c:Client {name: $name})
        SET c.dob = CASE WHEN $dob IS NOT NULL THEN date($dob) ELSE c.dob END,
            c.bloodType = COALESCE($blood, c.bloodType)
    """, {
        "name": client_name,
        "dob": data['client'].get('dob'),
        "blood": data['client'].get('bloodType')
    })
    
    # 2. 特性・診断
    for cond in data.get('conditions', []):
        if cond.get('name'):
            run_query("""
                MATCH (c:Client {name: $client})
                MERGE (con:Condition {name: $name})
                SET con.status = $status
                MERGE (c)-[:HAS_CONDITION]->(con)
            """, {"client": client_name, "name": cond['name'], "status": cond.get('status', 'Active')})
    
    # 3. 禁忌事項（NgAction）
    for ng in data.get('ngActions', []):
        if ng.get('action'):
            run_query("""
                MATCH (c:Client {name: $client})
                CREATE (ng:NgAction {action: $action, reason: $reason, riskLevel: $risk})
                CREATE (c)-[:MUST_AVOID]->(ng)
            """, {
                "client": client_name,
                "action": ng['action'],
                "reason": ng.get('reason', ''),
                "risk": ng.get('riskLevel', 'Panic')
            })
            
            # 関連特性との紐付け
            if ng.get('relatedCondition'):
                run_query("""
                    MATCH (ng:NgAction {action: $action})
                    MATCH (con:Condition {name: $cond})
                    MERGE (ng)-[:IN_CONTEXT]->(con)
                """, {"action": ng['action'], "cond": ng['relatedCondition']})
    
    # 4. 推奨ケア（CarePreference）
    for cp in data.get('carePreferences', []):
        if cp.get('instruction'):
            run_query("""
                MATCH (c:Client {name: $client})
                CREATE (cp:CarePreference {category: $cat, instruction: $inst, priority: $pri})
                CREATE (c)-[:REQUIRES]->(cp)
            """, {
                "client": client_name,
                "cat": cp.get('category', 'その他'),
                "inst": cp['instruction'],
                "pri": cp.get('priority', 'Medium')
            })
    
    # 5. 手帳・受給者証（Certificate）
    for cert in data.get('certificates', []):
        if cert.get('type'):
            run_query("""
                MATCH (c:Client {name: $client})
                CREATE (cert:Certificate {
                    type: $type,
                    grade: $grade,
                    nextRenewalDate: CASE WHEN $renewal IS NOT NULL THEN date($renewal) ELSE NULL END
                })
                CREATE (c)-[:HAS_CERTIFICATE]->(cert)
            """, {
                "client": client_name,
                "type": cert['type'],
                "grade": cert.get('grade'),
                "renewal": cert.get('nextRenewalDate')
            })
    
    # 6. キーパーソン（KeyPerson）
    for kp in data.get('keyPersons', []):
        if kp.get('name'):
            run_query("""
                MATCH (c:Client {name: $client})
                MERGE (kp:KeyPerson {name: $name, phone: $phone})
                SET kp.relationship = $rel, kp.role = $role
                MERGE (c)-[r:HAS_KEY_PERSON]->(kp)
                SET r.rank = $rank
            """, {
                "client": client_name,
                "name": kp['name'],
                "phone": kp.get('phone', ''),
                "rel": kp.get('relationship', ''),
                "role": kp.get('role', '緊急連絡先'),
                "rank": kp.get('rank', 1)
            })
    
    # 7. 後見人（Guardian）
    for g in data.get('guardians', []):
        if g.get('name'):
            run_query("""
                MATCH (c:Client {name: $client})
                CREATE (g:Guardian {name: $name, type: $type, phone: $phone, organization: $org})
                CREATE (c)-[:HAS_LEGAL_REP]->(g)
            """, {
                "client": client_name,
                "name": g['name'],
                "type": g.get('type', ''),
                "phone": g.get('phone', ''),
                "org": g.get('organization', '')
            })
    
    # 8. 医療機関（Hospital）
    for h in data.get('hospitals', []):
        if h.get('name'):
            run_query("""
                MATCH (c:Client {name: $client})
                MERGE (h:Hospital {name: $name})
                SET h.specialty = $spec, h.phone = $phone, h.doctor = $doc
                MERGE (c)-[:TREATED_AT]->(h)
            """, {
                "client": client_name,
                "name": h['name'],
                "spec": h.get('specialty', ''),
                "phone": h.get('phone', ''),
                "doc": h.get('doctor', '')
            })
    
    # 9. 生育歴（LifeHistory）
    for hist in data.get('lifeHistories', []):
        if hist.get('episode'):
            run_query("""
                MATCH (c:Client {name: $client})
                CREATE (h:LifeHistory {era: $era, episode: $episode, emotion: $emotion})
                CREATE (c)-[:HAS_HISTORY]->(h)
            """, {
                "client": client_name,
                "era": hist.get('era', ''),
                "episode": hist['episode'],
                "emotion": hist.get('emotion', '')
            })
    
    # 10. 願い（Wish）
    for wish in data.get('wishes', []):
        if wish.get('content'):
            run_query("""
                MATCH (c:Client {name: $client})
                CREATE (w:Wish {content: $content, status: 'Active', date: date($date)})
                CREATE (c)-[:HAS_WISH]->(w)
            """, {
                "client": client_name,
                "content": wish['content'],
                "date": wish.get('date', date.today().isoformat())
            })


def get_clients_list():
    """登録済みクライアント一覧を取得"""
    return [r['name'] for r in run_query("MATCH (c:Client) RETURN c.name as name ORDER BY c.name")]


def get_client_stats():
    """クライアント統計情報を取得"""
    client_count = run_query("MATCH (n:Client) RETURN count(n) as c")[0]['c']
    
    ng_by_client = run_query("""
        MATCH (c:Client)
        OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
        RETURN c.name as name, count(ng) as ng_count
        ORDER BY c.name
    """)
    
    return {
        'client_count': client_count,
        'ng_by_client': ng_by_client
    }
