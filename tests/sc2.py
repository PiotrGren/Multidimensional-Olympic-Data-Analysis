from dash.dependencies import State
import pandas as pd
import math
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
import pyspark.pandas as psd
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

except Exception as e:
    print(f"Wystąpił błąd podczas próby wczytania danych:\n\n{e}")




df_kpi2 = df.filter(col('Medal') != 'No medal') \
    .filter(col('Century') == 21) \
    .groupBy('Year', 'Season', 'Sport', 'Medal', 'Sex', 'Age Bin') \
    .agg(count('Sport').alias('Sport_Count')) \
    .orderBy(desc('Sport_Count'))

top_sports = df_kpi2.filter(col('Season') == 'Summer').select('Sport').distinct().limit(3)
top_sports = top_sports.union(df_kpi2.filter(col('Season') == 'Winter').select('Sport').distinct().limit(3))

df_kpi_result = df.filter(col('Medal') != 'No medal') \
    .filter(col('Century') == 21) \
    .join(top_sports, 'Sport', 'inner') \
    .groupBy('Year', 'Season', 'Sport', 'Medal', 'Sex', 'Age Bin') \
    .agg(count('Medal').alias('MedalCount')) \
    .orderBy('Year', 'Season', 'Sport')

#df_kpi_result.show(10)
df_rd = df_kpi_result.toPandas()

df_rd_winter = df_kpi_result.filter(col('Season') == 'Winter')
df_rd_summer = df_kpi_result.filter(col('Season') == 'Summer')

df_rd_winter = df_rd_winter.toPandas()
df_rd_summer = df_rd_summer.toPandas()

df_avg_age = df.filter(col('Medal') != 'No medal') \
               .filter(col('Century') == 21) \
               .join(top_sports, 'Sport', 'inner') \
               .groupBy('Year', 'Season', 'Sport', 'Sex') \
               .agg(round(avg('Age'), 2).alias('Average Age')) \
               .orderBy('Year', 'Season', 'Sport')

df_avg = df_avg_age.toPandas()

def find_age_bin(age, age_bins):
    age = math.floor(age)
    for bin_range in age_bins:
        bin_min, bin_max = [int(x) for x in bin_range.split('-')]
        if bin_min <= age <= bin_max:
            return bin_range
    return None

# Uzyskanie unikalnych przedziałów wiekowych
age_bins = [row['Age Bin'] for row in df.select('Age Bin').distinct().collect()]

# Dodanie kolumny z przedziałem wiekowym do df_avg
df_avg['Age Bin'] = df_avg['Average Age'].apply(lambda x: find_age_bin(x, age_bins))

# Ustalenie najczęściej zdobywanego medalu
df_kpi_result = df.filter(col('Medal') != 'No medal') \
    .join(top_sports, 'Sport', 'inner') \
    .groupBy('Sport', 'Medal', 'Sex', 'Age Bin') \
    .agg(count('Medal').alias('MedalCount')) \
    .orderBy('Sport', 'Sex')

df_common_medal = df_kpi_result.withColumn('Gold', when(col('Medal') == 'Gold', col('MedalCount')).otherwise(0)) \
    .withColumn('Silver', when(col('Medal') == 'Silver', col('MedalCount')).otherwise(0)) \
    .withColumn('Bronze', when(col('Medal') == 'Bronze', col('MedalCount')).otherwise(0))

# Sumowanie ilości medali dla każdego koloru
df_common_medal = df_common_medal.groupBy('Sport', 'Sex', 'Age Bin') \
    .agg({'Gold': 'sum', 'Silver': 'sum', 'Bronze': 'sum'}) \
    .withColumnRenamed('sum(Gold)', 'Gold') \
    .withColumnRenamed('sum(Silver)', 'Silver') \
    .withColumnRenamed('sum(Bronze)', 'Bronze')

df_common_medal = df_common_medal.withColumn('MedalCount', col('Gold') + col('Silver') + col('Bronze'))

# Tworzenie kolumny z najczęstszym medalem
df_common_medal = df_common_medal.withColumn('MostCommonMedal', 
                                             when((col('Gold') >= col('Silver')) & (col('Gold') >= col('Bronze')), 'Gold')
                                             .when((col('Silver') >= col('Gold')) & (col('Silver') >= col('Bronze')), 'Silver')
                                             .otherwise('Bronze'))
