import streamlit as st
import time
from dotenv import load_dotenv

# Import the new Unified Agent
from agents.unified_support_agent import UnifiedSupportAgent

# Load Environment Variables
load_dotenv()

# Page Config handled by app.py
# st.set_page_config(...) commented out for unified navigation

# Custom CSS for a more professional look
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
        color: #212529;
    }
    p, li, h1, h2, h3, h4, h5, h6 {
        color: #212529 !important;
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
        background-color: #eef5ff; /* A softer blue */
        border-left: 5px solid #007bff;
    }
    .chat-message.sos {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
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

# Initialize The Unified Agent (Cached)
@st.cache_resource
def load_agent():
    return UnifiedSupportAgent()

agent = load_agent()

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/family.png", width=80)
    st.title("Support Team")
    st.markdown("---")
    st.markdown("### 🟢 Active Agent")
    st.success("🤖 Unified Support Agent")
    
    st.markdown("---")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Main Header
st.title("🛡️ Post-Parent Support Agent")
st.caption("Unified AI for Digital Guardianship")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "data" in msg:
            with st.expander("🔍 Agent's Reasoning Data"):
                st.json(msg["data"])

# Handle User Input
if prompt := st.chat_input("日々の記録や、緊急の相談を入力してください..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent's turn to respond
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        with st.status("🤖 Agent is thinking...", expanded=True) as status:
            # Prepare conversation history for the agent
            # The new prompt is designed to handle history, so we can pass it
            history_for_agent = "\n".join(
                [f"{m['role']}: {m['content']}" for m in st.session_state.messages]
            )
            
            # Run the unified agent
            status.update(label="Analyzing request and context...", state="running")
            response = agent.run(history_for_agent, stream=False)
            status.update(label="✅ Complete", state="complete", expanded=False)

        # Display the response content
        response_content = response.content
        response_placeholder.markdown(response_content)

    # Add agent's response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content,
        "data": {
            "agent": "UnifiedSupportAgent",
            "tools_used": response.run_details,
        }
    })

