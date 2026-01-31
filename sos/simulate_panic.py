
import sys
import os
import asyncio
from datetime import datetime

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sos.api_server import create_smart_sos_message
from lib.db_operations import run_query

async def simulate_panic_sos():
    print("🚑 SOS Orchestrator Simulation: Panic at Station")
    print("---------------------------------------------")

    client_name = "山田健太"
    
    # Context specific to the request
    # Since we can't easily injection "Situation: Panic" into the function arguments directly 
    # (as it takes structured DB objects), we will simulate the DB retrieval part manually 
    # OR we can trust the 'Smart SOS' prompt to infer from the location/context if we could pass it.
    # However, the current create_smart_sos_message signature doesn't take 'situation' text directly,
    # it infers from DB data. 
    # To properly simulate "Panic at Station", we need to ensure the DB has data relevant to this,
    # OR we rely on the prompt to generate a general emergency message.
    
    # Wait, the user asked for "Situation: Panic Attack". 
    # My current implementation of `create_smart_sos_message` retrieves context from DB (NgAction, CarePref).
    # It does NOT take current situational context (like "Panic") as an argument yet.
    # I should update the script to fetch the REAL data for Yamada Kenta to see how it handles it.
    # And I will mock the "Location" as a station coordinate.
    
    # Station Coordinates (Example: Shinjuku Station)
    latitude = 35.6896
    longitude = 139.7006
    
    print(f"Target: {client_name}")
    print(f"Location: Shinjuku Station (Lat: {latitude}, Lon: {longitude})")
    
    # Fetch DB Data (Real data for Yamada)
    key_persons = run_query("""
        MATCH (c:Client {name: $name})-[:HAS_KEY_PERSON]->(kp:KeyPerson)
        RETURN kp.name as name, kp.relationship as relationship, kp.phone as phone
    """, {"name": client_name})

    cautions = run_query("""
        MATCH (c:Client {name: $name})-[:MUST_AVOID]->(ng:NgAction)
        RETURN ng.action as action, ng.riskLevel as riskLevel
    """, {"name": client_name})
    
    care_preferences = run_query("""
        MATCH (c:Client {name: $name})-[:REQUIRES]->(cp:CarePreference)
        RETURN cp.category as category, cp.instruction as instruction, cp.priority as priority
    """, {"name": client_name})
    
    hospitals = run_query("""
        MATCH (c:Client {name: $name})-[:TREATED_AT]->(h:Hospital)
        RETURN h.name as name, h.specialty as specialty, h.phone as phone
    """, {"name": client_name})

    # Generate Message
    print("\n[Thinking...] Orchestrating message with Antigravity Agent...\n")
    
    message = create_smart_sos_message(
        client_name=client_name,
        key_persons=key_persons,
        cautions=cautions,
        care_preferences=care_preferences,
        hospitals=hospitals,
        latitude=latitude,
        longitude=longitude,
        accuracy=15.0,
        situation_context="パニック発作の疑い（駅のホーム）"
    )
    
    print("================ GENERATED LINE MESSAGE ================")
    print(message)
    print("========================================================")

if __name__ == "__main__":
    asyncio.run(simulate_panic_sos())