df_common = df_common_medal.toPandas()

df_result = pd.merge(df_avg, df_common[['Sport', 'Sex', 'Age Bin', 'MostCommonMedal']],
                     on=['Sport', 'Sex', 'Age Bin'], how='left')


medal_colors = {'Gold': 'gold', 'Silver': 'silver', 'Bronze': 'peru'}
colors_list = {'Alpine Skiing':'#19b3b3','Biathlon':'#c2c20a', 'Ice Hockey': '#003300',
               'Boxing':'#950434', 'Gymnastics':'#cc9900', 'Tennis': '#138613'}

df_winter = df_result[df_result['Season'] == 'Winter']
df_summer = df_result[df_result['Season'] == 'Summer']



app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)

# Definiowanie layoutu aplikacji Dash
app.layout = html.Div(children=[
    html.H1(children='Dashboard Scenariusz 2: Zdobyte medale - analiza wzorców wiekowych w najpopularniejszych dyscyplinach sezonowych XXI w.', style = {'font-family':'Helvetica', 'padding':'2%'}),
    html.Div([
        html.Label('Dyscyplina sportowa:'),
        dcc.Checklist(
            id='grouping-options',
            options=[
                {'label': 'Narciarstwo Alpejskie', 'value': 'Alpine Skiing'},
                {'label': 'Biathlon', 'value': 'Biathlon'},
                {'label': 'Hokej na lodzie', 'value': 'Ice Hockey'},
                {'label': 'Boks', 'value': 'Boxing'},
                {'label': 'Gimnastyka', 'value': 'Gymnastics'},
                {'label': 'Tenis', 'value': 'Tennis'},
            ],
            value=['Alpine Skiing', 'Biathlon', 'Ice Hockey', 'Boxing', 'Gymnastics', 'Tennis'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        html.Label('Płeć:'),
        dcc.Checklist(
            id='gender-options',
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
            id='common-options',
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
            id='pie-graph'
        )
    ], style={'width':'45%', 'float': 'left', 'margin':'2%'}, className = 'checkbox-wrapper-2'),
    
    html.Div([
        html.Label('Wybierz dane wykresu:'),
        dcc.Checklist(
            id='data-options',
            options=[
                {'label': 'Rok', 'value': 'Year'},
                {'label': 'Sezon', 'value': 'Season'},
                {'label': 'Dyscyplina sportowa', 'value': 'Sport'},
                {'label': 'Medal', 'value': 'Medal'},
                {'label': 'Płeć', 'value': 'Sex'},
                {'label': 'Przedział wiekowy', 'value': 'Age Bin'},
            ],
            value=['Year', 'Sport', 'Medal'],
            inline=True,
            style = {'font-family':'Helvetica', 'font-size':'15px'},
            inputStyle={'font-family': 'Helvetica', 'border-radius':'5px'},
            inputClassName = 'sc-gJwTLC ikxBAC'
        ),

        dcc.Graph(
            id='sunburst-graph'
        )

    ], style={'width':'45%', 'float': 'right', 'margin':'2%'}, className = 'checkbox-wrapper-2'),

    html.Div([
        dcc.Graph(id='scatter-winter-graph')
    ], style={'float': 'left', 'width': '47%', 'margin-left':'2%', 'margin-right':'1%', 'margin-bottom':'2%', 'clear':'both'}),

    html.Div([
        dcc.Graph(id='scatter-summer-graph')
    ], style={'float': 'right', 'width': '47%', 'margin-left':'1%', 'margin-right':'2%', 'margin-bottom':'2%'}),

    html.Div([
        dcc.Graph(id='line-winter-graph')
    ], style={'float': 'left', 'width': '47%', 'margin-left':'2%', 'margin-right':'1%', 'margin-bottom':'2%', 'clear':'both'}),

    html.Div([
        dcc.Graph(id='line-summer-graph')
    ], style={'float': 'right', 'width': '47%', 'margin-left':'1%', 'margin-right':'2%', 'margin-bottom':'2%'}),

    html.Div([
        dcc.Graph(id='bar-graph')
    ], style={'float': 'center', 'width': '95%', 'margin':'2%', 'clear':'both'}),
])



#GRAPH 1 - PIE CHART
@app.callback(
    Output('gender-options', 'value'),
    [Input('common-option', 'value')],
    [State('gender-options', 'value')]
)
def update_gender_options(common_value, current_gender_value):
    if common_value == ['Common']:
        return []
    else:
        return current_gender_value if current_gender_value else ['Male', 'Female']
    
@app.callback(
    Output('pie-graph', 'figure'),
    [Input('grouping-options', 'value'), Input('gender-options', 'value'), Input('common-options', 'value')]
)
def update_pie(selected_sports, selected_genders, common_option):
    if common_option == ['Common']:
        if not selected_sports:
            selected_sports = ['Alpine Skiing', 'Biathlon', 'Ice Hockey', 'Boxing', 'Gymnastics', 'Tennis']

        df = df_rd[df_rd['Sport'].isin(selected_sports)]
        title = 'Udział sportowców w określonych przedziałach wiekowych<br />w liczbie zdobytych medali'
        labels_column = 'Age Bin'
    else:
        if not selected_sports:
            selected_sports = ['Alpine Skiing', 'Biathlon', 'Ice Hockey', 'Boxing', 'Gymnastics', 'Tennis']
        if not selected_genders:
            selected_genders = ['Male', 'Female']

        df = df_rd[(df_rd['Sport'].isin(selected_sports)) & (df_rd['Sex'].isin(selected_genders))]
        title = 'Udział sportowców w określonych przedziałach wiekowych i płci w liczbie zdobytych medali'
        df['Age-Sex'] = df['Age Bin'] + ' (' + df['Sex'] + ')'
        labels_column = 'Age-Sex'

    age_bin_counts = df.groupby(labels_column)['MedalCount'].sum().reset_index()

    # Definiowanie niestandardowych kolorów
    colors_list = ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725']

    # Tworzenie wykresu kołowego
    fig_pie = px.pie(age_bin_counts, names=labels_column, values='MedalCount', title=title, labels = {'Age Bin': 'Przedział wiekowy', 'MedalCount': 'Liczba medali'})

    # Aktualizacja kolorów
    fig_pie.update_traces(marker=dict(colors=colors_list))

    fig_pie.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)',
                          font=dict(color='white'), legend_title='Przedział wiekowy')

    return fig_pie


