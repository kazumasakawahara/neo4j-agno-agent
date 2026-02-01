from agents.base import BaseSupportAgent
from tools.neo4j_toolkit import Neo4jToolkit
from tools.resilience_toolkit import ResilienceToolkit
from tools.care_toolkit import CareToolkit
from tools.report_toolkit import ReportToolkit

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
                "--- SKILLS ---",
                "- Use `analyze_transition_impact` to assess risks when a key person is unavailable.",
                "- Use `suggest_alternatives` to find backup services.",
                "- Use `analyze_feedback` to find CarePreferences that have worked in the past.",
                "- Use `generate_excel_report` if the user asks for a file export."
            ],
            tools=[Neo4jToolkit(), ResilienceToolkit(), CareToolkit(), ReportToolkit()], 
        )
