import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
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
from sklearn.preprocessing import LabelEncoder

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


df_europe_gold_under_26 = df.filter((col('Medal') == 'Gold') &
                                    (col('Age') < 26) &
                                    (col('Continent') == 'Europe'))

df_gold_medal_counts = df_europe_gold_under_26.groupBy('Name').agg(count('Medal').alias('GoldMedalCount'))

df_selected_athletes = df_gold_medal_counts.filter(F.col('GoldMedalCount') >= 2)

df_final = df_selected_athletes.join(df_europe_gold_under_26, on='Name', how='inner') \
                               .select('Name', 'Sex', 'GoldMedalCount', 'Sport', 'Season', 'Age', 'Height', 'Weight', 'Continent', 'NOC', 'Year', 'Medal') \
                               .orderBy('Name', 'Year')

df_final = df_final.join(df_final.groupBy('Name').agg(F.countDistinct('Sport').alias('UniqueSports')), on='Name', how='inner')
df_final = df_final.filter(F.col('UniqueSports') == 1)

window = Window.partitionBy('Name')
df_final = df_final.withColumn('GoldMedalCount', F.count('Name').over(window))

unique_names = [row['Name'] for row in df_final.select('Name').distinct().collect()]


df_other_achievements = df.filter(col('Name').isin(unique_names) & (col('Medal') != 'Gold'))

# Podsumowanie innych osiągnięć dla każdego zawodnika
df_other_achievements_summary = df_other_achievements.groupBy('Name').agg(count('Medal').alias('OtherAchievementsCount'))

# Dołączenie informacji o innych osiągnięciach do ramki końcowej
df_final = df_final.join(df_other_achievements_summary, on='Name', how='left')

# Ustawienie wartości null na 0 dla braku innych osiągnięć
df_final = df_final.fillna(0, subset=['OtherAchievementsCount'])

# Wyświetlenie wyników
#df_final.show()

df_final = df_final.withColumn('Height', when(col('Height').isNull(), avg(col('Height')).over(Window.partitionBy('Sport'))) \
                                .otherwise(col('Height')))

df_final = df_final.withColumn('Weight', when(col('Weight').isNull(), avg(col('Weight')).over(Window.partitionBy('Sport'))) \
                                .otherwise(col('Weight')))

# Obliczenie BMI
df_final = df_final.withColumn('BMI', col('Weight') / (col('Height') / 100) ** 2)

# Wyświetlenie ramki danych po dodaniu informacji o wzroście, wadze i BMI
df_final = df_final.withColumn('Height', round(col('Height'), 2))
df_final = df_final.withColumn('Weight', round(col('Weight'), 2))
#df_final.show()




df_final_pd = df_final.toPandas()
df_final_pd

le = LabelEncoder()

for column in df_final_pd.columns:
    if df_final_pd[column].dtype == 'object':
        df_final_pd[column] = le.fit_transform(df_final_pd[column])

columns_to_drop = ['Name', 'NOC', 'Medal', 'UniqueSports', 'Continent']
df_final_pd.drop(columns=columns_to_drop, inplace=True)

df_final_pd = df_final_pd.dropna()
df_final_pd


import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from keras.models import Sequential
from keras.layers import Dense
from sklearn.metrics import mean_absolute_error


df_final_pd['AchievementCount'] = df_final_pd['GoldMedalCount'] + df_final_pd['OtherAchievementsCount']
df_final_pd
df = df_final_pd.drop(columns=['GoldMedalCount', 'OtherAchievementsCount'])

df = df.groupby('Year').agg({'AchievementCount': 'sum'}).reset_index()
df

# Podział na cechy (X) i etykiety (y)
X = df.drop(columns=['AchievementCount'])
y = df['AchievementCount']

# Standaryzacja danych
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Inicjalizacja modelu
model = Sequential()
model.add(Dense(64, input_dim=X_scaled.shape[1], activation='relu'))
model.add(Dense(32, activation='relu'))
model.add(Dense(1, activation='linear'))

# Kompilacja modelu
model.compile(loss='mean_squared_error', optimizer='adam')

