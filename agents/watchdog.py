import re
from agents.base import BaseSupportAgent
from tools.neo4j_toolkit import Neo4jToolkit
from tools.sos_toolkit import SOSToolkit

class EmergencyWatchdog(BaseSupportAgent):
    def __init__(self):
        super().__init__(
            name="EmergencyWatchdog",
            instructions=[
                "ROLE: SOS Monitor & Override",
                "GOAL: Detect emergencies instantly and trigger the Fast-path.",
                "DUTIES:",
                "1. Monitor all inputs for keywords like 'SOS', 'Emergency', 'Hospitalized', 'Panic'.",
                "2. If detected, BYPASS complex reasoning.",
                "3. IMMEIDATELY output a prioritized list of contacts and NgActions.",
                "4. Use the 'analyze_sos_context' tool to determine if it is Medical or Behavioral.",
                "5. Use the 'search_emergency_info' tool from Neo4jToolkit for detailed profiling."
            ],
            tools=[Neo4jToolkit(), SOSToolkit()]
        )

    def check_fast_path(self, text: str) -> bool:
        """
        Regex-based fast check.
        Returns True if SOS/Emergency keywords are found.
        """
        sos_keywords = r"(SOS|緊急(?!連絡先)|助けて|倒れた|入院|事故|パニック|救急車)"
        if re.search(sos_keywords, text, re.IGNORECASE):
            self.log_reasoning(f"FAST-PATH TRIGGERED: Keyword match in '{text}'")
            return True
        return False
