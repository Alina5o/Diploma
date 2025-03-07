import csv
from argparse import ArgumentParser

import pymysql
from tqdm import tqdm


def process_concepts(cursor):
    """Extract concepts from mrconso table and save them as CSV."""
    print("Processing Concepts...")
    cursor.execute("SELECT * FROM mrconso")
    mrconso = cursor.fetchall()

    exists_concept = set()
    concept_file = 'MRCONSO.processed.csv'
    with open(concept_file, 'w', encoding='utf-8', newline='') as out_concept:
        writer = csv.writer(out_concept)
        writer.writerow(['CUI:ID', 'LABEL', 'name'])

        for line in tqdm(mrconso, desc="Concepts", unit="record"):
            if line[0] in exists_concept:
                continue
            if line[1] == 'ENG':
                writer.writerow([line[0], 'Concept', line[-4]])
                exists_concept.add(line[0])

    print(f"{len(exists_concept)} concepts written to {concept_file}")
    return exists_concept


def process_atoms(cursor):
    """Extract atoms from mrconso table and save them as CSV."""
    print("Processing Atoms...")
    cursor.execute("SELECT * FROM mrconso")
    mrconso = cursor.fetchall()

    exists_atom = set()
    atom_file = 'MRAUI.processed.csv'
    with open(atom_file, 'w', encoding='utf-8', newline='') as out_atom:
        writer = csv.writer(out_atom)
        writer.writerow(['AUI:ID', 'LABEL', 'name', 'CUI'])

        for line in tqdm(mrconso, desc="Atoms", unit="record"):
            if line[7] in exists_atom:
                continue
            if line[1] == 'ENG':
                writer.writerow([line[7], 'Atom', line[-4], line[0]])
                exists_atom.add(line[7])

    print(f"{len(exists_atom)} atoms written to {atom_file}")
    return exists_atom


def process_relationships(cursor, valid_ids, chunk_size=100000):
    """Extract relationships from mrrel table and save them as CSV in chunks."""
    print("Processing Relationships...")

    relationship_file = 'MRREL.processed.csv'
    count = 0

    with open(relationship_file, 'w', encoding='utf-8', newline='') as out_rel:
        writer = csv.writer(out_rel)
        writer.writerow(['START_ID', 'END_ID', 'TYPE', 'RELA'])

        cursor.execute("SELECT COUNT(*) FROM mrrel")
        total_rows = cursor.fetchone()[0]

        for offset in tqdm(range(0, total_rows, chunk_size), desc="Relationships", unit="record"):
            cursor.execute(f"SELECT * FROM mrrel LIMIT {chunk_size} OFFSET {offset}")
            mrrel_chunk = cursor.fetchall()

            for line in mrrel_chunk:
                start_node = line[4]
                end_node = line[0]

                if line[6] == 'AUI':  # style 2
                    start_node = line[5]
                if line[2] == 'AUI':  # style 1
                    end_node = line[1]

                if start_node in valid_ids and end_node in valid_ids:
                    writer.writerow([start_node, end_node, line[3], line[7]])
                    count += 1

    print(f"{count} relationships processed and written to {relationship_file}")


def main():
    parser = ArgumentParser()
    parser.add_argument('--host', default='localhost', type=str)
    parser.add_argument('--user', required=True, type=str)
    parser.add_argument('--password', required=True, type=str)
    parser.add_argument('--database', required=True, type=str, default='umls')
    args = parser.parse_args()

    try:
        conn = pymysql.connect(
            host=args.host,
            user=args.user,
            password=args.password,
            database=args.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )
    except pymysql.MySQLError as e:
        raise RuntimeError(f"Error connecting to the database: {e}")

    with conn:
        with conn.cursor() as cursor:
            concepts = process_concepts(cursor)
            atoms = process_atoms(cursor)
            valid_ids = concepts | atoms
            process_relationships(cursor, valid_ids)


if __name__ == '__main__':
    main()

#python build_graph1.py --host localhost --user root --password 515668 --database umls

# CONCEPTS
# LOAD CSV WITH HEADERS FROM 'file:///concepts.csv' AS row
# CREATE (:Concept {id: CUI:ID, name: row.name});

# ATOMS
# LOAD CSV WITH HEADERS FROM 'file:///atoms.csv' AS row
# CREATE (:Atom {id: row.`AUI:ID`, name: row.name, cui: row.CUI});

# CALL apoc.load.json("file:///atoms.json.gz", "", {compression: "GZIP"}) YIELD value AS row
# CREATE (:Atom {id: row.`AUI:ID`, name: row.name, cui: row.CUI});

# CALL apoc.periodic.iterate(
#   "CALL apoc.load.json('file:///atoms.json.gz', '', {compression: 'GZIP'}) YIELD value AS row",
#   "CREATE (:Atom {id: row.`AUI:ID`, name: row.name, cui: row.CUI})",
#   {batchSize: 1000, parallel: true}
# );

# RELA
# LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
# MATCH (a1:Atom {id: row.":START_ID"})
# MATCH (a2:Atom {id: row.":END_ID"})
# CREATE (a1)-[:`{row.RELA}`]->(a2);


# CALL apoc.periodic.iterate(
#   "CALL apoc.load.json('file:///relationships.json.gz', '', {compression: 'GZIP'}) YIELD value AS row",
#   "MATCH (a1:Atom {id: row.\":START_ID\"})
#    MATCH (a2:Atom {id: row.\":END_ID\"})
#    CREATE (a1)-[r:RELATIONSHIP {type: row.RELA}]->(a2)",
#   {batchSize: 1000, parallel: true}
# );