# Trenowanie modelu
model.fit(X_scaled, y, epochs=100, batch_size=32, verbose=0)

# Przewidywanie na przyszłe 10 lat co 2 lata
future_years = np.arange(df['Year'].max() + 2, df['Year'].max() + 22, 2)
future_data = np.zeros((len(future_years), X_scaled.shape[1]))

for i, year in enumerate(future_years):
    future_data[i] = np.array([year] + [0] * (X_scaled.shape[1] - 1))  # Zakładamy brak innych danych

# Standaryzacja danych przyszłych
future_data_scaled = scaler.transform(future_data)

# Przewidywanie liczby osiągnięć dla przyszłych lat
predicted_values = model.predict(future_data_scaled).reshape(-1)

# Tworzenie wykresu
fig = go.Figure()

# Dodanie rzeczywistych danych
fig.add_trace(go.Scatter(x=df['Year'], y=y, mode='lines+markers', name='Dane historyczne', line=dict(color=px.colors.sequential.Viridis[3], width=3)))

# Dodanie przewidywań dla przyszłych lat
fig.add_trace(go.Scatter(x=future_years, y=predicted_values, mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Inferno[5], width=5)))

# Konfiguracja wykresu
fig.update_layout(title='Sieć Neuronowa',
                  xaxis_title='Rok',
                  yaxis_title='Liczba osiągnięć',
                  paper_bgcolor='rgba(50, 50, 50, 0.9)', 
                  plot_bgcolor='rgba(250, 250, 250, 0.95)', 
                  font=dict(color='white'), width = 1700, height = 600)

# Wyświetlenie wykresu
fig.show()

dir = os.path.join('assets/Wykresy/SC4')

os.makedirs(dir, exist_ok=True)
    
fig.write_image(os.path.join(dir, 'neuralnetwork.png'))


import pandas as pd
from prophet import Prophet
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error
import plotly.express as px

# Dodawanie wartości 'GoldMedalCount' i 'OtherAchievementsCount'
df_final_pd['AchievementCount'] = df_final_pd['GoldMedalCount'] + df_final_pd['OtherAchievementsCount']

# Agregowanie danych dla każdego roku
df_aggregated = df_final_pd.groupby('Year').agg({'AchievementCount': 'sum'}).reset_index()

# Konwersja kolumny 'Year' na datetime
df_aggregated['Year'] = pd.to_datetime(df_aggregated['Year'], format='%Y')

# Sortowanie według kolumny 'Year'
df_aggregated = df_aggregated.sort_values(by='Year')

# Przygotowanie danych do modelu
df_gold_other = df_aggregated[['Year', 'AchievementCount']].reset_index(drop=True)
df_gold_other.columns = ['ds', 'y']

# Funkcja oceny modelu
def score_func(y_true, y_pred):
    return mean_absolute_error(y_true, y_pred)

# Podział danych na zestawy treningowe i testowe oraz ewaluacja modelu
tscv = TimeSeriesSplit(n_splits=5)
scores = []

for train_index, test_index in tscv.split(df_gold_other):
    train_data = df_gold_other.iloc[train_index]
    test_data = df_gold_other.iloc[test_index]
    
    m = Prophet(yearly_seasonality=True)
    m.fit(train_data)
    
    future = m.make_future_dataframe(periods=len(test_data))
    forecast = m.predict(future)
    test_predictions = forecast.iloc[-len(test_data):][['yhat']]
   
    score = score_func(test_data[['y']], test_predictions)
    
    scores.append(score)

mean_score = sum(scores) / len(scores)
print(f'Mean Absolute Error (MAE) na danych testowych: {mean_score:.2f}')

# Trenowanie modelu na pełnych danych i przewidywanie na przyszłe 4 sezony olimpijskie
model = Prophet(yearly_seasonality=True)
model.fit(df_gold_other)

# Przewidywanie na przyszłe 4 sezony olimpijskie (2024, 2028, 2032, 2036)
future = model.make_future_dataframe(periods=10, freq='2Y')
forecast = model.predict(future)

