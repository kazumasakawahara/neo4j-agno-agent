import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def setup_vector_index():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    index_name = "support_log_vector_index"
    dimension = 768 # Text Embedding 004
    similarity_function = "cosine"
    
    query_check = "SHOW INDEXES YIELD name WHERE name = $name"
    
    query_create = f"""
    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (n:SupportLog)
    ON (n.embedding)
    OPTIONS {{indexConfig: {{
      `vector.dimensions`: {dimension},
      `vector.similarity_function`: '{similarity_function}'
    }}}}
    """
    
    print(f"🔌 Connecting to Neo4j at {NEO4J_URI}...")
    
    try:
        with driver.session() as session:
            # Check if exists
            result = session.run(query_check, name=index_name)
            if result.single():
                print(f"✅ Index '{index_name}' already exists.")
            else:
                print(f"🔨 Creating Vector Index '{index_name}'...")
                session.run(query_create)
                print(f"✅ Index '{index_name}' created successfully!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    setup_vector_index()
