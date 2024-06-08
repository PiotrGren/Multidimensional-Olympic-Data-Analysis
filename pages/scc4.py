from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
import os
import dash
from dash import dcc, html, Input, Output, callback, State
import plotly.express as px
from pyspark.sql.functions import when, col
import dash_bootstrap_components as dbc
import geopandas as gpd
from pyspark.sql import functions as F
from pyspark.sql.window import Window
import pandas as pd
from pyspark.sql import Window

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


'''

#################################################################################################
(PL)                                            |(EN)                                           
                SCENARIUSZ 1                    |                  SCENARIO 1                           
                                                |                                               
            PRZYGOTOWANIE DANYCH                |               DATA PREPARATION                
                                                |                                               
#################################################################################################

'''
df_europe_gold_under_26 = df.filter((col('Medal') == 'Gold') &
                                    (col('Age') < 26) &
                                    (col('Continent') == 'Europe'))

df_gold_medal_counts = df_europe_gold_under_26.groupBy('Name').agg(count('Medal').alias('GoldMedalCount'))

df_selected_athletes = df_gold_medal_counts.filter(F.col('GoldMedalCount') >= 2)

df_final = df_selected_athletes.join(df_europe_gold_under_26, on='Name', how='inner') \
                               .select('Name', 'Sex', 'GoldMedalCount', 'Sport', 'Season', 'Event', 'Age', 'Continent', 'NOC', 'Year', 'Medal') \
                               .orderBy('Name', 'Year')

df_final = df_final.join(df_final.groupBy('Name').agg(F.countDistinct('Sport').alias('UniqueSports')), on='Name', how='inner')
df_final = df_final.filter(F.col('UniqueSports') == 1)

window = Window.partitionBy('Name')
df_final = df_final.withColumn('GoldMedalCount', F.count('Name').over(window))

df_sorted = df_final.orderBy('Name', 'Year')

window = Window.partitionBy('Name').orderBy('Year')

df_temp = df_sorted.withColumn('PrevYear', F.lag('Year', 1).over(window))

df_selected_years = df_temp.withColumn('YearsToGetTwoGoldMedals', F.col('Year') - F.col('PrevYear'))

df_selected_years = df_selected_years.filter(df_selected_years['YearsToGetTwoGoldMedals'].isNotNull())

df_selected_athletes_unique = df_selected_years.dropDuplicates(['Name'])

df_selected_athletes_unique = df_selected_athletes_unique.select('Name', 'YearsToGetTwoGoldMedals')

df_final = df_final.join(df_selected_athletes_unique, on='Name', how='left')

df_final = df_final.withColumn('YearsToGetTwoGoldMedals', 
                               F.when(df_final['YearsToGetTwoGoldMedals'] == 0, 'S.Y.')
                               .otherwise(df_final['YearsToGetTwoGoldMedals']))

df_final = df_final.orderBy('Name', 'Year')

world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))


'''

#################################################################################################
(PL)                                            |(EN)                                           
                  STRONA DASH                   |                   DASH PAGE
                                                |
#################################################################################################

'''

dash.register_page(__name__, title='Scenariusz 4')

