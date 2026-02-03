import os
import sys
from dotenv import load_dotenv

from agents.input_agent import InputAgent
from agents.support_agent import SupportAgent
from agents.watchdog import EmergencyWatchdog
from agents.clinical_advisor import ClinicalAdvisorAgent

load_dotenv()

def main():
    print("============================================================")
    print("🛡️  Post-Parent Support Team - Autonomous Agents Active 🛡️")
    print("============================================================")
    print("WARNING: This system provides AI-based suggestions, NOT medical advice.")
    print("ALWAYS consult with a qualified professional for medical decisions.")
    print("============================================================")
    print("Type 'exit' to quit.\n")
    
    # Initialize Team
    input_agent = InputAgent()
    support_agent = SupportAgent()
    watchdog = EmergencyWatchdog()
    clinical_advisor = ClinicalAdvisorAgent()
    
    while True:
        try:
            user_input = input("📝 Enter narrative/report (or 'exit'):\n>> ")
            if user_input.lower() in ['exit', 'quit']:
                print("Shutting down agent team.")
                break
            
            if not user_input.strip():
                continue

            print("\n🔄 Processing...")

            # 1. Watchdog Fast-Path
            if watchdog.check_fast_path(user_input):
                print("\n[🚨 EMERGENCY WATCHDOG TRIGGERED]")
                # Using run(stream=True) for immediate feedback if supported, or just print response
                response = watchdog.run(f"Emergency detected: {user_input}. Analyze context and search info immediately!", stream=False)
                print(f"\n{response.content}\n")
                continue

            # 2. Input Agent (Structure & Check)
            print("\n[📥 Input Agent: Structuring Data...]")
            extraction_res = input_agent.run(f"Process this text: {user_input}", stream=False)
            print(f"\n{extraction_res.content}\n")
            
            formatted_data = extraction_res.content # In real app, this should be parsed JSON or passed as context

            # CHECK: Behavioral Issue?
            is_behavioral = any(k in user_input for k in ["拒否", "パニック", "自傷", "他害", "叫ぶ", "暴れる", "refusal", "panic", "meltdown"])
            
            if is_behavioral:
                print("\n[🩺 Clinical Advisor: Behavioral Challenge Detected...]")
                print("   Researching PBS strategies & Cross-referencing history...")
                
                advisor_prompt = f"""
                Situation: {user_input}
                
                Task:
                1. Identify the core behavioral issue.
                2. Research evidence-based strategies.
                3. Check internal records for the Client involved (extract name from: {formatted_data}).
                4. Propose a tailored solution in the specified format.
                """
                advisor_res = clinical_advisor.run(advisor_prompt, stream=True)
                
                print(f"\n[Clinical Advisor Proposal]:")
                for chunk in advisor_res:
                    print(chunk.content, end="", flush=True)
                print("\n")

            else:
                # 3. Support Agent (Reasoning & Skills)
                print("\n[🧠 Support Agent: Analyzing & Planning...]")
                # Pass the raw input + extracted context
                support_prompt = f"""
                User Input: {user_input}
                
                Extracted Context:
                {formatted_data}
                
                Task:
                1. If this is a request for information (e.g. "Generate report", "Show profile"), execute the tool directly.
                2. If this is a situation report, analyze risks and propose actions.
                3. Use your skills (Resilience, Care, Report) as needed.
                """
                
                support_res = support_agent.run(support_prompt, stream=True)
                
                # Streaming output for Support Agent
                print(f"\n[Support Agent Response]:")
                for chunk in support_res:
                    print(chunk.content, end="", flush=True)
                print("\n")

        except KeyboardInterrupt:
            print("\nShutting down.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
