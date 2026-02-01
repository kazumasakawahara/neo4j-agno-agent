from agents.base import BaseSupportAgent
from tools.neo4j_toolkit import Neo4jToolkit

class SupportAgent(BaseSupportAgent):
    def __init__(self):
        super().__init__(
            name="SupportAgent",
            instructions=[
                "ROLE: Knowledge Navigator & Alternative Planner (The 5th Pillar)",
                "GOAL: Explore the Knowledge Graph to find solutions when the primary caregiver is unavailable.",
                "DUTIES:",
                "1. Query Neo4j to understand the Client's profile (CarePreferences, NgActions, KeyPersons).",
                "2. When a problem arises (e.g., 'Mother is hospitalized'), formulate a Plan B.",
                "3. IDENTIFY RISKS: Check NgActions first.",
                "4. PROPOSE SOLUTIONS: Use CarePreferences and KeyPersons.",
                "5. SEEK APPROVAL: Before finalizing any action that affects the client, ask for user confirmation.",
            ],
            tools=[Neo4jToolkit()], 
            # human_in_the_loop=True inside flow not globally always? 
            # Agno `Agent` usually supports `add_history_to_messages` etc.
            # `human_input=True` might be supported in `run` or `console`.
            # We will handle approval in the loop instructions or via specific return requests.
        )
