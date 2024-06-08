import pyodbc

def create_database(database_name, server='localhost', username='sa', password='Passwd1234', driver='{ODBC Driver 17 for SQL Server}'):
    
    conn_str = f'DRIVER={driver};SERVER={server};DATABASE=master;UID={username};PWD={password}'

    try:
        # Nawiązanie połączenia
        conn = pyodbc.connect(conn_str)
        conn.autocommit = True
        
        # Utworzenie kursora
        cursor = conn.cursor()
        
        # Polecenie SQL CREATE DATABASE
        create_db_query = f"CREATE DATABASE {database_name}"
        
        # Wykonanie polecenia
        cursor.execute(create_db_query)
        
        # Zatwierdzenie zmian
        conn.commit()
        print(f"Baza danych {database_name} została utworzona.")
    except Exception as e:
        print(f"Wystąpił błąd podczas tworzenia bazy danych: {str(e)}")
    finally:
        # Zamykanie kursora i połączenia
        cursor.close()
        conn.close()

create_database("OLYMPICS")