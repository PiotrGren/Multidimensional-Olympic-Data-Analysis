import dash
from dash import html, dash_table
from dash.dependencies import Input, Output
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
import os

try:
    os.environ['PYARROW_IGNORE_TIMEZONE'] = '1'

    spark = SparkSession.builder \
        .appName("PySpark SQL Server Connection") \
        .config("spark.jars", "mssql-jdbc-12.6.1.jre8.jar") \
        .getOrCreate()
    
    server = "localhost"
    port = "1433"
    database_name = "OLYMPICS"
    url = f"jdbc:sqlserver://{server}:{port};databaseName={database_name}"

    table_name = "athlete_events_prepared"
    password = "Passwd1234"
    username = "sa"

    df = spark.read \
        .format("jdbc") \
        .option("url", url) \
        .option("dbtable", table_name) \
        .option("user", username) \
        .option("password", password) \
        .option("encrypt", "false") \
        .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
        .load()
    
    print("Dane zostały pomyślnie wczytane z MSSQL Server")

    df = df.withColumn('Continent', when(col('NOC') == 'RUS', 'Asia').otherwise(col('Continent')))

except Exception as e:
    print(f"Wystąpił błąd podczas próby wczytania danych:\n\n{e}")


pandas_df = df.toPandas()



dash.register_page(__name__, path='/', tite='Strona Główna')

layout = html.Div([
    html.Div('W ramach tego projektu przeprowadziliśmy wielowymiarową analizę danych dotyczących uczestników igrzysk olimpijskich. Dane, które wykorzystaliśmy, zostały pobrane z bazy historycznych wyników olimpijskich, a następnie poddane wstępnemu czyszczeniu i przekształceniu.Naszym celem było zrozumienie struktury danych oraz możliwości analizy wielowymiarowej, co pozwala na wyciągnięcie istotnych wniosków i odkrycie ukrytych wzorców.', 
             style = {'text-align':'justify', 'padding-left':'5%', 'padding-right':'5%', 'font-size':'20px', 'margin':'1%'}),

    html.Div([
        html.H2('Opis danych'),
        html.P("Dane użyte w projekcie zawierają następujące kolumny:"),
        html.Ul([
            html.Li("ID: Unikalny identyfikator zawodnika."),
            html.Li("Name: Imię i nazwisko zawodnika."),
            html.Li("Sex: Płeć zawodnika (Male/Female)."),
            html.Li("Age: Wiek zawodnika w momencie uczestnictwa w igrzyskach."),
            html.Li("Height: Wzrost zawodnika (w centymetrach)."),
            html.Li("Weight: Waga zawodnika (w kilogramach)."),
            html.Li("Team: Kraj reprezentowany przez zawodnika."),
            html.Li("NOC: Narodowy Komitet Olimpijski reprezentowany przez zawodnika."),
            html.Li("Games: Rok i sezon igrzysk (np. 1992 Summer)."),
            html.Li("City: Miasto, w którym odbyły się igrzyska."),
            html.Li("Sport: Dyscyplina sportowa."),
            html.Li("Event: Konkretne wydarzenie sportowe."),
            html.Li("Medal: Typ zdobytego medalu (Gold/Silver/Bronze/No medal)."),
            html.Li("Year: Rok, w którym odbyły się igrzyska."),
            html.Li("Season: Sezon igrzysk (Summer/Winter)."),
            html.Li("Century: Wiek, w którym odbyły się igrzyska."),
            html.Li("Age Bin: Kategoria wiekowa zawodnika."),
            html.Li("Continent: Kontynent, z którego pochodzi zawodnik."),
        ]),
        html.P("Dane te, po wstępnym wyczyszczeniu i przekształceniu, umożliwiają przeprowadzenie różnorodnych analiz wielowymiarowych."),

    
        
    ], style = {'text-align':'left', 'padding-left':'5%', 'padding-right':'5%',  'font-size':'20px', 'margin':'1%'})

], className = 'home-page-main')

'''
html.Div([
            dash_table.DataTable(
                data=pandas_df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in pandas_df.columns],
                page_size=10  # Liczba wierszy wyświetlanych na jednej stronie
            )
        ], style={'margin-left': '5%','margin-right': '5%','width': '90%'})
'''