# Łączenie rzeczywistych i przewidywanych danych
actual = df_gold_other.set_index('ds')
predicted = forecast.set_index('ds')[['yhat']]
results = actual.join(predicted, how='outer')

# Filtracja przewidywań tylko na przyszłe lata
future_predictions = results[results.index > actual.index.max()]

# Wizualizacja wyników
fig = px.scatter(results.reset_index(), x='ds', y='y', 
                 labels={'ds': 'Year', 'y': 'Achievement Count'},
                 title='Prophet')

# Add actual data as line with markers
fig.add_scatter(x=results.index, y=results['y'], mode='lines+markers', 
                name='Dane historyczne', line=dict(color=px.colors.sequential.Viridis[3], width=3))

# Add predictions as line with markers only for future years
fig.add_scatter(x=future_predictions.index, y=future_predictions['yhat'], mode='lines+markers', 
                name='Przewidywanie', line=dict(color=px.colors.sequential.Inferno[5], width=6))

fig.update_layout(
    xaxis_title='Rok',
    yaxis_title='Liczba osiągnięć',
    paper_bgcolor='rgba(50, 50, 50, 0.9)', 
    plot_bgcolor='rgba(250, 250, 250, 0.95)', 
    font=dict(color='white'), width = 1700, height = 600
)

fig.show()

dir = os.path.join('assets/Wykresy/SC4')

os.makedirs(dir, exist_ok=True)
    
fig.write_image(os.path.join(dir, 'prophet.png'))




import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import plotly.express as px
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error


# Ewaluacja modelu ARIMA
tscv = TimeSeriesSplit(n_splits=5)
scores = []

for train_index, test_index in tscv.split(df_gold_other):
    train_data = df_gold_other.iloc[train_index]
    test_data = df_gold_other.iloc[test_index]

    train_series = train_data.set_index('ds')['y']
    test_series = test_data.set_index('ds')['y']
    
    model = ARIMA(train_series, order=(5, 1, 0))
    model_fit = model.fit()
    
    forecast = model_fit.forecast(steps=len(test_series))
    
    score = mean_absolute_error(test_series, forecast)
    scores.append(score)

mean_score = np.mean(scores)
print(f'Mean Absolute Error (MAE) na danych testowych: {mean_score:.2f}')

# Trenowanie modelu ARIMA na pełnych danych i przewidywanie na przyszłe 8 okresów co 2 lata
train_series = df_gold_other.set_index('ds')['y']
model = ARIMA(train_series, order=(5, 1, 0))
model_fit = model.fit()

future_years = pd.date_range(start='2020', periods=8, freq='2Y')
forecast = model_fit.forecast(steps=8)

# Przygotowanie przewidywań do wizualizacji
future_df = pd.DataFrame({'ds': future_years, 'yhat': forecast})

# Łączenie rzeczywistych i przewidywanych danych
actual = df_gold_other.set_index('ds')
predicted = future_df.set_index('ds')
results = actual.join(predicted, how='outer')

# Wizualizacja wyników
fig = px.scatter(results.reset_index(), x='ds', y='y', 
                 labels={'ds': 'Year', 'y': 'Achievement Count'},
                 title='ARIMA')

# Dodanie rzeczywistych danych jako linia z markerami
fig.add_scatter(x=results.index, y=results['y'], mode='lines+markers', name='Dane historyczne', line=dict(color=px.colors.sequential.Viridis[3], width=3))

# Dodanie przewidywań jako linia z markerami tylko dla przyszłych lat
fig.add_scatter(x=predicted.index, y=predicted['yhat'], mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Inferno[5], width=6))

fig.update_layout(
    xaxis_title='Rok',
    yaxis_title='Liczba osiągnięć',
    paper_bgcolor='rgba(50, 50, 50, 0.9)', 
    plot_bgcolor='rgba(250, 250, 250, 0.95)', 
    font=dict(color='white'), width = 1700, height = 600
)

fig.show()

dir = os.path.join('assets/Wykresy/SC4')

os.makedirs(dir, exist_ok=True)
    
fig.write_image(os.path.join(dir, 'arima.png'))





