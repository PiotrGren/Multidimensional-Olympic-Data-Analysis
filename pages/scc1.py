from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
import os
import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
from pyspark.sql.functions import when, col
import dash_bootstrap_components as dbc
import geopandas as gpd
import plotly.graph_objects as go



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
df_kpi1 = df.filter(col('Medal') != 'No medal').groupBy('Continent', 'Season', 'Medal', 'Sex', 'Age Bin').agg(count('Medal').alias('MedalCount'))

df1 = df_kpi1.toPandas()

# Przekształcenie kolumny "Medal" na trzy osobne kolumny
df_kpi1_1 = df_kpi1.drop('Sex')
df_kpi1_transformed = df_kpi1.withColumn('Gold', when(col('Medal') == 'Gold', col('MedalCount')).otherwise(0)) \
                               .withColumn('Silver', when(col('Medal') == 'Silver', col('MedalCount')).otherwise(0)) \
                               .withColumn('Bronze', when(col('Medal') == 'Bronze', col('MedalCount')).otherwise(0))

# Sumowanie ilości medali dla każdego koloru
df_kpi1_pivoted = df_kpi1_transformed.groupBy('Continent', 'Season') \
                                      .agg({'Gold':'sum', 'Silver':'sum', 'Bronze':'sum'}) \
                                      .withColumnRenamed('sum(Gold)', 'Gold') \
                                      .withColumnRenamed('sum(Silver)', 'Silver') \
                                      .withColumnRenamed('sum(Bronze)', 'Bronze')

df_kpi1_pivoted = df_kpi1_pivoted.withColumn('MedalCount', col('Gold') + col('Silver') + col('Bronze'))


df_kpi1_p = df_kpi1_pivoted.toPandas()

df_kpi2 = df.filter(col('Medal') != 'No medal').groupBy('Continent', 'Season', 'Age Bin').agg(count('Medal').alias('MedalCount'))
df_kpi21 = df_kpi2.filter(col('Season') == 'Winter')
df_kpi22 = df_kpi2.filter(col('Season') == 'Summer')
df_kpi21 = df_kpi21.toPandas()
df_kpi22 = df_kpi22.toPandas()


df_geo = df.filter(col('Medal') != 'No medal').toPandas()
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

'''

#################################################################################################
(PL)                                            |(EN)                                           
                  STRONA DASH                   |                   DASH PAGE
                                                |
#################################################################################################

'''
# Inicjalizacja aplikacji Dash
#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
dash.register_page(__name__, title='Scenariusz 1')

