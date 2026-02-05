from agno.agent import Agent
from agno.models.google import Gemini
import os

class DistributorAgent(Agent):
    def __init__(self):
        # Read the router configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "router_config.md")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                router_config = f.read()
        except FileNotFoundError:
            router_config = "No config found. Default: Panic -> CLINICAL."

        super().__init__(
            model=Gemini(id="gemini-2.0-flash-exp"),
            description="You are the Central Dispatcher (Distributor) for the Post-Parent Support System.",
            instructions=[
                "ROLE: Route the user's input to the most appropriate agent based on the [Router Config].",
                f"--- ROUTER CONFIG ---\n{router_config}\n---------------------",
                "AGENTS:",
                "1. WATCHDOG: Immediate life threats only.",
                "2. CLINICAL: Behavioral issues (Panic, Refusal, etc.).",
                "3. SUPPORT: General inquiries, logging, planning, contact scraping.",
                "TASK:",
                "Analyze the input and output a JSON object indicating the target agent.",
                "FORMAT: {'target_agent': 'WATCHDOG' | 'CLINICAL' | 'SUPPORT', 'reason': 'Brief reason'}",
                "OUTPUT JSON ONLY. No markdown blocks."
            ],
            markdown=False
        )