#GRAPH 2 - SUNBURST
@app.callback(
    Output('sunburst-graph', 'figure'),
    Input('data-options', 'value')
)
def upgrade_sunburst_graph2(selected_data):
    if not selected_data:
        selected_data = ["Year", "Sport", "Medal"]

    fig = px.sunburst(df_rd, path=selected_data, values='MedalCount')
    fig.update_traces(textinfo='label+percent entry')
    fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', font=dict(color='white'))

    return fig


#GRAPH 3 - SCATTER WINTER
@app.callback(
    Output('scatter-winter-graph', 'figure'),
    Input('grouping-options', 'value')
)
def update_winter_scatter(selected_sports):
    filtered_df = df_rd_winter[df_rd_winter['Sport'].isin(selected_sports)] if selected_sports else df_rd_winter

    fig = px.scatter(filtered_df, x="Age Bin", y="MedalCount", size="MedalCount", color="Medal",
                     color_discrete_map={'Gold': 'gold', 'Silver': 'silver', 'Bronze': 'peru'},
                     hover_name="Sex", title="Zależność pomiędzy wiekiem, a osiągnięciami sportowca - sezon zimowy",
                     labels={"MedalCount": "Medal Count", "Age Bin": "Age Bin", "Medal": "Medal Type"})
    
    fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)',
                      font=dict(color='white'))
    
    return fig


#GRAPH 4 - SCATTER SUMMER
@app.callback(
    Output('scatter-summer-graph', 'figure'),
    Input('grouping-options', 'value')
)
def update_summer_scatter(selected_sports):
    filtered_df = df_rd_summer[df_rd_summer['Sport'].isin(selected_sports)] if selected_sports else df_rd_summer

    fig = px.scatter(filtered_df, x="Age Bin", y="MedalCount", size="MedalCount", color="Medal",
                     color_discrete_map={'Gold': 'gold', 'Silver': 'silver', 'Bronze': 'peru'},
                     hover_name="Sex", title="Zależność pomiędzy wiekiem, a osiągnięciami sportowca - sezon letni",
                     labels={"MedalCount": "Medal Count", "Age Bin": "Age Bin", "Medal": "Medal Type"})
    
    fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)',
                      font=dict(color='white'))
    return fig


