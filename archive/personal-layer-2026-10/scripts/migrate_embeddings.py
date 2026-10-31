import os
import google.generativeai as genai
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Config
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def get_embedding(text):
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY missing.")
        return None
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document" # Document for storage
        )
        return result['embedding']
    except Exception as e:
        print(f"❌ Embedding Error: {e}")
        return None

def migrate_embeddings():
    print("🚀 Starting Embedding Migration...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    fetch_query = """
    MATCH (log:SupportLog)
    WHERE log.embedding IS NULL
    RETURN log.id as id, log.situation as situation, log.action as action, log.effectiveness as effect
    """
    
    update_query = """
    MATCH (log:SupportLog {id: $id})
    CALL db.create.setVectorProperty(log, 'embedding', $embedding)
    YIELD node
    RETURN count(node)
    """
    
    with driver.session() as session:
        logs = list(session.run(fetch_query))
        print(f"📊 Found {len(logs)} logs without embeddings.")
        
        for log in logs:
            # Combine text for context
            text = f"Situation: {log['situation']}\nAction: {log['action']}\nEffectiveness: {log['effect']}"
            
            print(f"   🔹 Processing Log {log['id']}...", end=" ")
            embedding = get_embedding(text)
            
            if embedding:
                session.run(update_query, id=log['id'], embedding=embedding)
                print("✅ Saved.")
            else:
                print("Skipped.")
                
    driver.close()
    print("✨ Migration Complete.")

if __name__ == "__main__":
    migrate_embeddings()
