
import sys
import os
import requests
import time
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from lib.db_operations import run_query
except ImportError:
    # Basic fallback if path magic fails
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from lib.db_operations import run_query

def run_cypher(query, params=None):
    # Adapter for db_client style call
    return run_query(query, params)

def clean_db():
    run_cypher("MATCH (c:Client {name: 'ResilienceTestUser'}) DETACH DELETE c")
    run_cypher("MATCH (kp:KeyPerson {name: 'TestMother'}) DETACH DELETE kp")
    run_cypher("MATCH (r:CareRole {category: 'EmergencyTest'}) DETACH DELETE r")

def seed_db():
    # Create Client, Parent, and a Role with NO alternative (High Priority)
    run_cypher("""
        MERGE (c:Client {name: 'ResilienceTestUser', clientId: 'c-res-01'})
        MERGE (kp:KeyPerson {name: 'TestMother', relationship: '母'})
        MERGE (kp)<-[:HAS_KEY_PERSON]-(c)
        MERGE (r:CareRole {name: '緊急時の役割', category: 'EmergencyTest'})
        MERGE (kp)-[:FULFILLS]->(r)
    """)

def test_api():
    print("🚀 Starting Resilience API Flow Test")
    
    # 1. Start Server
    print("starting api server...")
    proc = subprocess.Popen(
        ["uv", "run", "python", "-u", "mobile/api_server.py"], # -u for unbuffered
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(10)  # Wait longer for startup

    try:
        # 2. Seed Data
        clean_db()
        seed_db()
        print("✅ DB Seeded.")

        # 3. Send Request
        api_url = "http://localhost:8080/api/narrative/extract"
        narrative = "母が急に倒れて入院することになりました。どうすればいいですか。"
        
        payload = {
            "text": narrative,
            "client_name": "ResilienceTestUser",
            "supporter_name": "TestSupporter"
        }
        
        print(f"📡 Sending Narrative: '{narrative}'")
        try:
            response = requests.post(api_url, json=payload, timeout=20)
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            print("\n--- SERVER LOGS ---")
            if proc.poll() is not None:
                outs, errs = proc.communicate()
            else:
                proc.terminate()
                outs, errs = proc.communicate()
            print(outs)
            print(errs)
            sys.exit(1)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response Received.")
            
            # 4. Verify Report
            report = data.get("resilience_report")
            if report and "緊急対応が必要" in report:
                print("🎉 SUCCESS: Resilience Report Detected!")
                print("-" * 20)
                print(report)
                print("-" * 20)
            else:
                print("❌ FAILED: Resilience Report missing or incorrect.")
                print(f"Response: {data}")
                
                # PRINT SERVER LOGS
                print("\n--- SERVER LOGS ---")
                if proc.poll() is None:
                    proc.terminate()
                outs, errs = proc.communicate()
                print(outs)
                print(errs)
                sys.exit(1)
        else:
            print(f"❌ API Failed: {response.status_code}")
            print(response.text)
            print("\n--- SERVER LOGS ---")
            if proc.poll() is None:
                proc.terminate()
            outs, errs = proc.communicate()
            print(outs)
            print(errs)
            sys.exit(1)

    finally:
        # 5. Cleanup
        print("🧹 Cleaning up...")
        if proc.poll() is None:
             proc.terminate()
        clean_db()

if __name__ == "__main__":
    test_api()
