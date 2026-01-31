
import sys
import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Adjust path to find lib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from lib.db_operations import run_query


def analyze_transition_impact(key_person_name: str) -> str:
    """
    Analyze what roles are impacted if the KeyPerson becomes unavailable.
    Implements specific logic for Finance/Asset Management:
    - Prioritize existing Adult Guardian.
    - If none, suggest Social Welfare Council (Daily Life Support) and recommend Guardianship.
    """
    print(f"🔍 Analyzing impact for: {key_person_name}...")
    
    # 0. Identify the Client associated with this KeyPerson
    client_res = run_query("""
        MATCH (kp:KeyPerson {name: $name})<-[:HAS_KEY_PERSON]-(c:Client)
        RETURN c.name as name
    """, {"name": key_person_name})
    
    client_name = client_res[0]['name'] if client_res else None
    
    # 1. Find roles fulfilled by this person
    roles = run_query("""
        MATCH (kp:KeyPerson {name: $name})-[:FULFILLS]->(role:CareRole)
        RETURN role.name as role_name, role.category as category
    """, {"name": key_person_name})
    
    if not roles:
        return json.dumps({"status": "no_roles_found", "message": f"{key_person_name} is not currently assigned any specific Care Roles in the graph."})
    
    impact_report = {
        "unavailable_person": key_person_name,
        "affected_client": client_name,
        "impacted_roles": [],
        "immediate_action_required": False
    }
    
    # 2. For each role, find potential alternatives
    for r in roles:
        role_name = r['role_name']
        category = r.get('category', '')
        
        role_info = {
            "role": role_name,
            "category": category,
            "alternatives": [],
            "advice": []
        }
        
        # --- SPECIAL LOGIC: Finance / Asset Management ---
        if category == 'Finance' or role_name in ['金銭管理', '財産管理']:
            # Check for existing Guardian
            guardians = []
            if client_name:
                guardians = run_query("""
                    MATCH (c:Client {name: $name})-[:HAS_GUARDIAN]->(g:Guardian)
                    RETURN g.name as name, g.type as type, g.phone as phone
                """, {"name": client_name})
            
            if guardians:
                # Case A: Guardian exists
                for g in guardians:
                    role_info["alternatives"].append({
                        "service_name": g['name'],
                        "type": f"Adult Guardian ({g['type']})",
                        "phone": g.get('phone', 'N/A'),
                        "priority": "High"
                    })
                role_info["advice"].append("成年後見人が登録されています。直ちに連絡を取り、業務を引き継いでください。")
            else:
                # Case B: No Guardian -> Social Welfare Council + Recommendation
                role_info["alternatives"].append({
                    "service_name": "社会福祉協議会",
                    "type": "日常生活自立支援事業",
                    "priority": "Medium (Fallback)"
                })
                
                # Check for dynamic Core Agency in DB
                core_agencies = run_query("""
                    MATCH (s:Service {type: 'CoreAgency'})
                    RETURN s.name as name, s.phone as phone
                """)
                
                agency_text = "お住まいの自治体の「中核機関（成年後見支援センター）」"
                if core_agencies:
                     agency = core_agencies[0]
                     agency_text = f"中核機関である **{agency['name']}（{agency.get('phone', '連絡先登録なし')}）**"

                role_info["advice"].append("成年後見人が不在です。まずは地元の社会福祉協議会による「日常生活自立支援事業」の利用を検討してください。")
                role_info["advice"].append(f"並行して、{agency_text} へ相談し、「成年後見制度」の利用検討を進めてください。")
        
        else:
            # --- Generic Logic for other roles ---
            alternatives = run_query("""
                MATCH (s:Service)-[:CAN_FULFILL]->(role:CareRole {name: $role})
                RETURN s.name as service_name, s.type as type, s.phone as phone
            """, {"role": role_name})
            
            for alt in alternatives:
                role_info["alternatives"].append(alt)
                
            if len(role_info["alternatives"]) == 0:
                impact_report["immediate_action_required"] = True
                role_info["advice"].append("代替サービスが見つかりません。相談支援専門員（高齢者の場合はケアマネジャー）に至急相談してください。")

        impact_report["impacted_roles"].append(role_info)
            
    return json.dumps(impact_report, indent=2, ensure_ascii=False)


def suggest_alternatives(role_name: str) -> str:
    """
    Suggest specific alternatives for a role.
    """
    print(f"💡 Finding alternatives for role: {role_name}...")
    
    candidates = run_query("""
        MATCH (s:Service)-[:CAN_FULFILL]->(r:CareRole {name: $role})
        RETURN s.name as name, s.type as type, s.location as location, s.capacity as capacity
    """, {"role": role_name})
    
    return json.dumps(candidates, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python transition_handler.py [analyze_impact|suggest] [ARG]")
        sys.exit(1)
        
    command = sys.argv[1]
    arg = sys.argv[2]
    
    if command == "analyze_impact":
        print(analyze_transition_impact(arg))
    elif command == "suggest":
        print(suggest_alternatives(arg))
    else:
        print(f"Unknown command: {command}")