layout = html.Div(children=[
    html.H3(children='Dashboard Scenariusz 4: Analiza wzorców wśród złotych medalistów Europy, odznaczonych złotem przynajmniej dwukrotnie w jednej dziedzinie sportowej', style = {'font-family':'Helvetica', 'padding':'2%'}),
    html.Div([
        html.Label('Wybierz dane:'),
        dcc.Checklist(
            id='scatter-europe-options',
            options=[
                {'label': 'Sezon letni', 'value': 'Summer'},
                {'label': 'Sezon zimowy', 'value': 'Winter'},
                {'label': 'Zdobyte tego samego roku', 'value': 'S.Y.'},
                {'label': 'Zdobyte w 2 lata', 'value': '2'},
                {'label': 'Zdobyte w 4 lata', 'value': '4'},
                {'label': 'Zdobyte w 8 lat', 'value': '8'},
            ],
            value=['Summer', 'Winter', 'S.Y.', '2', '4', '8'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='scatter-europe-graph'
        )
    ], style={'width':'45%', 'float': 'left', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.Div([
        html.Label('Wybierz dane:'),
        dcc.Checklist(
            id='bar-europe-options',
            options=[
                {'label': 'Polska', 'value': 'POL'},
                {'label': 'Francja', 'value': 'FRA'},
                {'label': 'Włochy', 'value': 'ITA'},
                {'label': 'Ukraina', 'value': 'UKR'},
                {'label': 'Wielka Brytania', 'value': 'GBR'},
                {'label': 'Czecho-Słowacja', 'value': 'TCH'},
                {'label': 'Słowacja', 'value': 'SVK'},
                {'label': 'Węgry', 'value': 'HUN'},
                {'label': 'Norwegia', 'value': 'NOR'},
                {'label': 'Finlandia', 'value': 'FIN'},
                {'label': 'Dania', 'value': 'DEN'},
                {'label': 'Holandia', 'value': 'NED'},
                {'label': 'Austria', 'value': 'AUT'},
                {'label': 'Liechtenstein', 'value': 'LIE'},
                {'label': 'Niemcy', 'value': 'GER'},
                {'label': 'Jugosławia', 'value': 'YUG'},
                {'label': 'Szwajcaria', 'value': 'SUI'},
                {'label': 'Rumunia', 'value': 'ROU'},
                {'label': 'Chorwacja', 'value': 'CRO'},
                {'label': 'Hiszpania', 'value': 'ESP'},
                {'label': 'Szwecja', 'value': 'SWE'},
                {'label': 'Bułgaria', 'value': 'BUL'},
                {'label': 'Białoruś', 'value': 'BEL'},
                {'label': 'Grecja', 'value': 'GRE'},
                {'label': 'Litwa', 'value': 'LAT'},
                {'label': 'Czechy', 'value': 'CZE'},
            ],
            value=['POL', 'FRA', 'ITA', 'UKR', 'GBR', 'TCH', 'SVK', 'HUN', 'NOR', 'FIN', 'DEN', 'NED', 'AUT', 'LIE', 'GER', 'YUG', 'SUI', 'ROU', 'CRO', 'ESP', 'SWE', 'BUL', 'BEL', 'GRE', 'LAT', 'CZE'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        html.Button('Zaznacz/Odznacz wszystkie', id='toggle-button', n_clicks=0, className='button-5'),

        dcc.Graph(
            id='bar-europe-graph'
        )
    ], style={'width':'45%', 'float': 'left', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.Div([
        html.Label('Wybierz dane:   [Z.M. - Zdobyte Medale (ilość)]'),
        dcc.Checklist(
            id='parcat-europe-options',
            options=[
                {'label': 'Mężczyźni', 'value': 'Male'},
                {'label': 'Kobiety', 'value': 'Female'},
                {'label': '2 Z.M.', 'value': '2'},
                {'label': '3 Z.M.', 'value': '3'},
                {'label': '4 Z.M.', 'value': '4'},
                {'label': '5 Z.M.', 'value': '5'},
                {'label': '6 Z.M.', 'value': '6'},
            ],
            value=['Male', 'Female', '2', '3', '4', '5', '6'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='parcat-europe-graph'
        )
    ], style={'width':'95%', 'clear': 'both', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.Div([
        html.Label('Płeć:'),
        dcc.Checklist(
            id='gender-europe-options',
            options=[
                {'label': 'Mężczyźni', 'value': 'Male'},
                {'label': 'Kobiety', 'value': 'Female'},
                
            ],
            value=['Male', 'Female'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Checklist(
            id='common-europe-options',
            options=[
                {'label': 'Wspólnie', 'value': 'Common'},
            ],
            value=['Common'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='pie-europe-graph'
        )
    ], style={'width':'45%', 'float': 'left', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.Div([
        html.Label('Płeć:'),
        dcc.Checklist(
            id='sunburst-europe-options',
            options=[
                {'label': 'Sezon', 'value': 'Season'},
                {'label': 'Dyscyplina sportowa', 'value': 'Sport'},
                {'label': 'Płeć', 'value': 'Sex'},
                {'label': 'Czas zdobycia 2 złotych medali', 'value': 'YearsToGetTwoGoldMedals'}
            ],
            value=['Season', 'Sport', 'Sex', 'YearsToGetTwoGoldMedals'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='sunburst-europe-graph'
        )
    ], style={'width':'45%', 'float': 'right', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.Div([
        html.Button('Europa (razem)', id='only-europe-button', className='button-4', n_clicks=0),
        dcc.Store(id='only-europe-store', data={'only_europe': False}),
        dcc.Graph(
            id='geo-graph-europe'
        )
    ], style = {'width':'95%', 'margin':'2%', 'clear':'both'}, className= 'checkbox-wrapper-2 europe-sc4'),

    #Predykcja liczby osiągnięć dla najlepszych sportowców z Europy na przyszłe igrzyska
    html.Div([
        html.Button('ARIMA', id='btn-arima2', className='button-5', n_clicks=0),
        html.Button('Sieć neuronowa', id='btn-nn', className='button-5', n_clicks=0),
        html.Button('Prophet', id='btn-prt', className='button-5', n_clicks=0),
    ], style={'padding': '2%', 'textAlign': 'center'}),

    html.Div(id='plots-container4', style={'padding': '2%', 'textAlign': 'center'})
])


#GRAPH 1 - SCATTER
@callback(
    Output('scatter-europe-graph', 'figure'),
    [Input('scatter-europe-options', 'value'), Input('bar-europe-options', 'value')]
)
def update_scatter_europe(selected, countries):
    if not selected:
        selected = ['Summer', 'Winter', 'S.Y.', '2', '4', '8']

    if not countries:
        countries = ['POL', 'FRA', 'ITA', 'UKR', 'GBR', 'TCH', 'SVK', 'HUN', 'NOR', 'FIN', 'DEN', 'NED', 'AUT', 'LIE', 'GER', 'YUG', 'SUI', 'ROU', 'CRO', 'ESP', 'SWE', 'BUL', 'BEL', 'GRE', 'LAT', 'CZE', 'FRG', 'GDR']

    if 'GER' in countries:
        countries = countries + ['FRG', 'GDR']

    filtered_df = df_final.withColumn('YearsToGetTwoGoldMedals', col('YearsToGetTwoGoldMedals').cast('string'))

    filtered_df = filtered_df.filter(col('Season').isin(selected)).filter(col('YearsToGetTwoGoldMedals').isin(selected)).filter(col('NOC').isin(countries))

    age_year_gold_count_df = filtered_df.filter(filtered_df['Medal'] == 'Gold').groupBy('Year', 'Age', 'Sex').count()

    age_year_gold_count_pd = age_year_gold_count_df.toPandas()

    fig = px.scatter(age_year_gold_count_pd, x='Year', y='Age', size='count', color='Sex', labels={'Year': 'Rok', 'Age': 'Wiek', 'count': 'Liczba sportowców', 'Sex':'Płeć'}, title='Wiek najlepszych złotych medalistów na przestrzeni lat',
                    color_discrete_sequence=px.colors.qualitative.Set1)

    fig.update_layout(paper_bgcolor = 'rgba(50, 50, 50, 0.9)', plot_bgcolor = 'rgba(250, 250, 250, 0.95)', font = dict(color = 'white'))

    return fig


#GRAPH 2 - BAR
@callback(
    Output('bar-europe-options', 'value'),
    Input('toggle-button', 'n_clicks'),
    State('bar-europe-options', 'value')
)
def toggle_all_options(n_clicks, current_values):
    options = ['POL', 'FRA', 'ITA', 'UKR', 'GBR', 'TCH', 'SVK', 'HUN', 'NOR', 'FIN', 'DEN', 'NED', 'AUT', 'LIE', 'GER', 'YUG', 'SUI', 'ROU', 'CRO', 'ESP', 'SWE', 'BUL', 'BEL', 'GRE', 'LAT', 'CZE']
    if n_clicks % 2 == 1:
        if len(current_values) == len(options):
            return []
        else:
            return options
    return current_values

@callback(
    Output('bar-europe-graph', 'figure'),
    [Input('bar-europe-options', 'value'), Input('scatter-europe-options', 'value')]
)
def update_europe_bar(countries, selected):
    if not countries:
        countries = ['POL', 'FRA', 'ITA', 'UKR', 'GBR', 'TCH', 'SVK', 'HUN', 'NOR', 'FIN', 'DEN', 'NED', 'AUT', 'LIE', 'GER', 'YUG', 'SUI', 'ROU', 'CRO', 'ESP', 'SWE', 'BUL', 'BEL', 'GRE', 'LAT', 'CZE']

    if 'GER' in countries:
        countries = countries + ['FRG', 'GDR']

    if not selected:
        selected = ['Summer', 'Winter', 'S.Y.', '2', '4', '8']

    filtered_df = df_final.filter((col('Season').isin(selected)) & (col('YearsToGetTwoGoldMedals').isin(selected)) & (col('NOC').isin(countries)))
    window = Window.partitionBy('Name').orderBy('Year')

    filtered_df = filtered_df.withColumn('row_number', F.row_number().over(window))

    df_first_appearance = filtered_df.filter(F.col('row_number') == 1).drop('row_number')

    age_sport_count = df_first_appearance.groupBy('Age', 'Sex', 'Sport').count().orderBy('Age')

    # Tworzenie wykresu
    fig = px.bar(age_sport_count, x='Age', y='count', color='Sex', barmode='group',
                hover_data = ['Age', 'Sex', 'Sport', 'count'],
                labels={'Age': 'Wiek', 'count': 'Liczba sportowców', 'Sex': 'Płeć', 'Sport': 'Dyscyplina sportowa'},
                title='Wiek w jakim sportowcy wygrali swój pierwszy złoty medal<br />z podziałem na płeć', 
                color_discrete_sequence=[px.colors.qualitative.Bold[2], px.colors.qualitative.Bold[9]])

    fig.update_layout(paper_bgcolor = 'rgba(50, 50, 50, 0.9)', plot_bgcolor = 'rgba(250, 250, 250, 0.95)', font = dict(color = 'white'))

    return fig


#GRAPH 3 - PARALLEL CATEGORIES
@callback(
    Output('parcat-europe-graph', 'figure'),
    [Input('parcat-europe-options', 'value'),
     Input('scatter-europe-options', 'value')]
)
def update_parcat(percat_options, selected):
    if not percat_options:
        percat_options = ['Male', 'Female', '2', '3', '4', '5', '6']

    if not selected:
        selected = ['Summer', 'Winter', 'S.Y.', '2', '4', '8']

    filtered_df = df_final.filter((col('Season').isin(selected)) & (col('YearsToGetTwoGoldMedals').isin(selected)) & (col('Sex').isin(percat_options)) & (col('GoldMedalCount').isin(percat_options)))

    fig = px.parallel_categories(filtered_df[['Continent', 'Sex', 'Age', 'YearsToGetTwoGoldMedals', 'Season', 'GoldMedalCount', 'Medal']], color="GoldMedalCount",
                             labels = {'Continent':'Kontynent', 'Sex':'Płeć', 'Age':'Wiek', 'Sport':'Dyscyplina sportowa', 'YearsToGetTwoGoldMedals':'Czas zdobycia dwóch medali', 'Season':'Sezon', 'Medal':'Medal', 'GoldMedalCount':'Zdobytych Medali'},
                             color_continuous_scale=px.colors.sequential.Plasma)

# Wyświetlenie diagramu
    fig.update_layout(title='Przepływ danych złotych medalistów według kategorii',
                    paper_bgcolor='rgba(50, 50, 50, 0.9)', font=dict(color='white'), plot_bgcolor='rgba(250, 250, 250, 0.95)', height = 650)
    return fig

    
#GRAPH 4 - PIE
@callback(
    Output('pie-europe-graph', 'figure'),
    [Input('gender-europe-options', 'value'),
     Input('common-europe-options', 'value'),
     Input('bar-europe-options', 'value')]
)
def update_europe_pie(genders, common, countries):
    if common == ['Common']:
        if not countries:
            countries = ['POL', 'FRA', 'ITA', 'UKR', 'GBR', 'TCH', 'SVK', 'HUN', 'NOR', 'FIN', 'DEN', 'NED', 'AUT', 'LIE', 'GER', 'YUG', 'SUI', 'ROU', 'CRO', 'ESP', 'SWE', 'BUL', 'BEL', 'GRE', 'LAT', 'CZE']

        if 'GER' in countries:
            countries = countries + ['FRG', 'GDR']

        filtered_df = df_final.filter(col('NOC').isin(countries))
        title = 'Udział podwójnych złotych medalistów w ogólnej liczbie medali<br />w zależności od czasu ich zdobycia'
        labels_columns = 'YearsToGetTwoGoldMedals'

        filtered_df = filtered_df.toPandas()

    else:
        if not countries:
            countries = ['POL', 'FRA', 'ITA', 'UKR', 'GBR', 'TCH', 'SVK', 'HUN', 'NOR', 'FIN', 'DEN', 'NED', 'AUT', 'LIE', 'GER', 'YUG', 'SUI', 'ROU', 'CRO', 'ESP', 'SWE', 'BUL', 'BEL', 'GRE', 'LAT', 'CZE']

        if 'GER' in countries:
            countries = countries + ['FRG', 'GDR']

        if not genders:
            genders = ['Male', 'Female']

        filtered_df = df_final.filter((col('NOC').isin(countries)) & (col('Sex').isin(genders)))
        title = 'Udział podwójnych złotych medalistów w ogólnej liczbie medali<br />w zależności od czasu ich zdobycia oraz płci'

        filtered_df = filtered_df.toPandas()

        filtered_df['YTGM-SEX'] = filtered_df['YearsToGetTwoGoldMedals'].astype(str) + ' (' + filtered_df['Sex'] + ')'
        labels_columns = 'YTGM-SEX'

    years_count = filtered_df.groupby(labels_columns).size().reset_index(name='Count')

    fig = px.pie(years_count, values='Count', names=labels_columns, title=title, color_discrete_sequence=px.colors.qualitative.Set1)

    fig.update_layout(paper_bgcolor = 'rgba(50, 50, 50, 0.9)', plot_bgcolor = 'rgba(250, 250, 250, 0.95)', font = dict(color = 'white'), legend_title='W ile lat zdobyto<br />2 złote medale')

    return fig


#GRAPH 5 - SUNBURST
@callback(
    Output('sunburst-europe-graph', 'figure'),
    Input('sunburst-europe-options', 'value')
)
def update_sunburst_europe(selected):
    if not selected:
        selected = ['Continent', 'Season', 'Sport', 'Sex', 'YearsToGetTwoGoldMedals']

    else:
        selected = ['Continent'] + selected

    df_kpi4 = df_final.toPandas()

    fig = px.sunburst(df_kpi4, path=selected,
                    color='Sport',
                    labels = {'Continent':'Kontynent', 'Season':'Sezon', 'Sex':'Płeć', 'Sport':'Dyscyplina sportowa', 'YearsToGetTwoGoldMedals':'W ciągu ilu lat zdobył 2 złote medale'})

    fig.update_traces(textinfo='label+percent entry', insidetextorientation='radial')
    fig.update_layout(title='Rozkład zdobytych medali w zależności od profilu antropometrycznego polskich sportowców',
                    margin=dict(t=50, l=0, r=0, b=0),
                    paper_bgcolor = 'rgba(50, 50, 50, 0.9)', plot_bgcolor = 'rgba(250, 250, 250, 0.95)', font = dict(color = 'white'))
    
    return fig


#GRAPH 6 - GEO GRAPH
@callback(
    Output('only-europe-store', 'data'),
    Input('only-europe-button', 'n_clicks'),
    State('only-europe-store', 'data')
)
def toggle_only_europe(n_clicks, data):
    if n_clicks:
        data['only_europe'] = not data['only_europe']
    return data

@callback(
    Output('geo-graph-europe', 'figure'),
    [Input('bar-europe-options', 'value'),
     Input('only-europe-store', 'data')]
)
def update_geo_graph(countries, data):
    only_europe = data['only_europe']

    if not countries:
        countries = ['POL', 'FRA', 'ITA', 'UKR', 'GBR', 'TCH', 'SVK', 'HUN', 'NOR', 'FIN', 'DEN', 'NED', 'AUT', 'LIE', 'GER', 'YUG', 'SUI', 'ROU', 'CRO', 'ESP', 'SWE', 'BUL', 'BEL', 'GRE', 'LAT', 'CZE']

    if 'GER' in countries:
        countries = countries + ['FRG', 'GDR']

    if not only_europe:
        df_pd_geo = df_final.filter(df_final['NOC'].isin(countries))
        df_noc = df_pd_geo.filter(df_pd_geo['NOC'] != 'RUS').toPandas().groupby('NOC').count().reset_index()

        europe_medals = world.merge(df_noc, left_on='iso_a3', right_on='NOC', how='left')
        hm = 'name'

    else:
        df_pd_geo = df_final.toPandas()
        df_continent = df_pd_geo.groupby('Continent').count().reset_index()

        europe_medals = world.merge(df_continent, left_on='continent', right_on='Continent', how='left')
        hm = 'continent'

    fig = px.choropleth(europe_medals,
                        geojson=europe_medals.geometry,
                        locations=europe_medals.index,
                        color = 'Medal',
                        hover_name=hm,
                        projection='equirectangular',
                        color_continuous_scale=px.colors.sequential.Aggrnyl)
    
    fig.update_geos(fitbounds="locations", bgcolor = "rgba(50, 50, 50, 0.9)")
    fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', font=dict(color='white'), plot_bgcolor='rgba(250, 250, 250, 0.95)', height = 700)

    return fig



#DATA MINING
@callback(
    Output('plots-container4', 'children'),
    [Input('btn-arima2', 'n_clicks'),
     Input('btn-nn', 'n_clicks'),
     Input('btn-prt', 'n_clicks')]
)
def display_plots(n_clicks_arima, n_clicks_rf, n_clicks_svr):
    ctx = dash.callback_context
    if not ctx.triggered:
        return html.Div("Wybierz algorytm, aby zobaczyć wykres.")
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    algorithm_map = {
        'btn-arima2': 'arima',
        'btn-nn': 'neuralnetwork',
        'btn-prt': 'prophet'
    }
    
    algorithm = algorithm_map[button_id]
    plot_image_path = f'assets/Wykresy/SC4/{algorithm}.png'

    return html.Div(html.Img(src=plot_image_path, style={'width': '95%', 'padding': '1%', 'margin':'1%'}), style={'display': 'flex', 'justify-content': 'center'})