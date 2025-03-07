import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")  
password = os.getenv("NEO4J_PASSWORD") 

driver = GraphDatabase.driver(uri, auth=(username, password))

def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            print(record)

query = """
MATCH (n:Concept)
WHERE n.name CONTAINS 'heart disease' OR n.id IN ['C0018799', 'C0018800', 'C0018811']
RETURN n
LIMIT 10
"""
run_query(query)
