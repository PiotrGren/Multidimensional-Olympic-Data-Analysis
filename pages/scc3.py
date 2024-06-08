from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
import os
import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
from pyspark.sql.functions import when, col
import dash_bootstrap_components as dbc
from pyspark.sql.functions import *
from pyspark.ml.feature import Bucketizer
import random
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib
from dash.exceptions import PreventUpdate
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

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

#################################################################################################
(PL)                                            |(EN)                                           
                SCENARIUSZ 3                    |                  SCENARIO 3                           
                                                |                                               
            PRZYGOTOWANIE DANYCH                |               DATA PREPARATION                
                                                |                                               
#################################################################################################

'''
hm = df.groupBy('Sport').agg(mean('Height').alias('MeanHeight'))
df_kpi3 = df.join(hm, 'Sport', 'left').withColumn('Height', when(col('Height').isNull(), col('MeanHeight')).otherwise(col('Height')))
df_kpi3 = df_kpi3.drop('MeanHeight')

wm = df_kpi3.groupBy('Sport', 'Height').agg(mean('Weight').alias('MeanWeight'))
df_kpi3 = df_kpi3.join(wm, ['Sport', 'Height'], 'left').withColumn('Weight', when(col('Weight').isNull(), col('MeanWeight')).otherwise(col('Weight')))
df_kpi3 = df_kpi3.drop('MeanWeight')

wma = df_kpi3.groupBy('Sport').agg(mean('Weight').alias('MeanWeight'))
df_kpi3 = df_kpi3.join(wma, 'Sport', 'left').withColumn('Weight', when(col('Weight').isNull(), col('MeanWeight')).otherwise(col('Weight')))
df_kpi3 = df_kpi3.drop('MeanWeight')

df_kpi3 = df_kpi3.dropna(subset=['Height', 'Weight'])

df_kpi3 = df_kpi3.filter(col('NOC') == 'POL')
top5sports = df_kpi3.groupBy('Sport').count().orderBy(desc('count')).limit(5)
top5sports = [row['Sport'] for row in top5sports.collect()]
df_kpi3 = df_kpi3.filter(df_kpi3['Sport'].isin(top5sports))

df_kpi3 = df_kpi3.withColumn('BMI', round(col('Weight') / (col('Height') / 100) ** 2, 2))

df_kpi3 = df_kpi3.filter((col('BMI') >= 18.50) & (col('BMI') <= 35.00))

min_bmi = df_kpi3.agg(min(col('BMI'))).collect()[0][0]
max_bmi = df_kpi3.agg(max(col('BMI'))).collect()[0][0]

bins = np.linspace(min_bmi, max_bmi, num=9)
bins = [np.round(b, 2) for b in bins]

labels = []
for i in range(1, len(bins)):
    if i == 1:
        labels.append(f'{str(bins[i-1])}-{str(bins[i])}')
    else:
        labels.append(f'{str(np.round(bins[i-1]+ 0.01, 2))}-{str(bins[i])}')

przedzialy = Bucketizer(splits = bins, inputCol='BMI', outputCol = 'BMI Bin')

df_kpi3 = przedzialy.setHandleInvalid("keep").transform(df_kpi3)


df_kpi3 = df_kpi3.withColumn('BMI Bin',
                   when(df_kpi3['BMI Bin'] == 0.0, labels[0])
                   .when(df_kpi3['BMI Bin'] == 1.0, labels[1])
                   .when(df_kpi3['BMI Bin'] == 2.0, labels[2])
                   .when(df_kpi3['BMI Bin'] == 3.0, labels[3])
                   .when(df_kpi3['BMI Bin'] == 4.0, labels[4])
                   .when(df_kpi3['BMI Bin'] == 5.0, labels[5])
                   .when(df_kpi3['BMI Bin'] == 6.0, labels[6])
                   #.when(df['Age Bin'] == 7.0, labels[7])
                   #.when(df['Age Bin'] == 8.0, labels[8])
                   .otherwise("Unknown"))

df_kpi3 = df_kpi3.filter((df_kpi3['BMI Bin'] != "Unknown"))

df_final = df_kpi3.filter(col('Medal') != 'No medal').filter(col('Year') >= 1945).groupBy('Team', 'Sport', 'Sex','Height', 'Weight','Age', 'Age Bin','BMI', 'BMI Bin', 'Medal').agg(count('Medal').alias('MedalCount')).orderBy('Team', 'Sport', 'Sex')
df_final2 = df_kpi3.filter(col('Year') >= 1945).groupBy('Team', 'Sport', 'Sex','Height', 'Weight','Age', 'Age Bin','BMI', 'BMI Bin', 'Medal').agg(count('Medal').alias('MedalCount')).orderBy('Team', 'Sport', 'Sex')

df_final = df_final.withColumn('Team', when(df_final['Team'] == 'Poland-1', 'Poland').otherwise(df_final['Team']))
df_final2 = df_final2.withColumn('Team', when(df_final2['Team'] == 'Poland-1', 'Poland').otherwise(df_final2['Team']))

df_final = df_final.toPandas()
df_final2 = df_final2.toPandas()

age_bin_mapping = {bin_val: i for i, bin_val in enumerate(df_final['Age Bin'].unique())}
bmi_bin_mapping = {bin_val: i for i, bin_val in enumerate(df_final['BMI Bin'].unique())}
sport_mapping = {bin_val: i for i, bin_val in enumerate(df_final['Sport'].unique())}
sex_mapping = {bin_val: i for i, bin_val in enumerate(df_final['Sex'].unique())}
medal_mapping = {bin_val: i for i, bin_val in enumerate(df_final['Medal'].unique())}

mappinglist = [age_bin_mapping, bmi_bin_mapping, sport_mapping, sex_mapping, medal_mapping]

for mapping in mappinglist:
    mapping_name = [name for name in globals() if globals()[name] is mapping][0]

    key_list_name = mapping_name.replace('_mapping', '_keys')
    values_list_name = mapping_name.replace('_mapping', '_values')

    key_list = []
    values_list = []
    for key, value in mapping.items():
        key_list.append(key)
        values_list.append(value)

    globals()[key_list_name] = key_list
    globals()[values_list_name] = values_list

    #print(f'{key_list_name} = {globals()[key_list_name]}')
    #print(f'{values_list_name} = {globals()[values_list_name]}')

cminv = float(np.min(df_final['BMI']))
cmaxv = float(np.max(df_final['BMI']))

le = LabelEncoder()
df_result = df_final2
df_result['Sport_Encoded'] = le.fit_transform(df_result['Sport'])
df_result['Medal_Encoded'] = df_result['Medal'].apply(lambda x: 0 if x == 'No medal' else 1)
df_result['Sex_Encoded'] = le.fit_transform(df_result['Sex'])

#print(df_result.columns)

X = df_result[['Sport_Encoded', 'Sex_Encoded', 'Height', 'Weight', 'Age', 'BMI']]
X_sport = df_result[['Sport']]
y = df_result['Medal_Encoded']

color_good_pred = px.colors.sequential.Emrld[4]
color_bad_pred = px.colors.sequential.RdBu[2]
'''

