import streamlit as st
import json
import time
from dotenv import load_dotenv

# Import Agents
from agents.input_agent import InputAgent
from agents.support_agent import SupportAgent
from agents.watchdog import EmergencyWatchdog
from agents.clinical_advisor import ClinicalAdvisorAgent

# Load Environment Variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Post-Parent Support Team",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .chat-message {
        padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .chat-message.user {
        background-color: #ffffff;
        border-left: 5px solid #6c757d;
    }
    .chat-message.bot {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
    }
    .chat-message.sos {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
    }
    .chat-message.clinical {
        background-color: #fff8e1;
        border-left: 5px solid #ffc107;
    }
    .agent-avatar {
        width: 40px; height: 40px; border-radius: 50%; margin-right: 1rem;
        display: flex; align-items: center; justify-content: center; font-size: 20px;
    }
    h1 {
        color: #1a237e;
        font-family: 'Helvetica Neue', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Agents (Cached)
@st.cache_resource
def load_agents():
    return {
        "input": InputAgent(),
        "support": SupportAgent(),
        "watchdog": EmergencyWatchdog(),
        "clinical": ClinicalAdvisorAgent()
    }

agents = load_agents()

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/family.png", width=80)
    st.title("Support Team")
    st.markdown("---")
    st.markdown("### 🟢 Active Agents")
    st.success("📝 Input Agent")
    st.success("🧠 Support Agent")
    st.error("🐕 Emergency Watchdog")
    st.warning("🩺 Clinical Advisor")
    
    st.markdown("---")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Main Header
st.title("🛡️ Post-Parent Support Agent Team")
st.caption("AI-Powered Digital Guardianship System")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "data" in msg:
            with st.expander("🔍 Reasoning & Data"):
                st.json(msg["data"])

# User Input
if prompt := st.chat_input("日々の記録や、緊急の相談を入力してください..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent Processing Flow
    with st.status("🔄 Team is working...", expanded=True) as status:
        
        # 1. Watchdog
        status.update(label="🐕 Watchdog checking for emergencies...", state="running")
        watchdog_triggered = agents["watchdog"].check_fast_path(prompt)
        
        if watchdog_triggered:
            status.update(label="🚨 SOS DETECTED!", state="error")
            sos_res = agents["watchdog"].run(f"Emergency detected: {prompt}", stream=False)
            response_content = sos_res.content
            role = "assistant"
            
            # Highlight SOS
            st.error("🚨 EMERGENCY PROTOCOL ACTIVATED")
            st.markdown(f"**SOS Plan:**\n{response_content}")
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"🚨 **SOS ACTIVATED**\n\n{response_content}",
                "data": {"agent": "EmergencyWatchdog", "status": "Critical"}
            })

        else:
            # 2. Input Agent
            status.update(label="📝 Structuring data...", state="running")
            extraction_res = agents["input"].run(f"Process this text: {prompt}", stream=False)
            formatted_data = extraction_res.content
            
            # 3. Behavioral Check
            is_behavioral = any(k in prompt for k in ["拒否", "パニック", "自傷", "他害", "叫ぶ", "暴れる", "refusal", "panic", "meltdown"])
            
            if is_behavioral:
                status.update(label="🩺 Clinical Advisor researching...", state="running")
                
                advisor_prompt = f"""
                Situation: {prompt}
                Task:
                1. Identify behavioral issue.
                2. Research evidence-based strategies.
                3. Check internal records (Name from: {formatted_data}).
                4. Propose solution.
                """
                advisor_res = agents["clinical"].run(advisor_prompt, stream=False)
                response_content = advisor_res.content
                
                st.warning("🩺 Clinical Advice")
                st.markdown(response_content)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"🩺 **Clinical Advice**\n\n{response_content}",
                    "data": {"agent": "ClinicalAdvisor", "context": formatted_data}
                })
                
            else:
                status.update(label="🧠 Support Agent analyzing...", state="running")
                
                support_prompt = f"""
                User Input: {prompt}
                Extracted Context: {formatted_data}
                Task:
                1. Situation report -> Analyze risks & propose actions.
                2. Info request -> Execute tools.
                3. Use Resilience/Care/Report skills.
                """
                support_res = agents["support"].run(support_prompt, stream=False)
                response_content = support_res.content
                
                st.success("🧠 Support Plan")
                st.markdown(response_content)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"🧠 **Support Plan**\n\n{response_content}",
                    "data": {"agent": "SupportAgent", "context": formatted_data}
                })
        
        status.update(label="✅ Complete", state="complete", expanded=False)
