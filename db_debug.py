import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

def describe_table(table_name):
    print(f"\n--- Table: {table_name} ---")
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table_name}'")
    for col, dtype in cur.fetchall():
        print(f"  {col}: {dtype}")

tables = ['entity_master', 'relation_master', 'assertions', 'quant_data', 'ontology_rules']
for t in tables:
    describe_table(t)

cur.close()
conn.close()