#GRAPH 5 - LINE WINTER
@app.callback(
    Output('line-winter-graph', 'figure'),
    [Input('grouping-options', 'value'), Input('gender-options', 'value')]
)
def update_winter_line(selected_sports, selected_genders):
    if not selected_sports:
        selected_sports = ['Alpine Skiing', 'Biathlon', 'Ice Hockey', 'Boxing', 'Gymnastics', 'Tennis']
    if not selected_genders:
        selected_genders = ['Male', 'Female']

    filtered_df = df_winter[df_winter['Sport'].isin(selected_sports)] if selected_sports else df_winter
    filtered_df = filtered_df[filtered_df['Sex'].isin(selected_genders)] if selected_genders else filtered_df
    
    fig = px.line(filtered_df, x='Year', y='Average Age', color='Sport', line_dash='Sex', line_group='Sport',
                  markers=True, color_discrete_map=colors_list,
                  title='Średni wiek sportowców w sezonie zimowym na przestrzeni lat',
                  labels={'Year': 'Rok', 'Average Age': 'Średni wiek'})
    
    for trace in fig.data:
        trace.visible = True

    fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'))
    
    return fig


#GRAPH 6 - LINE SUMMER
@app.callback(
    Output('line-summer-graph', 'figure'),
    [Input('grouping-options', 'value'), Input('gender-options', 'value')]
)
def update_summer_line(selected_sports, selected_genders):
    if not selected_sports:
        selected_sports = ['Alpine Skiing', 'Biathlon', 'Ice Hockey', 'Boxing', 'Gymnastics', 'Tennis']
    if not selected_genders:
        selected_genders = ['Male', 'Female']

    filtered_df = df_summer[df_summer['Sport'].isin(selected_sports)] if selected_sports else df_summer
    filtered_df = filtered_df[filtered_df['Sex'].isin(selected_genders)] if selected_genders else filtered_df
    
    fig = px.line(filtered_df, x='Year', y='Average Age', color='Sport', line_dash='Sex', line_group='Sport',
                  markers=True, color_discrete_map=colors_list,
                  title='Średni wiek sportowców w sezonie letnim na przestrzeni lat',
                  labels={'Year': 'Rok', 'Average Age': 'Średni wiek'})
    
    for trace in fig.data:
        trace.visible = True

    fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'))
    
    return fig


#GRAPH 7 - BAR PLOT
@app.callback(
    Output('bar-graph', 'figure'),
    [Input('grouping-options', 'value'), Input('gender-options', 'value')]
)
def update_bar_graph(selected_sports, selected_genders):
    if not selected_sports:
        selected_sports = ['Alpine Skiing', 'Biathlon', 'Ice Hockey', 'Boxing', 'Gymnastics', 'Tennis']
    if not selected_genders:
        selected_genders = ['Male', 'Female']

    filtered_df = df_rd[df_rd['Sport'].isin(selected_sports) & df_rd['Sex'].isin(selected_genders)]
    
    fig = px.bar(filtered_df, x='Age Bin', y='MedalCount', color='Medal', barmode='stack', color_discrete_map={'Gold':'#ccad33', 'Silver':'Silver', 'Bronze':'peru'},
                 title='Liczba medali zdobytych przez grupy wiekowe', labels={'Age Bin': 'Grupa wiekowa', 'MedalCount': 'Liczba medali', 'Sport':'Dyscyplina', 'Sex':'Płeć'},  hover_data={'Sport': True, 'Sex': True})
    
    fig.update_layout(paper_bgcolor = 'rgba(50, 50, 50, 0.9)', plot_bgcolor = 'rgba(250, 250, 250, 0.95)', font = dict(color = 'white'), height = 700)
    
    return fig

app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

# Uruchomienie serwera
if __name__ == '__main__':
    app.run_server(debug=True)#, host = '0.0.0.0', port = 8050)