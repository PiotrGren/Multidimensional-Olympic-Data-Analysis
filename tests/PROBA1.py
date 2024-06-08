import pyodbc

server = "localhost"
username = "sa"
password = "Passwd1234"
driver = "{ODBC Driver 17 for SQL Server}"

conn_str = f"DRIVER={driver};SERVER={server};DATABASE=master;UID={username};PWD={password}"

try:
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True

    print("POPRAWNIE UDAŁO SIĘ POŁACZYĆ Z BAZĄ")

except Exception as e:
    print(f"\nWYSTĄPIŁ BŁĄD:\n\n{e}")

finally:
    conn.close()

print("NIE WIEM")