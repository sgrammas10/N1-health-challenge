import sqlite3


DB_PATH = "n1_data_ops_challenge.db"

ROSTERS = ["roster_1", "roster_2", "roster_3", "roster_4", "roster_5"]

def run(conn, sql):
    return conn.execute(sql).fetchall()

def basic_column_profile(conn, table, col):
    print(f"\n--- {table}.{col} ---")

    #what storage types are there
    print("types:", run(conn, f"""
        SELECT typeof({col}), COUNT(*) FROM {table}
        GROUP BY typeof({col})
    """))    

    #how many nulls / blanks are there
    print("nulls / blanks:", run(conn, f"""
        SELECT SUM({col} IS NULL),
               SUM(TRIM({col}) = '')
        FROM {table}
    """))

    #what are the lengths of the values
    print("lengths:", run(conn, f"""
        SELECT LENGTH({col}) AS len, COUNT(*) FROM {table}
        GROUP BY len ORDER BY COUNT(*) DESC LIMIT 10
    """))

    #examples of the values
    print("samples:", run(conn, f"""
        SELECT DISTINCT {col} FROM {table} LIMIT 5
    """))

conn = sqlite3.connect(DB_PATH)
for table in ROSTERS:
    basic_column_profile(conn, table, "DoB")