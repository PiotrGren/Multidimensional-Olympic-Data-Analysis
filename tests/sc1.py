from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
import pyspark.pandas as psd
import os
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
from pyspark.sql.functions import when, col
import dash_bootstrap_components as dbc


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

except Exception as e:
    print(f"Wystąpił błąd podczas próby wczytania danych:\n\n{e}")





'''

#################################################

                SCENARIUSZ 1

#################################################

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

'''

#################################################

                APLIKACJA DASH

#################################################

'''
# Inicjalizacja aplikacji Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Definiowanie layoutu aplikacji Dash
app.layout = html.Div(children=[
    html.H1(children='Dashboard Scenariusz 1: Zdobyte medale - analiza kontynentalna', style = {'font-family':'Helvetica', 'padding':'2%'}),
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
])


#GRAPH 1 - SUNBURST
@app.callback(
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
@app.callback(
    Output('bar-graph', 'figure'),
    [Input('grouping-options', 'value'),
     Input('age-bins', 'value')]
)
def update_bar(selected_groupings, selected_age_bins):
    filtered_df = df1[df1['Age Bin'].isin(selected_age_bins)]


    fig_bar = px.bar(filtered_df, x='Continent', y='MedalCount', hover_data = ['Season', 'Sex', 'Age Bin', 'MedalCount'], color='MedalCount', title='Liczba zdobytych medali przez kontynenty w podziale na sezony', barmode='group', labels={'MedalCount':'Zdobyte medale', 'Continent':'Kontynent', 'Season':'Sezon', 'Sex':'Płeć', 'Age Bin':'Przedział wiekowy'})

    fig_bar.update_layout(paper_bgcolor = 'rgba(50, 50, 50, 0.9)',
    font = dict(color = 'white'))
    #fig_bar.update_layout(height = 700)
    return fig_bar


#GRAPH 3 - 
@app.callback(
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
@app.callback(
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
@app.callback(
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


app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

# Uruchomienie serwera
if __name__ == '__main__':
    app.run_server(debug=True)#, host = '0.0.0.0', port = 8050)