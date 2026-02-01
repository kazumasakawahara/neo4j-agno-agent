import os
import json
import sys
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from agno.agent import Agent
from agno.tools import Toolkit
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class Neo4jToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="neo4j_toolkit")
        
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, user, password]):
            # Fallback or error logging
            print("❌ Neo4j connection details missing in .env")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.register(self.run_cypher_query)
        self.register(self.search_emergency_info)
        self.register(self.check_renewal_dates)
        self.register(self.get_client_profile)
        self.register(self.list_clients)
        # self.register(self.register_knowledge) # Complex object handling might need wrapper

    def run_cypher_query(self, cypher: str) -> str:
        """
        Executes a Cypher query against the Neo4j database.
        Use this to search, verify data, or retrieve specific information not covered by other tools.
        
        Args:
            cypher: Valid Cypher query string.
            
        Returns:
            JSON string of results.
        """
        try:
            with self.driver.session() as session:
                result = session.run(cypher)
                data = [record.data() for record in result]
                if not data:
                    return "Search results: 0 records"
                return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            return f"Cypher Execution Error: {e}"

    def search_emergency_info(self, client_name: str, situation: str = "") -> str:
        """
        [EMERGENCY ONLY] Retrieves safety-critical information with priority sorting.
        Follows 'Safety First' protocol:
        1. NgAction (Contraindications) - TOP PRIORITY
        2. CarePreference (Recommended Actions)
        3. KeyPerson (Emergency Contacts)
        4. Hospital
        5. Guardian
        
        Args:
            client_name: Name of the client (partial match allowed).
            situation: Optional context keyword (e.g., 'panic', 'meal').
            
        Returns:
            JSON string of emergency info.
        """
        try:
            # Reusing the optimized query from server.py logic
            query = """
            MATCH (c:Client)
            WHERE c.name CONTAINS $name
            OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
            WHERE $situation = '' OR ng.action CONTAINS $situation
            OPTIONAL MATCH (ng)-[:IN_CONTEXT]->(ngCon:Condition)
            WITH c, collect(DISTINCT {
                action: ng.action,
                reason: ng.reason,
                riskLevel: ng.riskLevel,
                context: ngCon.name
            }) AS ngActions

            OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
            WHERE $situation = '' OR cp.category CONTAINS $situation
            OPTIONAL MATCH (cp)-[:ADDRESSES]->(cpCon:Condition)
            WITH c, ngActions, collect(DISTINCT {
                category: cp.category,
                instruction: cp.instruction,
                priority: cp.priority,
                forCondition: cpCon.name
            }) AS carePrefs

            OPTIONAL MATCH (c)-[kpRel:HAS_KEY_PERSON]->(kp:KeyPerson)
            WITH c, ngActions, carePrefs, collect(DISTINCT {
                rank: kpRel.rank,
                name: kp.name,
                relationship: kp.relationship,
                phone: kp.phone,
                role: kp.role
            }) AS keyPersons

            OPTIONAL MATCH (c)-[:TREATED_AT]->(h:Hospital)
            WITH c, ngActions, carePrefs, keyPersons, collect(DISTINCT {
                name: h.name,
                specialty: h.specialty,
                phone: h.phone,
                doctor: h.doctor
            }) AS hospitals

            OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)

            RETURN
                c.name AS client,
                c.dob AS dob,
                c.bloodType AS bloodType,
                ngActions AS forbidden_actions,
                carePrefs AS recommended_care,
                keyPersons AS emergency_contacts,
                hospitals AS hospitals,
                collect(DISTINCT {
                    name: g.name,
                    type: g.type,
                    phone: g.phone
                }) AS legal_guardians
            """
            
            with self.driver.session() as session:
                result = session.run(query, name=client_name, situation=situation)
                data = [record.data() for record in result]
                
                if not data or not data[0].get('client'):
                    return f"Client '{client_name}' not found."
                
                return json.dumps(data[0], ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            return f"Error in search_emergency_info: {e}"

    def check_renewal_dates(self, days_ahead: int = 90, client_name: str = "") -> str:
        """
        Checks for certificates (Disability handbook, beneficiary certs) expiring soon.
        
        Args:
            days_ahead: Number of days to check ahead (default 90).
            client_name: Optional client name filter.
            
        Returns:
            JSON list of expiring certificates.
        """
        try:
            query = """
            MATCH (c:Client)-[:HAS_CERTIFICATE]->(cert:Certificate)
            WHERE cert.nextRenewalDate IS NOT NULL
              AND ($client_name = '' OR c.name CONTAINS $client_name)
            WITH c, cert,
                 duration.inDays(date(), cert.nextRenewalDate).days AS daysUntilRenewal
            WHERE daysUntilRenewal <= $days AND daysUntilRenewal >= 0
            RETURN
                c.name AS client,
                cert.type AS certificate_type,
                cert.grade AS grade,
                cert.nextRenewalDate AS renewal_date,
                daysUntilRenewal AS days_remaining
            ORDER BY daysUntilRenewal ASC
            """
            
            with self.driver.session() as session:
                result = session.run(query, days=days_ahead, client_name=client_name)
                data = [record.data() for record in result]
                
                if not data:
                    return f"No certificates expiring within {days_ahead} days."
                    
                return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            return f"Error in check_renewal_dates: {e}"

    def get_client_profile(self, client_name: str) -> str:
        """
        Retrieves the full profile of a client covering all 4 Pillars.
        
        Args:
            client_name: Name of the client.
            
        Returns:
            JSON object of the full profile.
        """
        try:
            # Simplified query for brevity, similar to server.py logic
            query = """
            MATCH (c:Client)
            WHERE c.name CONTAINS $name
            OPTIONAL MATCH (c)-[:HAS_HISTORY]->(h:LifeHistory)
            OPTIONAL MATCH (c)-[:HAS_WISH]->(w:Wish)
            OPTIONAL MATCH (c)-[:HAS_CONDITION]->(con:Condition)
            OPTIONAL MATCH (c)-[:REQUIRES]->(cp:CarePreference)
            OPTIONAL MATCH (c)-[:MUST_AVOID]->(ng:NgAction)
            OPTIONAL MATCH (c)-[:HAS_CERTIFICATE]->(cert:Certificate)
            OPTIONAL MATCH (c)-[:RECEIVES]->(pa:PublicAssistance)
            OPTIONAL MATCH (c)-[:HAS_KEY_PERSON]->(kp:KeyPerson)
            OPTIONAL MATCH (c)-[:HAS_LEGAL_REP]->(g:Guardian)
            OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(s:Supporter)
            OPTIONAL MATCH (c)-[:TREATED_AT]->(hosp:Hospital)
            
            RETURN 
                c.name AS name,
                c.dob AS dob,
                collect(DISTINCT h) AS history,
                collect(DISTINCT w) AS wishes,
                collect(DISTINCT con) AS conditions,
                collect(DISTINCT cp) AS care_preferences,
                collect(DISTINCT ng) AS ng_actions,
                collect(DISTINCT cert) AS certificates,
                collect(DISTINCT kp) AS key_persons,
                collect(DISTINCT g) AS guardians,
                collect(DISTINCT hosp) AS hospitals
            """
            
            with self.driver.session() as session:
                result = session.run(query, name=client_name)
                data = [record.data() for record in result]
                if not data or not data[0].get('name'):
                    return f"Client '{client_name}' not found."
                return json.dumps(data[0], ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            return f"Error in get_client_profile: {e}"

    def list_clients(self) -> str:
        """
        Lists all registered clients.
        
        Returns:
            JSON list of client names and basic info.
        """
        try:
            query = "MATCH (c:Client) RETURN c.name as name, c.dob as dob ORDER BY c.name"
            with self.driver.session() as session:
                result = session.run(query)
                data = [record.data() for record in result]
                return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            return f"Error listing clients: {e}"
