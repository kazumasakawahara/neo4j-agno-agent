
import os
import sys
from dotenv import load_dotenv

# Import our specialized agents
from agents.input_agent import InputAgent
from agents.support_agent import SupportAgent
from agents.watchdog import EmergencyWatchdog

# Load environment variables
load_dotenv()

def main():
    """
    Main orchestration loop for the Support Team.
    
    Flow:
    1. User Input (Text)
    2. Watchdog Check (Fast Path for SOS)
    3. InputAgent (Extraction & Safety)
    4. SupportAgent (Reasoning & Response)
    """
    print("="*60)
    print("🛡️  Post-Parent Support Team - Active 🛡️")
    print("="*60)
    
    # Initialize Agents
    watchdog = EmergencyWatchdog()
    input_agent = InputAgent()
    support_agent = SupportAgent()
    
    # Simple interaction loop
    while True:
        try:
            print("\n📝 Enter narrative/report (or 'exit' to quit):")
            user_input = input(">> ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 System shutting down.")
                break
            
            if not user_input:
                continue

            print("\n--- 🕵️ Processing ---")

            # 1. Watchdog: Fast Path Check
            if watchdog.check_fast_path(user_input):
                print("\n🚨 EMERGENCY DETECTED! Triggering Watchdog...")
                watchdog.print_response(f"EMERGENCY SIGNAL RECEIVED: {user_input}\nAction: Search emergency info and guide immediately.")
                continue

            # 2. InputAgent: Structure & Gatekeep
            print("\n👤 InputAgent: Structuring data...")
            # We want to capture the structured output. 
            # In Agno, print_response prints to stdout. 
            # To get the response programmatically, we use .run() and access .content or messages.
            input_response = input_agent.run(f"Process this text: {user_input}")
            structured_data = input_response.content if hasattr(input_response, 'content') else str(input_response)
            
            print(f"\n📄 Structured Data (Preview):\n{structured_data}")
            
            # Simple safety check logic (heuristic based on InputAgent's tool usage)
            # Ideally, InputAgent would return a flag or specific object.
            # For this MVP, we pass the data to SupportAgent.

            # 3. SupportAgent: Plan & Act
            print("\n🧠 SupportAgent: Analyzing...")
            support_agent.print_response(f"""
            Here is the structured situation from InputAgent:
            {structured_data}
            
            Please analyze:
            1. Does this update the Client's history?
            2. Do we need to register this?
            3. Are there implies needs?
            """)

        except KeyboardInterrupt:
            print("\n👋 System shutting down.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
