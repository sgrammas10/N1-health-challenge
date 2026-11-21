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

def convert_date_format(col, table):
    if table == "roster_2":
        return f"substr({col},7,4) || '-' || substr({col}, 1,2) || '-' || substr({col}, 4,2)"
    return col

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
# for table in ROSTERS:
#     print(f"\n--- {table}.Person_Id ---")
#     print(run(conn, f"""
#         SELECT COUNT(*) AS total_rows,
#                 COUNT(DISTINCT Person_Id) AS distinct_ids
#         FROM {table}
#     """))
#     print("samples:", run(conn, f"SELECT Person_Id FROM {table} LIMIT 5"))

# for table in ROSTERS:
#     basic_column_profile(conn, table, "Person_Id")


stacked = " UNION ALL ".join(
    f"SELECT Person_Id, '{t}' AS roster FROM {t}" for t in ROSTERS
)

#how many rosters does each id appear in
# print("\n--- Person_Id roster counts ---")
# print(run(conn, f"""
#     SELECT n_rosters, COUNT(*) AS n_ids
#     FROM (SELECT Person_id, COUNT(*) AS n_rosters
#           FROM ({stacked})
#           GROUP BY Person_id)
#     GROUP BY n_rosters
#     ORDER BY n_rosters
# """))

parts = []
for t in ROSTERS:
    parts.append(f"""
    SELECT '{t}' AS roster, Person_Id, First_name, Last_name, 
    {convert_date_format('DoB', t)} AS DoB,
    Street_Address, City, State, Zip, payer,
    {convert_date_format('eligibility_start_date', t)} AS eligibility_start_date,
    {convert_date_format('eligibility_end_date', t)} AS eligibility_end_date
    FROM {t}""")
conn.execute("DROP VIEW IF EXISTS stacked")
conn.execute("CREATE TEMP VIEW stacked AS " + " UNION ALL ".join(parts))

#pair up rows of duplicate ids count differences
# print("\n--- duplicate pairs---")
# print("(roster_a, roster_b, pairs, first, last, dob, address, zip, payer, start, end)")
# for row in run(conn, """
#     SELECT a.roster, b.roster, COUNT(*) AS pairs,
#     SUM(a.First_name != b.First_name),
#     SUM(a.Last_name != b.Last_name),
#     SUM(a.DoB != b.DoB),
#     SUM(a.Street_Address != b.Street_Address),
#     SUM(a.Zip != b.Zip),
#     SUM(a.payer != b.payer),
#     SUM(a.eligibility_start_date != b.eligibility_start_date),
#     SUM(a.eligibility_end_date != b.eligibility_end_date)
#     FROM stacked a
#     JOIN stacked b ON a.Person_Id = b.Person_Id AND a.roster < b.roster
#     GROUP BY a.roster, b.roster
#     ORDER BY pairs DESC"""
#     ):
#     print(row)

#see a few pairs side by side
# print("\n --- sample duplicate pairs --- ")
# for row in run(conn,"""
#     SELECT a.Person_Id, a.roster, a.payer, a.eligibility_start_date, a.eligibility_end_date,
#     b.roster, b.payer, b.eligibility_start_date, b.eligibility_end_date
#     FROM stacked a
#     JOIN stacked b ON a.Person_Id = b.Person_Id AND a.roster < b.roster
#     LIMIT 10


# """):
#     print(row)

print("\n--- payer values by roster ---")
for row in run(conn, """
    SELECT roster, payer, COUNT(*) AS n
    FROM stacked
    GROUP BY roster, payer
    ORDER BY roster, n DESC
"""):
    print(row)  

print("\n--- State values ---")
print(run(conn, """
    SELECT State, COUNT(*) FROM stacked
    GROUP BY State ORDER BY COUNT(*) DESC
"""))

print("\n--- Zip types and lengths by roster ---")
for row in run(conn, """
    SELECT roster, typeof(Zip), LENGTH(Zip), COUNT(*)
    FROM stacked
    GROUP BY roster, typeof(Zip), LENGTH(Zip)
"""):
    print(row)

print("\n--- Zip samples ---")
print(run(conn, "SELECT DISTINCT Zip FROM stacked LIMIT 15"))


print("\n--- zcta in scores table ---")
print(run(conn, """
    SELECT typeof(zcta), COUNT(*), COUNT(DISTINCT zcta)
    FROM model_scores_by_zip
    GROUP BY typeof(zcta)
"""))

print("\n--- member zip match rate ---")
print(run(conn, """
    SELECT COUNT(*) AS member_rows,
            SUM(m.zcta IS NOT NULL) AS matched,
            SUM(m.zcta IS NULL)     AS unmatched
    FROM stacked s
    LEFT JOIN model_scores_by_zip m
        ON CAST(s.Zip AS INTEGER) = m.zcta
"""))


print(run(conn, """
    SELECT SUM(food_access_score IS NULL),
           SUM(social_isolation_score IS NULL),
           SUM(algorex_sdoh_composite_score IS NULL),
           MIN(food_access_score), MAX(food_access_score),
           MIN(algorex_sdoh_composite_score), MAX(algorex_sdoh_composite_score)
    FROM model_scores_by_zip
"""))