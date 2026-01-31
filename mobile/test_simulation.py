
import sys
import os
import json
from fastapi.testclient import TestClient

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mobile.api_server import app

client = TestClient(app)

def test_simulation():
    print("🧪 Verification: Mobile API Safety Check")
    print("---------------------------------------")
    
    narrative = "今日は調子が良さそうだったので、気晴らしにロックフェスティバルの会場近くまで連れて行きました。少し音が大きかったですが、本人は興奮している様子でした。"
    print(f"📄 Input Narrative: {narrative}")
    print(f"👤 Client: 山田健太")
    print(f"🚫 Active NgAction: 極端に大きな音がする場所（コンサート等）")
    print("---------------------------------------")

    response = client.post("/api/narrative/extract", json={
        "text": narrative,
        "client_name": "山田健太",
        "supporter_name": "TestSupporter"
    })
    
    data = response.json()
    
    if data.get('safety_violation'):
        print("\n⚠️  [WARNING TRIGGERED]")
        print(f"Warning Message: {data.get('safety_warning')}")
        print("✅ Correctly identified compliance violation.")
    else:
        print("\n❌ [NO WARNING]")
        print("System failed to detect violation.")

if __name__ == "__main__":
    test_simulation()
