
import os
import sys
import json
from datetime import datetime

# Add parent directory to path to import lib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.db_operations import resolve_client, run_query

def smart_sos_decision(client_identifier: str, context: str):
    """
    Analyze context and return SOS plan (Recipients + Message Body).
    """
    client = resolve_client(client_identifier)
    if not client:
        return {"error": f"Client not found: {client_identifier}"}

    client_name = client.get('name')
    print(f"[{datetime.now()}] 🚨 Smart SOS Activated for {client_name}")
    print(f"Context: {context}")

    # 1. Context Analysis (Simple Heuristic for Prototype)
    # In real world, use LLM or Classifier
    is_medical = any(x in context.lower() for x in ['seizure', 'faint', 'bleed', 'injury', 'sick', 'pain', 'medical', '救急', '発作', '怪我'])
    is_behavioral = any(x in context.lower() for x in ['panic', 'shout', 'run', 'wander', 'behavior', 'patriot', 'パニック', '大声', '徘徊', '逃'])
    
    classification = "General"
    if is_medical:
        classification = "Medical"
    elif is_behavioral:
        classification = "Behavioral"
        
    print(f"Analysis: Classification = {classification}")

    # 2. Information Retrieval based on Classification
    relevant_info = {}
    
    if classification == "Medical":
        # Fetch Hospital & Conditions
        hospitals = run_query("""
            MATCH (c:Client)-[:TREATED_AT]->(h:Hospital)
            WHERE c.name = $name
            RETURN h.name, h.phone
        """, {"name": client_name})
        
        conditions = run_query("""
            MATCH (c:Client)-[:HAS_CONDITION]->(cond:Condition)
            WHERE c.name = $name AND cond.status = 'Active'
            RETURN cond.name
        """, {"name": client_name})
        
        relevant_info['hospitals'] = [h['h.name'] for h in hospitals]
        relevant_info['conditions'] = [c['cond.name'] for c in conditions]
        
    elif classification == "Behavioral":
        # Fetch Care Preferences
        care_prefs = run_query("""
            MATCH (c:Client)-[:REQUIRES]->(cp:CarePreference)
            WHERE c.name = $name AND cp.priority = 'High'
            RETURN cp.category, cp.instruction
        """, {"name": client_name})
        
        relevant_info['care_prefs'] = [f"{cp['cp.category']}: {cp['cp.instruction']}" for cp in care_prefs]

    # 3. Recipient Selection (Always include KeyPerson Rank 1)
    key_persons = run_query("""
        MATCH (c:Client)-[r:HAS_KEY_PERSON]->(kp:KeyPerson)
        WHERE c.name = $name
        RETURN kp.name, kp.relationship, kp.phone, r.rank
        ORDER BY r.rank ASC
        LIMIT 2
    """, {"name": client_name})
    
    primary_contact = key_persons[0] if key_persons else {"kp.name": "Unknown", "kp.phone": "Unknown"}

    # 4. Message Generation
    message_body = f"SOS: {client_name} needs help.\n"
    message_body += f"Situation: {context} ({classification})\n"
    message_body += f"Primary Contact: {primary_contact.get('kp.name')} ({primary_contact.get('kp.phone')})\n"
    
    if classification == "Medical":
        message_body += "\n[Medical Info]\n"
        message_body += f"Conditions: {', '.join(relevant_info.get('conditions', []))}\n"
        message_body += f"Hospitals: {', '.join(relevant_info.get('hospitals', []))}\n"
        message_body += "Action: Call Ambulance if critical. Contact Hospital."
        
    elif classification == "Behavioral":
        message_body += "\n[Care Instructions]\n"
        instructions = relevant_info.get('care_prefs', [])
        if instructions:
            message_body += "\n".join(f"- {i}" for i in instructions)
        else:
            message_body += "- No high priority care preferences found."
        message_body += "\nAction: Approach calmly. Follow instructions above."

    else:
        message_body += "\nAction: Contact Key Person immediately."

    # Output decision object
    decision = {
        "classification": classification,
        "recipients": [kp['kp.name'] for kp in key_persons],
        "message": message_body
    }
    
    print("\n---------------- SOS PLAN ----------------")
    print(json.dumps(decision, indent=2, ensure_ascii=False))
    print("------------------------------------------")
    
    return decision

if __name__ == "__main__":
    if len(sys.argv) > 2:
        smart_sos_decision(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python smart_sos.py <ClientName> <Context>")
