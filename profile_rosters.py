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

def date_format_profile(conn, table, col):
    print(f"\n--- {table}.{col} ---")
    print(run(conn, f"""
        SELECT CASE
                 WHEN {col} IS NULL OR TRIM({col}) = '' THEN 'missing'
                 WHEN substr({col}, 5, 1) = '-'         THEN 'YYYY-MM-DD'
                 WHEN substr({col}, 3, 1) = '/'         THEN 'XX/XX/YYYY'
                 ELSE 'other'
               END AS fmt,
               COUNT(*)
        FROM {table}
        GROUP BY fmt
    """))

conn = sqlite3.connect(DB_PATH)
# for table in ROSTERS:
#     basic_column_profile(conn, table, "DoB")

# DATE_COLS = ["DoB", "eligibility_start_date", "eligibility_end_date"]
# for col in DATE_COLS:
#     for table in ROSTERS:
#         date_format_profile(conn, table, col)

#quick check for roster 2 data
# for col in ["Dob", "eligibility_start_date", "eligibility_end_date"]:
#     print(f"\n--- roster_2.{col} ---")
#     print(run(conn, f"SELECT DISTINCT {col} FROM roster_2 LIMIT 50"))



# Is Person_Id unique within each roster?
for table in ROSTERS:
    print(f"\n--- {table}.Person_Id ---")
    print(run(conn, f"""
        SELECT COUNT(*) AS total_rows,
                COUNT(DISTINCT Person_Id) AS distinct_ids
        FROM {table}
    """))
    print("samples:", run(conn, f"SELECT Person_Id FROM {table} LIMIT 5"))

for table in ROSTERS:
    basic_column_profile(conn, table, "Person_Id")