import os
import json
import pandas as pd
import psycopg2
from psycopg2 import sql

# Constants
CONFIG_FILE = "config/db_config.json"
PROCESSED_DATA_PATH = "data/processed"
SCHEMA_SCRIPT_PATH = "sql/dw_schema.sql"
TABLES = {
    "category_dimension": "category_dimension.csv",
    "product_dimension": "product_dimension.csv",
    "user_dimension": "user_dimension.csv",
    "cart_dimension": "cart_dimension.csv",
    "sales_fact_table": "sales_fact_table.csv"
}

# Load database configuration
def load_db_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Config file {CONFIG_FILE} not found.")
        exit(1)

DB_CONFIG = load_db_config()

# Establish database connection
def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"ERROR: Unable to connect to the database - {e}")
        exit(1)

# Execute SQL script
def execute_sql_script(script_path):
    if not os.path.exists(script_path):
        print(f"ERROR: SQL script {script_path} not found.")
        return
    
    try:
        with open(script_path, 'r') as file:
            sql_script = file.read()
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_script)
                conn.commit()
        print(f"SQL script {script_path} executed successfully.")
    except Exception as e:
        print(f"ERROR executing {script_path}: {e}")

# Check if table exists
def table_exists(table_name):
    query = sql.SQL(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);"
    )
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (table_name,))
                return cur.fetchone()[0]
    except Exception as e:
        print(f"ERROR checking table {table_name}: {e}")
        return False

# Load CSV into PostgreSQL
def load_csv_to_postgres(table_name, csv_filename):
    csv_path = os.path.join(PROCESSED_DATA_PATH, csv_filename)
    if not os.path.exists(csv_path):
        print(f"ERROR: File {csv_path} not found.")
        return
    
    try:
        df = pd.read_csv(csv_path, parse_dates=["cart_date"] if table_name == "cart_dimension" else [])
        print(f"Loading {table_name} - Preview:\n", df.head())
    
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if table_exists(table_name):
                    print(f"Table {table_name} exists. Clearing data...")
                    cur.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(sql.Identifier(table_name)))
                
                with open(csv_path, 'r') as f:
                    cur.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER", f)
                conn.commit()
        
        print(f"{table_name} successfully loaded.")
    except Exception as e:
        print(f"ERROR loading {table_name}: {e}")

# Load all tables
def load_all_data():
    for table_name, csv_filename in TABLES.items():
        load_csv_to_postgres(table_name, csv_filename)

# Main function
def main():
    print("Starting schema creation process...")
    execute_sql_script(SCHEMA_SCRIPT_PATH)
    print("Starting database load process...")
    load_all_data()
    print("All CSVs successfully loaded into PostgreSQL.")

if __name__ == "__main__":
    main()