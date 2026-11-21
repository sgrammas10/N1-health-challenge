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

def main():
    conn = sqlite3.connect(DB_PATH)
    create_stacked_view(conn)
    build_std_member_info(conn)