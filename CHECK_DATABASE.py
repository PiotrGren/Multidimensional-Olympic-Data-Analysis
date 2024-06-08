import pyodbc
from sqlalchemy import create_engine, inspect

def check_database_exists(database_name, server='localhost', username='sa', password='Passwd1234', driver='{ODBC Driver 17 for SQL Server}'):
    
    conn_str = f'DRIVER={driver};SERVER={server};DATABASE=master;UID={username};PWD={password}'

    try:
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        
        cursor = conn.cursor()
        
        check_db_query = f"SELECT name FROM sys.databases WHERE name = '{database_name}'"
        
        cursor.execute(check_db_query)

        result = cursor.fetchone()
        if result:
            print(f"\nBaza danych {database_name} istnieje wśród baz danych serwera\n")
        else:
            print(f"\nBaza danych {database_name} nie istnieje wśród baz danych serwera\n")
        


        list_db_query = "SELECT name FROM sys.databases"
        
        cursor.execute(list_db_query)
        
        databases = cursor.fetchall()

        print("Istniejące bazy danych:")
        for db in databases:
            print(db[0])

    except Exception as e:
        print(f"Wystąpił błąd podczas sprawdzania bazy danych: {str(e)}")

    finally:
        cursor.close()
        conn.close()

def list_tables_and_show_data(database_name, server="localhost", username='sa', password='Passwd1234', driver="ODBC Driver 17 for SQL Server"):
    try:
        engine = create_engine(f'mssql+pyodbc://{username}:{password}@{server}/{database_name}?driver={driver}')
    except Exception as e:
        print("Podana baza danych nie istnieje")
        return None

    # Tworzenie inspektora bazy danych
    inspector = inspect(engine)

    # Pobieranie listy tabel
    tables = inspector.get_table_names()
    print(f"Istniejące tabele w bazie danych {database_name}: {tables}")

check_database_exists("OLYMPICS")
list_tables_and_show_data("OLYMPICS")
