import sys
import os
import json
from dotenv import load_dotenv

# Ensure root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.input_agent import InputAgent
from agents.support_agent import SupportAgent
from agents.watchdog import EmergencyWatchdog

load_dotenv()

def main():
    print("🚀 Starting Agno Agent Team Simulation...")
    
    # 1. Initialize Team
    input_agent = InputAgent()
    support_agent = SupportAgent()
    watchdog = EmergencyWatchdog()
    
    # 2. Scenario Input
    scenario_text = """
    【緊急連絡】
    山田花子です。母（山田太郎の母）が本日午後、自宅で転倒し、救急車で運ばれました。
    大腿骨骨折の疑いで、そのまま緊急入院することになりました。
    
    太郎は今、作業所にいますが、夕方の帰宅時に家には誰もいません。
    私は病院の手続きで戻れません。
    太郎はパニックになるかもしれません。
    どうすればよいでしょうか？
    SOSです。
    """
    
    print(f"\n📝 Scenario:\n{scenario_text}\n")
    
    # 3. Watchdog Check (Fast-path)
    print("--- [Step 1: Emergency Watchdog] ---")
    if watchdog.check_fast_path(scenario_text):
        print("🚨 FAST-PATH TRIGGERED! Emergency keywords detected.")
        print("   Running Emergency Search immediately...")
        client_name = "山田太郎" 
        response = watchdog.run(f"Emergency detected for {client_name}. Search for emergency contact and NgActions.", stream=False)
        print(f"\n[Watchdog Output]:\n{response.content}\n")
    
    # 4. Input Processing (Deep Path)
    print("--- [Step 2: Input Agent] ---")
    print("   Structuring narrative...")
    extraction_response = input_agent.run(f"Process this text: {scenario_text}", stream=False)
    structured_data = extraction_response.content
    print(f"\n[Input Agent Output]:\n{structured_data}\n")
    
    # 5. Support Agent (Planning)
    print("--- [Step 3: Support Agent] ---")
    print("   Analyzing situation and planning alternatives...")
    
    planning_prompt = f"""
    Based on the following situation, formulate a support plan (Plan B).
    
    Situation: {scenario_text}
    
    Structured Data:
    {structured_data}
    
    Task:
    1. Check if 'Unaccompanied' is a risk.
    2. Find KeyPersons to contact.
    3. Propose a concrete action plan for Taro.
    4. Ask for user approval.
    """
    
    support_response = support_agent.run(planning_prompt, stream=False)
    print(f"\n[Support Agent Output]:\n{support_response.content}\n")
    
    # 6. Approval Simulation
    print("--- [Step 4: Approval] ---")
    # For automated running in this environment, we skip input()
    print(">> Do you approve this plan? (y/n): [Auto-answering 'y' for demo]")
    print("✅ Plan Approved. Executing... (Simulated)")

if __name__ == "__main__":
    main()
