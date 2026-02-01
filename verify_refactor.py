
import sys
import os
from dotenv import load_dotenv

# Ensure we can import from the current directory
sys.path.insert(0, os.getcwd())

from agents.input_agent import InputAgent
from agents.support_agent import SupportAgent
from agents.watchdog import EmergencyWatchdog

load_dotenv()

def verify():
    print("🧪 Starting Verification...")
    
    # 1. Initialize
    try:
        watchdog = EmergencyWatchdog()
        input_agent = InputAgent()
        support_agent = SupportAgent()
        print("✅ Agents initialized successfully.")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return

    # 2. Test Watchdog (Emergency)
    emergency_text = "SOS! 山田さんが倒れました！救急車！"
    print(f"\n🧪 Testing Watchdog with: '{emergency_text}'")
    if watchdog.check_fast_path(emergency_text):
        print("✅ Watchdog correctly detected emergency.")
    else:
        print("❌ Watchdog FAILED to detect emergency.")

    # 3. Test InputAgent (Normal)
    normal_text = "山田さんは今日、落ち着いて過ごしました。"
    print(f"\n🧪 Testing InputAgent with: '{normal_text}'")
    try:
        response = input_agent.run(f"Process this text: {normal_text}")
        print("✅ InputAgent ran successfully.")
        # print(response.content) # Optional: print content
    except Exception as e:
        print(f"❌ InputAgent failed: {e}")

    print("\n🎉 Verification Complete.")

if __name__ == "__main__":
    verify()