#################################################################################################
(PL)                                            |(EN)                                           
                  STRONA DASH                   |                   DASH PAGE
                                                |
#################################################################################################

'''

dash.register_page(__name__, title = 'Scenariusz 3')

layout = html.Div(children = [
    html.H3(children='Dashboard Scenariusz 3: Analiza profilu antropometrycznego polskich sportowców w kontekście zdobytych osiągnięć', style = {'font-family':'Helvetica', 'padding':'2%'}),

    html.Div([
        html.Label('Wybierz dane:'),
        dcc.Checklist(
            id='grouping-options-pol',
            options=[
                {'label': 'Dyscyplina sportowa', 'value': 'Sport'},
                {'label': 'Płeć', 'value': 'Sex'},
                {'label': 'Przedział wiekowy', 'value': 'Age Bin'},
                {'label': 'Wskaźnik BMI', 'value': 'BMI Bin'},
                {'label': 'Medal', 'value': 'Medal'},
            ],
            value=['Team','Sport', 'Sex', 'Age Bin', 'BMI Bin', 'Medal'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='sunburst-graph-pol'
        )
    ], style={'width':'40%', 'float':'left', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.Div([
        dcc.Graph(
            id='bar-graph-pol-sex'
        )
    ], style={'width':'50%', 'float':'right', 'margin':'2%', 'margin-top':'4%'}),

    html.Div([
        html.Label('Wybierz dane:'),
        dcc.Checklist(
            id='grouping-options-pol-tree',
            options=[
                {'label': 'Dyscyplina sportowa', 'value': 'Sport'},
                {'label': 'Płeć', 'value': 'Sex'},
                {'label': 'Przedział wiekowy', 'value': 'Age Bin'},
                {'label': 'Wskaźnik BMI', 'value': 'BMI Bin'},
                {'label': 'Medal', 'value': 'Medal'},
            ],
            value=['Team','Sport', 'Sex', 'Age Bin', 'BMI Bin', 'Medal'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='tree-graph-pol'
        )
    ], style={'width':'95%', 'margin':'2%', 'clear':'both'}, className = 'checkbox-wrapper-2'),

    html.Div([
        html.Div([
            html.Label('Wybierz dyscypliny:', style={'margin-bottom':'1%'}),
            dcc.Checklist(
                id='pol-scatter-sport',
                options=[
                    {'label': 'Lekko atletyka', 'value': 'Athletics'},
                    {'label': 'Kajakarstwo', 'value': 'Canoeing'},
                    {'label': 'Szermierka', 'value': 'Fencing'},
                    {'label': 'Gimnastyka', 'value': 'Gymnastics'},
                    {'label': 'Wioślarstwo', 'value': 'Rowing'},
                ],
                value=['Athletics', 'Canoeing', 'Fencing', 'Gymnastics', 'Rowing'],
                inline=True,
                style = {'font-family':'Helvetica', 'font-size':'15px'},
                inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
                inputClassName = 'sc-gJwTLC ikxBAC'
            )
        ], className='left-column'),
        
        html.Div([
            html.Label('Wybierz przedziały wiekowe:'),
            dcc.Checklist(
                id='pol-scatter-agebin',
                options=[
                    {'label': '1-20', 'value': '1-20'},
                    {'label': '21-25', 'value': '21-25'},
                    {'label': '26-30', 'value': '26-30'},
                    {'label': '31-40', 'value': '31-40'},
                ],
                value=['1-20', '21-25', '26-30', '31-40'],
                inline=True,
                style = {'font-family':'Helvetica', 'font-size':'15px'},
                inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
                inputClassName = 'sc-gJwTLC ikxBAC'
            )
        ], className='right-column'),

        html.Div([
            html.Label('Wybierz przedziały wskaźnika BMI:'),
            dcc.Checklist(
                id='pol-scatter-bmibin',
                options=[
                    {'label': '18.51-20.56', 'value': '18.51-20.56'},
                    {'label': '20.57-22.61', 'value': '20.57-22.61'},
                    {'label': '22.62-24.66', 'value': '22.62-24.66'},
                    {'label': '24.67-26.7', 'value': '24.67-26.7'},
                    {'label': '26.71-28.75', 'value': '26.71-28.75'},
                    {'label': '28.76-30.8', 'value': '28.76-30.8'},
                    {'label': '30.81-32.85', 'value': '30.81-32.85'},
                ],
                value=['18.51-20.56', '20.57-22.61', '28.76-30.8', '26.71-28.75', '22.62-24.66', '30.81-32.85', '24.67-26.7'],
                inline=True,
                style = {'font-family':'Helvetica', 'font-size':'15px'},
                inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
                inputClassName = 'sc-gJwTLC ikxBAC'
            )
        ], className='center-column'),

        html.Div([
            dcc.Graph(
                id='scatter-graph-pol'
            )
        ], className='graph-scatter-pol')
        
    ], style={'width':'95%', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.Div([
        dcc.Checklist(
                id='parallel-options',
                options=[
                    {'label': 'Dyscyplina sportowa', 'value': 'Sport'},
                    {'label': 'Wiek', 'value': 'Age'},
                    {'label': 'Medal', 'value': 'Medal'},
                    {'label': 'BMI', 'value': 'BMI'},
                    {'label': 'Płeć', 'value': 'Sex'},
                ],
                value=['Sport', 'Age','Medal', 'BMI', 'Sex'],
                inline=True,
                style = {'font-family':'Helvetica', 'font-size':'15px'},
                inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
                inputClassName = 'sc-gJwTLC ikxBAC'
            ),

        dcc.Graph(
                id='parallel-graph'
            )
    ], style={'width':'95%', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.H3(children='Data Mining - Przewidywanie szansy na zdobycie medalu na podstawie profilu antropometrycznego', style={'font-family':'Helvetica', 'padding':'2%'}),
    html.H4(children='Wybierz wielkość danych:', style={'font-family':'Helvetica', 'padding':'2%'}),
    
    html.Div([
        html.Button('100%', id='btn-100', className='button-5', n_clicks=0),
        html.Button('80%', id='btn-80', className='button-5', n_clicks=0),
        html.Button('60%', id='btn-60', className='button-5', n_clicks=0),
        html.Button('40%', id='btn-40', className='button-5', n_clicks=0),
        html.Button('20%', id='btn-20', className='button-5', n_clicks=0),
    ], style={'padding': '2%', 'textAlign': 'center'}),

    html.Div([
        dcc.Graph(id='3d-scatter-graph')
    ], id='plots-container3', style={'padding': '2%', 'textAlign': 'center'}),

], className='mainpol')

#GRAPH 1 - SUNBURST GRAPH
@callback(
    Output('sunburst-graph-pol', 'figure'),
    Input('grouping-options-pol', 'value')
)
def update_pol_sunburst(selected_gr):
    if not selected_gr:
        selected_gr = ['Team']
    else:
        selected_gr = selected_gr

    df_unique = df_final.drop_duplicates()

    fig = px.sunburst(df_unique, path = selected_gr, values = 'MedalCount',
                      color = 'Medal', color_discrete_map={'Gold': 'gold', 'Silver': 'silver', 'Bronze': 'peru'},
                  labels = {'MedalCount':'Liczba Medali'})
    
    fig.update_traces(textinfo='label+percent entry', insidetextorientation='radial')
    fig.update_layout(title='Rozkład zdobytych medali w zależności od profilu antropometrycznego<br /> polskich sportowców',
                  margin=dict(t=50, l=0, r=0, b=0),
                  paper_bgcolor = 'rgba(50, 50, 50, 0.9)', plot_bgcolor = 'rgba(250, 250, 250, 0.95)', font = dict(color = 'white'))
    

    return fig


#GRAPH 2 - BAR GRAPH
@callback(
    Output('bar-graph-pol-sex', 'figure'),
    Input('pol-scatter-bmibin', 'value')
)
def update_bar_pol_graph(selected):
    custom_colors = ['#800000', '#DAA520', '#006400', '#F5F5DC', '#FF69B4', '#FF4500', '#483D8B']

    # Tworzenie wykresu barplot
    fig = px.bar(df_final, x='Age Bin', y='MedalCount', color='BMI Bin', facet_row='Sex', barmode='group',
                category_orders={'Age Bin': ['1-20', '21-25', '26-30', '31-40']},
                title='Liczba zdobytych medali w zależności od wieku i BMI z podziałem na płeć',
                labels={'MedalCount': 'Liczba medali'},
                color_discrete_sequence=custom_colors)  # Ustawienie własnej palety kolorów

    # Personalizacja wykresu
    fig.update_layout(xaxis=dict(title='Przedział wiekowy'),
                    yaxis=dict(title='Liczba medali'),
                    legend=dict(title='BMI'),
                    paper_bgcolor = 'rgba(50, 50, 50, 0.9)', plot_bgcolor = 'rgba(250, 250, 250, 0.95)', font = dict(color = 'white'),
                    height = 550)
    
    for row_idx, row_figs in enumerate(fig._grid_ref): 
        for col_idx, col_fig in enumerate(row_figs):
            fig.update_yaxes(row=row_idx+1, col=col_idx+1,
                    matches = 'y'+str(len(row_figs)*row_idx+1))
            
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    
    return fig


#GRAPH 3 - TREE GRAPH
@callback(
    Output('tree-graph-pol', 'figure'),
    Input('grouping-options-pol-tree', 'value')
)
def update_tree_graph_pol(selected):
    if not selected:
        selected = ['Team', 'Sport', 'Medal']
    else:
        selected = selected

    fig = px.treemap(df_final, path=['Team', 'Sport', 'Sex', 'Age Bin', 'BMI Bin', 'Medal'], values='MedalCount', labels={'MedalCount':'Liczba Medali'})

# Personalizacja wykresu
    fig.update_traces(textinfo='label+percent entry')
    fig.update_layout(title='Rozkład zdobytych medali w zależności od profilu antropometrycznego sportowców', height = 650,
                    margin=dict(t=50, l=0, r=0, b=0), paper_bgcolor = 'rgba(50, 50, 50, 0.9)', plot_bgcolor = 'rgba(250, 250, 250, 0.95)', font = dict(color = 'white'))
    
    return fig


#GRAPH 4 - SCATTER
@callback(
    Output('scatter-graph-pol', 'figure'),
    [Input('pol-scatter-sport', 'value'), Input('pol-scatter-agebin', 'value'), Input('pol-scatter-bmibin', 'value')]
)
def update_scatter_pol(selected_sport, selected_age, selected_bmi):
    if not selected_sport:
        selected_sport = ['Athletics', 'Canoeing', 'Fencing', 'Gymnastics', 'Rowing']
    if not selected_age:
        selected_age = ['1-20', '21-25', '26-30', '31-40']
    if not selected_bmi:
        selected_bmi = ['18.51-20.56', '20.57-22.61', '28.76-30.8', '26.71-28.75', '22.62-24.66', '30.81-32.85', '24.67-26.7']

    filtered_df = df_final[df_final['Sport'].isin(selected_sport)]
    filtered_df = filtered_df[filtered_df['Age Bin'].isin(selected_age)]
    filtered_df = filtered_df[filtered_df['BMI Bin'].isin(selected_bmi)]
    
    fig = px.scatter(filtered_df, x='Age', y='BMI', color='Medal', size='Weight', symbol='Sex',
                 color_discrete_map={'Gold': '#cc9900', 'Silver': 'silver', 'Bronze':'peru'},
                 symbol_map={'Male': 'diamond', 'Female': 'circle'},
                 title='Zależność między wiekiem a BMI sportowca', labels={'Age Bin': 'Przedział wiekowy', 'BMI Bin': 'BMI'})

# Personalizacja wykresu
    fig.update_layout(xaxis=dict(title='Przedział wiekowy'), height = 600,
                    yaxis=dict(title='BMI'), paper_bgcolor = 'rgba(50, 50, 50, 0.9)', plot_bgcolor = 'rgba(250, 250, 250, 0.95)', font = dict(color = 'white'))
    
    return fig


#GRAPH 5 - PARALLEL COORDINATES
@callback(
    Output('parallel-graph', 'figure'),
    Input('parallel-options', 'value')
)
def update_parallel(selected):
    if not selected:
        selected = ['Sport', 'Age','Medal', 'BMI', 'Sex']
    elif len(selected) == 1:
        if selected[0] == 'BMI':
            selected = selected + ['Medal']
        else:
            selected = selected + ['BMI']

    dimensions = []

    if 'Sport' in selected:
        dimensions.append(
            dict(range=[np.min(sport_values), np.max(sport_values)],
                label='Sport', values=df_final['Sport'].map(sport_mapping),
                tickvals=list(sport_mapping.values()), ticktext=list(sport_mapping.keys()))
        )

    if 'Age' in selected:
        dimensions.append(
            dict(range=[int(np.min(df_final['Age'])), int(np.max(df_final['Age']))],
                label='Age', values=df_final['Age'])
        )

    if 'Medal' in selected:
        dimensions.append(
            dict(range=[np.min(medal_values), np.max(medal_values)],
                label='Medal', values=df_final['Medal'].map(medal_mapping),
                tickvals=list(medal_mapping.values()), ticktext=list(medal_mapping.keys()))
        )

    if 'BMI' in selected:
        dimensions.append(
            dict(range=[int(np.min(df_final['BMI'])) - 1, int(np.max(df_final['BMI'])) + 1],
                label='BMI', values=df_final['BMI'])
        )

    if 'Sex' in selected:
        dimensions.append(
            dict(range=[np.min(sex_values), np.max(sex_values)],
                label='Sex', values=df_final['Sex'].map(sex_mapping),
                tickvals=list(sex_mapping.values()), ticktext=list(sex_mapping.keys()))
        )

    fig = go.Figure(
        data=go.Parcoords(
            line=dict(
                color=df_final['BMI'],
                #colorscale=px.colors.diverging.Tealrose,
                colorscale = px.colors.sequential.PuRd[::-1],
                showscale = True,
                cmin=cminv, cmax=cmaxv
            ),
            dimensions=dimensions
        )
    )

    fig.update_layout(
        paper_bgcolor='rgba(50, 50, 50, 0.9)', 
        plot_bgcolor='rgba(250, 250, 250, 0.95)', 
        font=dict(color='white'),
        title_font=dict(size=20, color='white'),
        height = 650
    )

    return fig

@callback(
    Output('3d-scatter-graph', 'figure'),
    [Input('btn-100', 'n_clicks'),
     Input('btn-80', 'n_clicks'),
     Input('btn-60', 'n_clicks'),
     Input('btn-40', 'n_clicks'),
     Input('btn-20', 'n_clicks')]
)
def update_3d_scatter(n_btn_100, n_btn_80, n_btn_60, n_btn_40, n_btn_20):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'btn-20'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    model = joblib.load('assets/models/model_sc3.joblib')

    if button_id == 'btn-100':
        percentage = 100
    elif button_id == 'btn-80':
        percentage = 80
    elif button_id == 'btn-60':
        percentage = 60
    elif button_id == 'btn-40':
        percentage = 40
    elif button_id == 'btn-20':
        percentage = 20
    else:
        raise PreventUpdate
    
    print(f"Percentage: {percentage}")
    
    num_rows = int(len(X)*percentage / 100)

    sample_indices = X.sample(n=num_rows, random_state=42).index
    X_subset = X.loc[sample_indices]
    y_subset = y.loc[sample_indices]
    X_sport_subset = X_sport.loc[sample_indices]

    y_pred = model.predict(X_subset)

    accuracy = accuracy_score(y_subset, y_pred)

    results = pd.DataFrame({'Sport': X_sport_subset['Sport'],
                           'Sex_Encoded': X_subset['Sex_Encoded'],
                           'Height': X_subset['Height'],
                           'Weight': X_subset['Weight'],
                           'Age': X_subset['Age'],
                           'BMI': X_subset['BMI'],
                           'Actual': y_subset,
                           'Predicted': y_pred})
    
    results['Actual'] = results['Actual'].apply(lambda x: 'Medal' if x == 1 else 'No medal')
    results['Predicted'] = results['Predicted'].apply(lambda x: 'Medal' if x == 1 else 'No medal')
    results['Sex_Encoded'] = results['Sex_Encoded'].apply(lambda x: 'Mężczyzna' if x == 1 else 'Kobieta')

    fig = px.scatter_3d(results, x='Height', y='Weight', z='Age', color='Actual', symbol='Predicted', opacity=0.5, 
                    title=f"Wartości rzeczywiste i przewidywane w zależności od cech antropometrycznych - {np.round(accuracy, 2)}",
                    hover_data=['Actual', 'Predicted', 'Sport', 'Sex_Encoded', 'Height', 'Weight', 'Age'],
                    labels={'Height': 'Wzrost', 'Weight': 'Waga', 'Age': 'Wiek', 'Actual': 'Wartość rzeczywista', 'Predicted': 'Wartość przewidywana', 'Sport':'Dyscyplina', 'Sex_Encoded':'Płeć'})

    # Dostosowanie wyglądu wykresu
    fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', 
                    plot_bgcolor='rgba(250, 250, 250, 0.95)', 
                    font=dict(color='white'),
                    width = 1800, height = 850)

    # Dostosowanie legendy
    fig.update_traces(marker=dict(color=color_good_pred, symbol='circle'), selector=dict(mode='markers', name='Medal, Medal'))
    fig.update_traces(marker=dict(color=color_good_pred, symbol='diamond'), selector=dict(mode='markers', name='No medal, No medal'))
    fig.update_traces(marker=dict(color=color_bad_pred, symbol='diamond'), selector=dict(mode='markers', name='No medal, Medal'))
    fig.update_traces(marker=dict(color=color_bad_pred, symbol='circle'), selector=dict(mode='markers', name='Medal, No medal'))

    # Dodanie legendy
    fig.update_layout(legend_title="Legenda",
                    legend=dict(
                        title="Legenda",
                        itemsizing='constant',
                        orientation='h',
                        yanchor='bottom',
                        y=1,
                        xanchor='right',
                        x=1
                    ))
    return fig
