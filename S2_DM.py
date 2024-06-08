import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.arima.model import ARIMA
import plotly.graph_objects as go
from dash.dependencies import State
import math
import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import dash_bootstrap_components as dbc
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
import os
import plotly.graph_objects as go
from sklearn.svm import SVR

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


#df_kpi_result.show(10)
df_avg_age = df.filter(col('Medal') != 'No medal') \
               .join(top_sports, 'Sport', 'inner') \
               .groupBy('Year', 'Season', 'Sport', 'Sex') \
               .agg(round(avg('Age'), 2).alias('Average Age')) \
               .orderBy('Year', 'Season', 'Sport', 'Sex')
#.filter(col('Century') == 21) \

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

df_result = df_result[df_result['Season'] == 'Summer']
df_result = df_result[df_result['Sport'].isin(['Gymnastics', 'Swimming', 'Athletics'])]

# Model 1: SVR
def svr_predict(df, sex):
    df_sex = df[df['Sex'] == sex]
    X = df_sex[['Year']]
    y = df_sex['Average Age']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Model Support Vector Regressor (SVR)
    svr_regressor = SVR(kernel='rbf')
    svr_regressor.fit(X_train, y_train)
    svr_pred = svr_regressor.predict(X_test)
    
    # Przewidywanie na przyszłość
    future_years = np.array([2020, 2024, 2028, 2032, 2036]).reshape(-1, 1)
    svr_future_pred = svr_regressor.predict(future_years)
    
    return future_years, svr_future_pred, svr_regressor

# Model 2: Random Forest
def random_forest_predict(df, sex):
    df_sex = df[df['Sex'] == sex]
    X = df_sex[['Year']]
    y = df_sex['Average Age']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    rand_forest = RandomForestRegressor(n_estimators=100, random_state=42)
    rand_forest.fit(X_train, y_train)
    rf_pred = rand_forest.predict(X_test)
    
    # Przewidywanie na przyszłość
    future_years = np.array([2020, 2024, 2028, 2032, 2036]).reshape(-1, 1)
    rf_future_pred = rand_forest.predict(future_years)
    
    return future_years, rf_future_pred, rand_forest

# Model 3: ARIMA
def arima_predict(df, sex):
    df_sex = df[df['Sex'] == sex]
    df_arima = df_sex.set_index('Year')
    arima_model = ARIMA(df_arima['Average Age'], order=(5, 1, 0))  # Dobór parametrów (p, d, q)
    arima_result = arima_model.fit()
    
    # Przewidywanie na przyszłość
    future_years = np.array([2020, 2024, 2028, 2032, 2036])
    arima_future_pred = arima_result.predict(start=len(df_arima), end=len(df_arima)+len(future_years)-1, typ='levels')
    
    return future_years, arima_future_pred, arima_model

# Przewidywania dla każdej płci
future_years_svr_m, svr_future_pred_m, _ = svr_predict(df_result, 'Male')
future_years_svr_f, svr_future_pred_f, _ = svr_predict(df_result, 'Female')

future_years_rf_m, rf_future_pred_m, _ = random_forest_predict(df_result, 'Male')
future_years_rf_f, rf_future_pred_f, _ = random_forest_predict(df_result, 'Female')

future_years_arima_m, arima_future_pred_m, _ = arima_predict(df_result, 'Male')
future_years_arima_f, arima_future_pred_f, _ = arima_predict(df_result, 'Female')


def create_scatter_plot(df, future_years_m, predictions_m, future_years_f, predictions_f, model_name):
    fig = go.Figure()
    
    # Rzeczywiste dane dla mężczyzn
    male_data = df[df['Sex'] == 'Male']
    fig.add_trace(go.Scatter(x=male_data['Year'], y=male_data['Average Age'], 
                             mode='markers+lines', name='Rzeczywiste dane (Mężczyźni)', marker_color=px.colors.sequential.tempo[-6], 
                             text=male_data['Average Age'], textposition='top center', marker_size=10))
    
    # Rzeczywiste dane dla kobiet
    female_data = df[df['Sex'] == 'Female']
    fig.add_trace(go.Scatter(x=female_data['Year'], y=female_data['Average Age'], 
                             mode='markers+lines', name='Rzeczywiste dane (Kobiety)', marker_color=px.colors.sequential.Plasma[4], 
                             text=female_data['Average Age'], textposition='bottom center', marker_size=10))
    
    # Przewidywania dla mężczyzn
    fig.add_trace(go.Scatter(x=future_years_m.flatten(), y=predictions_m, 
                             mode='markers+lines', name=f'Przewidywania (Mężczyźni)', marker_color=px.colors.sequential.OrRd[-2], 
                             text=np.round(predictions_m, 2), textposition='top left', marker_size=10))
    
    # Przewidywania dla kobiet
    fig.add_trace(go.Scatter(x=future_years_f.flatten(), y=predictions_f, 
                             mode='markers+lines', name=f'Przewidywania (Kobiety)', marker_color=px.colors.sequential.solar[-2], 
                             text=np.round(predictions_f, 2), textposition='bottom right', marker_size=10))
    
    fig.update_layout(
        title=f'Przewidywany średni wiek sportowców ({model_name})',
        xaxis_title='Rok',
        yaxis_title='Średni wiek',
        paper_bgcolor='rgba(50, 50, 50, 0.9)', 
        plot_bgcolor='rgba(250, 250, 250, 0.95)', 
        font=dict(color='white'),
        width = 1100
    )
    
    return fig

fig_svr = create_scatter_plot(df_result, future_years_svr_m, svr_future_pred_m, future_years_svr_f, svr_future_pred_f, 'Support Vector Regressor')
fig_rf_scatter = create_scatter_plot(df_result, future_years_rf_m, rf_future_pred_m, future_years_rf_f, rf_future_pred_f, 'Random Forest')
fig_arima_scatter = create_scatter_plot(df_result, future_years_arima_m, arima_future_pred_m, future_years_arima_f, arima_future_pred_f, 'ARIMA')

#fig_svr.show()
#fig_rf_scatter.show()
#fig_arima_scatter.show()


dir = os.path.join('assets/Wykresy/SC2')

os.makedirs(dir, exist_ok=True)
    
fig_svr.write_image(os.path.join(dir, 'svr.png'))
fig_rf_scatter.write_image(os.path.join(dir, 'randomforest.png'))
fig_arima_scatter.write_image(os.path.join(dir, 'arima.png'))