# Definiowanie layoutu aplikacji Dash
layout = html.Div(children=[
    html.H3(children='Dashboard Scenariusz 1: Zdobyte medale - analiza kontynentalna', style = {'font-family':'Helvetica', 'padding':'2%'}),
    html.Div([
        html.Label('Wybierz dane:'),
        dcc.Checklist(
            id='grouping-options',
            options=[
                {'label': 'Kontynent', 'value': 'Continent'},
                {'label': 'Sezon', 'value': 'Season'},
                {'label': 'Medal', 'value': 'Medal'},
                {'label': 'Płeć', 'value': 'Sex'},
                {'label': 'Wiek', 'value': 'Age Bin'},
                {'label': 'Medale', 'value': 'MedalCount'},
            ],
            value=['Continent', 'Season', 'Medal', 'MedalCount'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='sunburst-graph'
        )
    ], style={'width':'32%', 'float': 'left', 'margin':'2%'}, className = 'checkbox-wrapper-2'),
    
    html.Div([
        html.Label('Wybierz przedziały wiekowe:'),
        dcc.Checklist(
            id='age-bins',
            options=[{'label': age_bin, 'value': age_bin} for age_bin in df1['Age Bin'].unique()],
            value=df1['Age Bin'].unique(),
            inline=True,
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='bar-graph'
        ),
    ], style={'width': '60%', 'float': 'right', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.Div([
        dcc.Graph(
            id='bar-graph3'
        ),
        
        ], style={'float': 'left', 'width': '47%', 'margin-left':'2%', 'margin-right':'1%', 'margin-bottom':'2%'}),

        html.Div([
            dcc.Graph(
                id='bar-graph4'
            )
        ], style={'float': 'right', 'width': '47%', 'margin-left':'1%', 'margin-right':'2%', 'margin-bottom':'2%'}),
    
    html.Div([
        dcc.Graph(
            id='bar-graph2'
        ),
    ], style = {'clear': 'both', 'margin':'2%'}),

    html.Div([
        dcc.Checklist(
            id='continent-options',
            options=[
                {'label': 'Europa', 'value': 'Europe'},
                {'label': 'Ameryka Północna', 'value': 'North America'},
                {'label': 'Ameryka Południowa', 'value': 'South America'},
                {'label': 'Azja', 'value': 'Asia'},
                {'label': 'Afryka', 'value': 'Africa'},
                {'label': 'Australia i Oceania', 'value': 'Oceania'},
            ],
            value=['Europe', 'North America', 'South America', 'Asia', 'Africa', 'Oceania'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

         dcc.Checklist(
            id='only-continent',
            options=[
                {'label': 'Tylko Kontynenty', 'value': 'Yes'}
            ],
            value=['Yes'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='geo-graph'
        )
    ], style = {'width':'95%', 'margin':'2%'}, className= 'checkbox-wrapper-2'),

    html.H3(children='Data Mining - Przewidywanie liczby medali w czasie (przyszłe igrzyska) z podziałem na sezony', style={'font-family':'Helvetica', 'padding':'2%'}),
    html.H4(children='Wybierz kontynent:', style={'font-family':'Helvetica', 'padding':'2%'}),
    
    html.Div([
        html.Button('Europa', id='btn-europe', className='button-5', n_clicks=0),
        html.Button('Północna Ameryka', id='btn-north-america', className='button-5', n_clicks=0),
        html.Button('Południowa Ameryka', id='btn-south-america', className='button-5', n_clicks=0),
        html.Button('Azja', id='btn-asia', className='button-5', n_clicks=0),
        html.Button('Oceania', id='btn-oceania', className='button-5', n_clicks=0),
        html.Button('Afryka', id='btn-africa', className='button-5', n_clicks=0),
    ], style={'padding': '2%', 'textAlign': 'center'}),

    html.Div(id='plots-container', style={'padding': '2%', 'textAlign': 'center'}),
])


#GRAPH 1 - SUNBURST
@callback(
    Output('sunburst-graph', 'figure'),
    Input('grouping-options', 'value')
)
def update_sunburst(selected_groupings):
    if not selected_groupings:
        selected_groupings = ["Continent", "Season", "Medal", "MedalCount"]

    fig_sunburst = px.sunburst(df1, path=selected_groupings, values='MedalCount')

    fig_sunburst.update_layout(paper_bgcolor = 'rgba(50, 50, 50, 0.9)',
    font = dict(color = 'white'))

    #fig_sunburst.update_traces(textinfo='label+percent entry')
    return fig_sunburst



#GRAPH 2 - 
@callback(
    Output('bar-graph', 'figure'),
    [Input('grouping-options', 'value'),
     Input('age-bins', 'value')]
)
def update_bar(selected_groupings, selected_age_bins):
    filtered_df = df1[df1['Age Bin'].isin(selected_age_bins)]


    fig_bar = px.bar(filtered_df, x='Continent', y='MedalCount', hover_data = ['Season', 'Sex', 'Age Bin', 'MedalCount'], color='MedalCount', title='Liczba zdobytych medali przez kontynenty w podziale na sezony', barmode='group', labels={'MedalCount':'Zdobyte medale', 'Continent':'Kontynent', 'Season':'Sezon', 'Sex':'Płeć', 'Age Bin':'Przedział wiekowy'})

    fig_bar.update_layout(paper_bgcolor = 'rgba(50, 50, 50, 0.9)',
    font = dict(color = 'white'), height = 550)
    #fig_bar.update_layout(height = 700)
    return fig_bar


#GRAPH 3 - 
@callback(
    Output('bar-graph2', 'figure'),
    Input('grouping-options', 'value')
)
def update_bar2(selected_groupings):
    fig = px.bar(df_kpi1_p,
             x='Continent',
             y=['Gold', 'Silver', 'Bronze'],
             color_discrete_map={'Gold': 'gold', 'Silver': 'silver', 'Bronze': 'peru'},  # Przypisanie kolorów dla medali
             barmode='group',  # Słupki skumulowane na sobie
             title='Medale zdobyte przez kontynenty',
             text='Season',
             labels={
                 'value': 'Liczba zdobytych medali',
                 'Continent': 'Kontynent',
                 'variable': 'Medal',
                 'gold': 'Złoto',
                 'silver': 'Srebro',
                 'bronze': 'Brąz'
                }
             )
    
    fig.update_layout(height = 500,
    paper_bgcolor = 'rgba(50, 50, 50, 0.9)',
    font = dict(color = 'white'))
    
    return fig

#GRAPH 4 -
@callback(
    Output('bar-graph3', 'figure'),
    [Input('grouping-options', 'value'),
     Input('age-bins', 'value')]
)
def update_bar_winter(selected_groupings, selected_age_bins):
    filtered_df = df_kpi21[df_kpi21['Age Bin'].isin(selected_age_bins)]
    fig = px.bar(filtered_df, 
             x='Age Bin', 
             y='MedalCount', 
             color='Continent',
             facet_row_spacing=0.05,
             barmode='group', 
             labels={
                 'MedalCount': 'Liczba zdobytych medali',
                 'Age Bin': 'Przedziały wiekowe',
                 'Continent': 'Kontynent',
                 'Season': 'Sezon'
             },
             title='Liczba zdobytych medali w różnych przedziałach wiekowych - sezon zimowy')
    
    fig.update_layout(
    legend_title='Kontynent',
    barmode='group',
    paper_bgcolor = 'rgba(50, 50, 50, 0.9)',
    font = dict(color = 'white'))

    return fig

#GRAPH 5 - 
@callback(
    Output('bar-graph4', 'figure'),
    [Input('grouping-options', 'value'),
     Input('age-bins', 'value')]
)
def update_bar_summer(selected_groupings, selected_age_bins):
    filtered_df = df_kpi22[df_kpi22['Age Bin'].isin(selected_age_bins)]
    fig2 = px.bar(filtered_df, 
             x='Age Bin', 
             y='MedalCount', 
             color='Continent',
             facet_row_spacing=0.05,
             barmode='group', 
             labels={
                 'MedalCount': 'Liczba zdobytych medali',
                 'Age Bin': 'Przedziały wiekowe',
                 'Continent': 'Kontynent',
                 'Season': 'Sezon'
             },
             title='Liczba zdobytych medali w różnych przedziałach wiekowych - sezon letni')
    
    fig2.update_layout(
    legend_title='Kontynent',
    barmode='group',
    paper_bgcolor = 'rgba(50, 50, 50, 0.9)',
    font = dict(color = 'white')) 

    return fig2


#GRAPH 6 - GEO GRAPH
@callback(
    Output('geo-graph', 'figure'),
    [Input('continent-options', 'value'),
     Input('only-continent', 'value')]
)
def update_geo_graph(continents, continents_map):
    if not continents:
        continents = ['Europe', 'North America', 'South America', 'Asia', 'Africa', 'Oceania']

    filtered_df = df_geo[df_geo['Continent'].isin(continents)]
    filtered_df.loc[filtered_df['NOC'] == 'RUS', 'Continent'] = 'Asia'

    if not continents_map:
        #filtered_df = filtered_df[df_geo['Continent'].isin(continents)]
        filtered_df = filtered_df.groupby('NOC')['Medal'].count().reset_index()

        world_medals = world.merge(filtered_df, left_on='iso_a3', right_on='NOC', how='left')

        hover = 'name'

    else:
        #filtered_df = filtered_df[df_geo['Continent'].isin(continents)]
        filtered_df = filtered_df.groupby('Continent')['Medal'].count().reset_index()

        world_medals = world.merge(filtered_df, left_on='continent', right_on='Continent', how='left')

        hover = 'continent'

    world_medals.loc[world_medals['iso_a3'] == 'RUS', 'continent'] = 'Asia'

    fig = px.choropleth(
        world_medals,
        geojson=world_medals.geometry,
        locations=world_medals.index,
        color='Medal',
        hover_name=hover,
        projection='equirectangular',
        labels = {'Medal':'Liczba zdobytych medali'},
        title = 'Zestawienie zdobytej liczby medali przez kontynenty',
        color_continuous_scale=px.colors.diverging.Portland
    )

    fig.update_geos(fitbounds="locations", bgcolor = "rgba(50, 50, 50, 0.9)")

    fig.update_layout(height = 700, paper_bgcolor = 'rgba(50, 50, 50, 0.9)', font = dict(color = 'white'), plot_bgcolor='#049528')

    return fig
    

#DISPLAYING PREDICTION IMAGES
@callback(
    Output('plots-container', 'children'),
    [Input('btn-europe', 'n_clicks'),
     Input('btn-north-america', 'n_clicks'),
     Input('btn-south-america', 'n_clicks'),
     Input('btn-asia', 'n_clicks'),
     Input('btn-oceania', 'n_clicks'),
     Input('btn-africa', 'n_clicks')]
)
def display_plots(n_clicks_europe, n_clicks_north_america, n_clicks_south_america, n_clicks_asia, n_clicks_oceania, n_clicks_africa):
    ctx = dash.callback_context
    if not ctx.triggered:
        return html.Div("Wybierz kontynent, aby zobaczyć wykresy.")
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    continent_map = {
        'btn-europe': 'Europe',
        'btn-north-america': 'North America',
        'btn-south-america': 'South America',
        'btn-asia': 'Asia',
        'btn-oceania': 'Oceania',
        'btn-africa': 'Africa'
    }
    
    continent = continent_map[button_id]
    base_path = f'assets/Wykresy/{continent}'
    plot_filenames = [
        'summer_arima.png',
        'summer_gradientboosting.png',
        'summer_randomforest.png',
        'winter_arima.png',
        'winter_gradientboosting.png',
        'winter_randomforest.png'
    ]

    plots = []
    for i in range(0, len(plot_filenames), 3):
        row_plots = []
        for j in range(3):
            #plot_path = os.path.join(base_path, plot_filenames[i + j])
            plot_path = base_path + '/' + plot_filenames[i + j]
            row_plots.append(html.Img(src=plot_path, style={'width': '32%', 'padding': '1%'}))
        plots.append(html.Div(row_plots, style={'display': 'flex', 'justify-content': 'center'}))
    
    return html.Div(plots)