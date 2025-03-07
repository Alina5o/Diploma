
import argparse
import os
import math
from neo4j import GraphDatabase
from utils.tools import *

# Function to load concepts without splitting the CSV
def load_concepts(driver, filepath):
    query = f"""
    LOAD CSV WITH HEADERS FROM 'file:///{filepath}' AS row
    CREATE (:Concept {{id: row.`CUI:ID`, name: row.name}});
    """
    with driver.session() as session:
        session.run(query)
    print(f"Concepts loaded from {filepath}")

# Function to load atoms, splitting the CSV into 3 parts
def load_atoms(driver, filepath):
    # Split the CSV into 3 parts
    num_parts = 3
    split_csv(filepath, num_parts)

    # Cypher query for loading atoms
    query = """
    LOAD CSV WITH HEADERS FROM 'file:///{filepath}' AS row
    CREATE (:Atom {{id: row.`AUI:ID`, name: row.name, cui: row.CUI}});
    CREATE INDEX FOR (a:Atom) ON (a.id);
    CREATE INDEX FOR (c:Concept) ON (c.id);
    """
    
    for i in range(1, num_parts + 1):
        part_filepath = f"part_{i}.csv"
        part_query = query.format(filepath=part_filepath)
        with driver.session() as session:
            session.run(part_query)
        print(f"Atoms loaded from {part_filepath}")

# Function to load relationships, splitting the CSV into 12 parts
def load_relationships(driver, filepath):
    num_parts = 12
    split_csv(filepath, num_parts)

    # Cypher query for loading relationships
    query = """
    LOAD CSV WITH HEADERS FROM 'file:///{filepath}' AS row
    WITH row
    WHERE row.RELA IS NOT NULL AND trim(row.RELA) <> ''
    MATCH (concept1:Concept {{id: row.START_ID}})
    MATCH (concept2:Concept {{id: row.END_ID}})
    CALL apoc.create.relationship(concept1, row.TYPE, {{name: row.RELA}}, concept2) YIELD rel
    RETURN count(rel) AS relationships_created;
    """

    for i in range(1, num_parts + 1):
        part_filepath = f"part_{i}.csv"
        part_query = query.format(filepath=part_filepath)
        with driver.session() as session:
            session.run(part_query)
        print(f"Relationships loaded from {part_filepath}")

# Function to split the CSV into parts
def split_csv(filepath, num_parts):
    import pandas as pd
    
    df = pd.read_csv(filepath)
    total_rows = len(df)
    rows_per_part = math.ceil(total_rows / num_parts)

    # Directory of the original file
    dir_path, filename = os.path.split(filepath)
    file_name, ext = os.path.splitext(filename)

    for i in range(num_parts):
        start_row = i * rows_per_part
        end_row = min((i + 1) * rows_per_part, total_rows)
        part_df = df.iloc[start_row:end_row]
        part_filepath = os.path.join(dir_path, f"{file_name}_part_{i + 1}{ext}")
        part_df.to_csv(part_filepath, index=False)
        print(f"Created part file: {part_filepath}")

# Main function for creating a connection to Neo4j and running all operations
def main(args):
    driver = GraphDatabase.driver(args.uri, auth=(args.username, args.password))

    try:
        load_concepts(driver, args.concepts_file)
        load_atoms(driver, args.atoms_file)
        load_relationships(driver, args.relationships_file)
    finally:
        driver.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load CSV data into Neo4j")
    
    # Add arguments for the Neo4j connection
    parser.add_argument('--uri', type=str, default="bolt://localhost:7687", help="Neo4j connection URI (default: bolt://localhost:7687)")
    parser.add_argument('--username', type=str, default="neo4j", help="Neo4j username (default: neo4j)")
    parser.add_argument('--password', type=str, default="password", help="Neo4j password (default: password)")
    
    # Add arguments for the CSV files
    parser.add_argument('concepts_file', type=str, help='CSV file for concepts')
    parser.add_argument('atoms_file', type=str, help='CSV file for atoms')
    parser.add_argument('relationships_file', type=str, help='CSV file for relationships')
    
    args = parser.parse_args()
    
    main(args)
