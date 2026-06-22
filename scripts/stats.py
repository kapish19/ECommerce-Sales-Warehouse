import psycopg2
import json
import pandas as pd
import re

# Database connection configuration
CONFIG_FILE = "config/db_config.json"
QUERIES_FILE = "sql/queries.sql"

# Load database configuration
def load_db_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Config file {CONFIG_FILE} not found.")
        exit(1)

DB_CONFIG = load_db_config()

# Function to read and parse SQL queries from file
def load_queries():
    queries = {}
    try:
        with open(QUERIES_FILE, "r") as f:
            sql_content = f.read()

        # Splitting queries using the comments as titles
        query_blocks = re.split(r'-- Question: (.+)', sql_content)[1:]

        for i in range(0, len(query_blocks), 2):
            title = query_blocks[i].strip()
            query = query_blocks[i + 1].strip()
            queries[title] = query

    except FileNotFoundError:
        print(f"ERROR: Queries file {QUERIES_FILE} not found.")
        exit(1)

    return queries

# Load SQL queries
queries = load_queries()

# Execute Queries and Display Results
def run_queries():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        for title, query in queries.items():
            print(f"\n Running Query: {title}")
            cur.execute(query)
            rows = cur.fetchall()

            # Convert to Pandas DataFrame for better display
            colnames = [desc[0] for desc in cur.description]
            df = pd.DataFrame(rows, columns=colnames)

            # Display dataframe
            print(df)

        cur.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_queries()