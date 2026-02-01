import json
from datetime import datetime, timedelta
from agno.tools import Toolkit
from lib.db_operations import resolve_client, run_query

class CareToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="care_toolkit")
        self.register(self.analyze_feedback)

    def analyze_feedback(self, client_name: str, days_lookback: int = 30) -> str:
        """
        Analyze recent support logs to discover effective care strategies ('Excellent' or 'Good' outcomes)
        and suggest new CarePreferences.
        
        Args:
            client_name: Name of the client.
            days_lookback: How many days back to analyze (default 30).
        """
        client = resolve_client(client_name)
        if not client:
            return "Client not found."

        name = client.get('name')
        start_date = (datetime.now() - timedelta(days=days_lookback)).strftime("%Y-%m-%d")
        
        query = """
        MATCH (s:Supporter)-[:LOGGED]->(log:SupportLog)-[:ABOUT]->(c:Client)
        WHERE (c.name = $name OR c.clientId = $name)
          AND log.date >= date($start_date)
          AND (log.effectiveness CONTAINS 'Excellent' OR log.effectiveness CONTAINS 'Good' OR log.effectiveness CONTAINS '◎' OR log.effectiveness CONTAINS '○')
        RETURN 
            log.situation AS situation,
            log.action AS action,
            log.effectiveness AS effectiveness,
            s.name AS supporter
        ORDER BY log.date DESC
        """
        logs = run_query(query, {"name": name, "start_date": start_date})
        
        if not logs:
            return "No high-effectiveness logs found in the period."
            
        suggestions = []
        for log in logs:
            suggestions.append({
                "instruction": f"When {log['situation']}, try: {log['action']}",
                "reason": f"Proven effective by {log['supporter']} (Effect: {log['effectiveness']})"
            })
            
        return json.dumps({
            "client": name,
            "found_logs": len(logs),
            "suggestions": suggestions
        }, ensure_ascii=False, indent=2)
