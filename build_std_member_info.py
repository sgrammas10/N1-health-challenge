import sqlite3

DB_PATH = "n1_data_ops_challenge.db"

ROSTERS = ["roster_1", "roster_2", "roster_3", "roster_4", "roster_5"]

ELIGIBILITY_YEAR = 2025 #assumption since data and challenge from 2025



def create_stacked_view(conn):
    """stack all rosters into one view and convert roster 2 dates to correct format(YYYY-MM-DD)"""
    def convert_date_format(col, table):
        if table == "roster_2":
            return f"substr({col},7,4) || '-' || substr({col}, 1,2) || '-' || substr({col}, 4,2)"
        return col

    
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

def build_std_member_info(conn):
    """combine, standardize, filter to eligibility year and dedupe into one row per member"""
    year_start = f"{ELIGIBILITY_YEAR}-01-01"
    year_end = f"{ELIGIBILITY_YEAR}-12-31"
    conn.execute("DROP TABLE IF EXISTS std_member_info")
    conn.execute(f"""  
        CREATE TABLE std_member_info AS
        SELECT DISTINCT
            Person_Id AS member_id,
            TRIM(First_Name) AS member_first_name,
            TRIM(Last_name) AS member_last_name,
            DoB AS date_of_birth,
            TRIM(Street_Address) AS main_address,
            TRIM(City) AS city,
            CASE WHEN State = 'California' THEN 'CA' ELSE State END AS state,
            Zip AS zip_code,
            payer,
            eligibility_start_date,
            eligibility_end_date
        FROM stacked
        WHERE eligibility_start_date <= '{year_end}'
          AND eligibility_end_date   >= '{year_start}'
    """)
    conn.commit()

def verify(conn):
    total, distinct = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT member_id) FROM std_member_info"
    ).fetchone()
    print(f"std_member_info: {total} rows, {distinct} distinct members")
    assert total == distinct, "More than one row per member"

def answer_questions(conn):
    q1 = conn.execute(f""" 
        SELECT COUNT(DISTINCT member_id)
        FROM std_member_info
        WHERE eligibility_start_date <= '2025-04-30'
            AND eligibility_end_date >= '2025-04-01'
    """).fetchone()[0]
    print(f"Q1. Members eligible in April 2025: {q1}")


    q2 = conn.execute(f""" 
        SELECT COUNT(*)
        FROM (SELECT Person_Id FROM stacked GROUP BY Person_Id HAVING COUNT(*) > 1)
    """).fetchone()[0]
    print(f"Q2. Members appearing in more than one roster: {q2}")

    print("Q3. Members by payer:")
    for payer, n, pct in conn.execute(""" 
        SELECT payer, COUNT(*) AS n, ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM std_member_info), 1) AS pct
        FROM std_member_info
        GROUP BY payer
        ORDER BY n DESC
    """):
        print(f"{payer}: {n} ({pct}%)")

    q4 = conn.execute(""" 
        SELECT COUNT(DISTINCT s.member_id)
        FROM std_member_info s
        JOIN model_scores_by_zip m ON CAST(s.zip_code AS INTEGER) = m.zcta
        WHERE m.food_access_score < 2
    """).fetchone()[0]
    print(f"Q4. Members in zips with food access score < 2: {q4}")

    q5 = conn.execute(""" 
        SELECT AVG(m.social_isolation_score)
        FROM std_member_info s
        JOIN model_scores_by_zip m ON CAST(s.zip_code AS INTEGER) = m.zcta
    """).fetchone()[0]
    print(f"Q5. Average social isolation score (across members): {q5:.2f}")

    print("Q6. Members in the highest-SDOH-composite zip:")
    rows = conn.execute(""" 
        SELECT s.member_id, s.member_first_name, s.member_last_name, s.zip_code, m.algorex_sdoh_composite_score
        FROM std_member_info s
        JOIN model_scores_by_zip m ON CAST(s.zip_code AS INTEGER) = m.zcta
        WHERE m.algorex_sdoh_composite_score = 
            (SELECT MAX(algorex_sdoh_composite_score) FROM model_scores_by_zip)
        ORDER BY s.member_last_name, s.member_first_name
    """).fetchall()

    print(f"{len(rows)} member(s)")
    for row in rows:
        print(f"    {row}")

def main():
    conn = sqlite3.connect(DB_PATH)
    create_stacked_view(conn)
    build_std_member_info(conn)
    verify(conn)
    answer_questions(conn)


    # min_end, max_start, boundary = conn.execute("""
    #     SELECT MIN(eligibility_end_date), MAX(eligibility_start_date),
    #         SUM(eligibility_end_date = '2025-01-01')
    #     FROM std_member_info
    # """).fetchone()
    # print(f"earliest end: {min_end}, latest start: {max_start}, boundary members: {boundary}")





if __name__ == "__main__":
    main()
    