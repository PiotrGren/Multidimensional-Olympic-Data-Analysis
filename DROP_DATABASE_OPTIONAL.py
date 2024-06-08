from sqlalchemy import create_engine, text

def drop_database(database_name, server="localhost", username='sa', password='Passwd1234', driver="ODBC Driver 17 for SQL Server"):
    # Tworzenie silnika bazy danych do połączenia z serwerem
    engine = create_engine(f'mssql+pyodbc://{username}:{password}@{server}/master?driver={driver}', isolation_level="AUTOCOMMIT")

    # Tworzenie połączenia
    with engine.connect() as connection:
        # Upewnienie się, że wszyscy użytkownicy są odłączeni od bazy danych
        connection.execute(text(f"ALTER DATABASE {database_name} SET SINGLE_USER WITH ROLLBACK IMMEDIATE"))

        # Usunięcie bazy danych
        connection.execute(text(f"DROP DATABASE IF EXISTS {database_name}"))
        print(f"Baza danych {database_name} została usunięta")

# Przykład użycia funkcji
database_name = "OLYMPICS"

drop_database(database_name)
