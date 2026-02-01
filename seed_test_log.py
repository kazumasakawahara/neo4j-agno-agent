
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.db_operations import run_query

def seed_log():
    client_name = "山田健太"
    print(f"Seeding 'Excellent' log for {client_name}...")
    
    query = """
    MATCH (c:Client {name: $name})
    MATCH (s:Supporter) 
    WITH c, s LIMIT 1
    CREATE (log:SupportLog {
        date: date(),
        situation: 'Panicked at supermarket',
        action: 'Used noise-canceling headphones immediately',
        effectiveness: 'Excellent (◎)',
        note: 'Very effective, calmed down in 1 min.',
        createdAt: datetime()
    })
    CREATE (s)-[:LOGGED]->(log)-[:ABOUT]->(c)
    RETURN log
    """
    
    result = run_query(query, {"name": client_name})
    print("Seeded:", result)

if __name__ == "__main__":
    seed_log()
