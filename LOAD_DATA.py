import pandas as pd
from sqlalchemy import create_engine, inspect

def load_data(database_name, file_path, table_name, server="localhost", username='sa', password='Passwd1234', driver="ODBC Driver 17 for SQL Server"):

    engine = create_engine(f'mssql+pyodbc://{username}:{password}@{server}/{database_name}?driver={driver}')

    df = pd.read_csv(file_path)

    df.to_sql(table_name, engine, if_exists="append", index=False)

    print("Dane zostały pomyślnie dodane do tabeli w bazie danych")

def list_tables_and_show_data(database_name, server="localhost", username='sa', password='Passwd1234', driver="ODBC Driver 17 for SQL Server"):
    # Tworzenie silnika bazy danych
    engine = create_engine(f'mssql+pyodbc://{username}:{password}@{server}/{database_name}?driver={driver}')

    # Tworzenie inspektora bazy danych
    inspector = inspect(engine)

    # Pobieranie listy tabel
    tables = inspector.get_table_names()
    print(f"Istniejące tabele w bazie danych {database_name}: {tables}")

    '''
    for table in tables:
        df = pd.read_sql_table(table, engine)
        print(f"Pierwsze 5 wierszy tabeli {table}:")
        print(df.head())
    '''
    



database_name = "OLYMPICS"
file_path = "Dane/athlete_events.csv"
#file_path2 = "Dane/country-codes.csv"

load_data(database_name, file_path, "athlete_events")
#load_data(database_name, file_path2,  "country_codes")

list_tables_and_show_data(database_name)