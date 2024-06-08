import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from keras.models import Sequential
from keras.layers import Dense
import plotly.express as px
import os
import tensorflow as tf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import plotly.express as px
import os
import kaleido
import plotly.io as pio
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
import os
import subprocess
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import plotly.express as px
import os
import kaleido
import plotly.io as pio
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import *
import os
import subprocess
from sklearn.svm import SVR
from prophet import Prophet


try:
    #subprocess.run(["set", "PYARROW_IGNORE_TIMEZONE=1"])

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



# Zakładam, że dane z MSSQL zostały wcześniej wczytane do ramki danych Pandas
olympic_data = df.toPandas()

# Przygotowanie danych: Agregacja liczby medali dla każdego kraju na poszczególnych igrzyskach
olympic_data['Medal Count'] = olympic_data['Medal'].apply(lambda x: 0 if x == 'No medal' else 1)

# Dodanie liczby sportowców
athlete_counts = olympic_data.groupby(['Year', 'Season', 'Continent'])['ID'].nunique().reset_index()
athlete_counts.rename(columns={'ID': 'Athlete Count'}, inplace=True)

# Obliczanie średniego wieku sportowców
avg_ages = olympic_data.groupby(['Year', 'Season', 'Continent'])['Age'].mean().reset_index()
avg_ages.rename(columns={'Age': 'Avg Age'}, inplace=True)

# Obliczanie średniego wzrostu sportowców
avg_height = olympic_data.groupby(['Year', 'Season', 'Continent'])['Height'].mean().reset_index()
avg_height.rename(columns={'Height': 'Avg Height'}, inplace=True)

# Obliczanie średniej wagi sportowców
avg_weight = olympic_data.groupby(['Year', 'Season', 'Continent'])['Weight'].mean().reset_index()
avg_weight.rename(columns={'Weight': 'Avg Weight'}, inplace=True)

# Łączenie danych
medal_counts = olympic_data.groupby(['Year', 'Season', 'Continent'])['Medal Count'].sum().reset_index()
combined_data = pd.merge(medal_counts, athlete_counts, on=['Year', 'Season', 'Continent'])
combined_data = pd.merge(combined_data, avg_ages, on=['Year', 'Season', 'Continent'])
combined_data = pd.merge(combined_data, avg_height, on=['Year', 'Season', 'Continent'])
combined_data = pd.merge(combined_data, avg_weight, on=['Year', 'Season', 'Continent'])

# Dodanie cech sezonowych (np. rok igrzysk jako cecha cykliczna)
combined_data['Year_sin'] = np.sin(2 * np.pi * combined_data['Year'] / np.max(combined_data['Year']))
combined_data['Year_cos'] = np.cos(2 * np.pi * combined_data['Year'] / np.max(combined_data['Year']))

# Podział danych na sezony
summer_data = combined_data[combined_data['Season'] == 'Summer']
winter_data = combined_data[combined_data['Season'] == 'Winter']

# Lista kontynentów
continents = olympic_data['Continent'].unique()

# Funkcja do trenowania modelu i przewidywania na przyszłe lata
def predict_future_medals(model, data, season, continent):
    data = data[data['Continent'] == continent]
    X = data[['Year', 'Year_sin', 'Year_cos', 'Athlete Count', 'Avg Age']].values
    y = data['Medal Count'].values
    
    model.fit(X, y)
    
    future_years = pd.DataFrame({'Year': [2020, 2024, 2028, 2032, 2036]})
    future_years['Year_sin'] = np.sin(2 * np.pi * future_years['Year'] / np.max(data['Year']))
    future_years['Year_cos'] = np.cos(2 * np.pi * future_years['Year'] / np.max(data['Year']))
    
    # Przypisanie przybliżonych wartości dla liczby sportowców i średniego wieku
    future_years['Athlete Count'] = data['Athlete Count'].mean()
    future_years['Avg Age'] = data['Avg Age'].mean()
    
    future_predictions = model.predict(future_years[['Year', 'Year_sin', 'Year_cos', 'Athlete Count', 'Avg Age']].values)
    
    # Łączenie danych historycznych z przewidywanymi
    future_results = pd.DataFrame({
        'Year': future_years['Year'],
        'Medal Count': future_predictions
    })
    
    results = pd.concat([data[['Year', 'Medal Count']], future_results])
    
    return results, future_results



# Generowanie przewidywań i wykresów dla każdego kontynentu i sezonu przy użyciu GradientBoostingRegressor
figures = []
for continent in continents:
    model = GradientBoostingRegressor(n_estimators=500, random_state=42)
    
    summer_results, future_summer_results = predict_future_medals(model, summer_data, 'Summer', continent)
    winter_results, future_winter_results = predict_future_medals(model, winter_data, 'Winter', continent)
    
    summer_fig = px.line(summer_results, x='Year', y='Medal Count', title=f'Sezon letni - {continent} - Gradient Boosting Regressor')
    winter_fig = px.line(winter_results, x='Year', y='Medal Count', title=f'Sezon zimowy - {continent} - Gradient Boosting Regressor')
    
    summer_fig.add_scatter(x=summer_results['Year'], y=summer_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=winter_results['Year'], y=winter_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    
    # Dodanie przewidywanych danych w innym kolorze
    summer_fig.add_scatter(x=future_summer_results['Year'], y=future_summer_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=future_winter_results['Year'], y=future_winter_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    
    # Zmiana tła i koloru tekstu
    summer_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    winter_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    
    figures.append((continent, 'Summer', summer_fig))
    figures.append((continent, 'Winter', winter_fig))

    summer_dir = os.path.join('Wykresy', continent)
    winter_dir = os.path.join('Wykresy', continent)

    os.makedirs(summer_dir, exist_ok=True)
    os.makedirs(winter_dir, exist_ok=True)
    
    summer_fig.write_image(os.path.join(summer_dir, 'summer_gradientboosting.png'))
    winter_fig.write_image(os.path.join(winter_dir, 'winter_gradientboosting.png'))


def predict_future_medals(data, season, continent):
    data = data[data['Continent'] == continent]
    X = data[['Year', 'Year_sin', 'Year_cos', 'Athlete Count', 'Avg Age']].values
    y = data['Medal Count'].values
    
    model = RandomForestRegressor(n_estimators=500, random_state=42)
    model.fit(X, y)
    
    future_years = pd.DataFrame({'Year': [2020, 2024, 2028, 2032, 2036]})
    future_years['Year_sin'] = np.sin(2 * np.pi * future_years['Year'] / np.max(data['Year']))
    future_years['Year_cos'] = np.cos(2 * np.pi * future_years['Year'] / np.max(data['Year']))
    
    # Przypisanie przybliżonych wartości dla liczby sportowców i średniego wieku
    future_years['Athlete Count'] = data['Athlete Count'].mean()
    future_years['Avg Age'] = data['Avg Age'].mean()
    
    future_predictions = model.predict(future_years[['Year', 'Year_sin', 'Year_cos', 'Athlete Count', 'Avg Age']].values)
    
    # Łączenie danych historycznych z przewidywanymi
    future_results = pd.DataFrame({
        'Year': future_years['Year'],
        'Medal Count': future_predictions
    })
    
    results = pd.concat([data[['Year', 'Medal Count']], future_results])
    
    return results, future_results


# Generowanie przewidywań i wykresów dla każdego kontynentu i sezonu
figures = []
for continent in continents:
    summer_results, future_summer_results = predict_future_medals(summer_data, 'Summer', continent)
    winter_results, future_winter_results = predict_future_medals(winter_data, 'Winter', continent)
    
    summer_fig = px.line(summer_results, x='Year', y='Medal Count', title=f'Sezon letni - {continent} - Random Forest')
    winter_fig = px.line(winter_results, x='Year', y='Medal Count', title=f'Sezon zimowy - {continent} - Random Forest')
    
    summer_fig.add_scatter(x=summer_results['Year'], y=summer_results['Medal Count'],
                        mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=winter_results['Year'], y=winter_results['Medal Count'],
                        mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))

    # Dodanie punktów danych
    summer_fig.update_traces(mode='lines+markers', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4),  marker=dict(size=10), selector=dict(mode='lines'))
    winter_fig.update_traces(mode='lines+markers', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10), selector=dict(mode='lines'))
    
    # Dodanie przewidywanych danych w innym kolorze
    summer_fig.add_scatter(x=future_summer_results['Year'], y=future_summer_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4),  marker=dict(size=10))
    winter_fig.add_scatter(x=future_winter_results['Year'], y=future_winter_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4),  marker=dict(size=10))
    
    # Zmiana tła i koloru tekstu
    summer_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    winter_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    
    figures.append((continent, 'Summer', summer_fig))
    figures.append((continent, 'Winter', winter_fig))

    summer_dir = os.path.join('Wykresy', continent)
    winter_dir = os.path.join('Wykresy', continent)

    os.makedirs(summer_dir, exist_ok=True)
    os.makedirs(winter_dir, exist_ok=True)
    
    summer_fig.write_image(os.path.join(summer_dir, 'summer_randomforest.png'))
    winter_fig.write_image(os.path.join(winter_dir, 'winter_randomforest.png'))


from statsmodels.tsa.arima.model import ARIMA

def prepare_data_for_arima(data):
    # Prepare the data in the format required by ARIMA
    data = data[['Year', 'Medal Count']].set_index('Year')
    return data

def predict_future_medals_arima(data, season, continent):
    data = data[data['Continent'] == continent]
    arima_data = prepare_data_for_arima(data)
    
    # Fit ARIMA model
    model = ARIMA(arima_data, order=(5, 1, 0))
    model_fit = model.fit()
    
    # Predict future medals
    future_years = [2020, 2024, 2028, 2032, 2036]
    forecast = model_fit.forecast(steps=len(future_years))
    
    # Combine historical and future predictions
    historical_results = arima_data.reset_index()
    future_results = pd.DataFrame({'Year': future_years, 'Medal Count': forecast})
    
    results = pd.concat([historical_results, future_results], ignore_index=True)
    
    return results, future_results

# Generowanie przewidywań i wykresów dla każdego kontynentu i sezonu przy użyciu ARIMA
figures = []
for continent in continents:
    summer_results, future_summer_results = predict_future_medals_arima(summer_data, 'Summer', continent)
    winter_results, future_winter_results = predict_future_medals_arima(winter_data, 'Winter', continent)
    
    summer_fig = px.line(summer_results, x='Year', y='Medal Count', title=f'Sezon letni - {continent} - ARIMA')
    winter_fig = px.line(winter_results, x='Year', y='Medal Count', title=f'Sezon zimowy - {continent} - ARIMA')
    
    summer_fig.add_scatter(x=summer_results['Year'], y=summer_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=winter_results['Year'], y=winter_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    
    # Dodanie przewidywanych danych w innym kolorze
    summer_fig.add_scatter(x=future_summer_results['Year'], y=future_summer_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=future_winter_results['Year'], y=future_winter_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    
    # Zmiana tła i koloru tekstu
    summer_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    winter_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    
    figures.append((continent, 'Summer', summer_fig))
    figures.append((continent, 'Winter', winter_fig))

    summer_dir = os.path.join('Wykresy', continent)
    winter_dir = os.path.join('Wykresy', continent)

    os.makedirs(summer_dir, exist_ok=True)
    os.makedirs(winter_dir, exist_ok=True)
    
    summer_fig.write_image(os.path.join(summer_dir, 'summer_arima.png'))
    winter_fig.write_image(os.path.join(winter_dir, 'winter_arima.png'))

'''
def prepare_data_for_prophet(data):
    # Prepare the data in the format required by Prophet
    data = data[['Year', 'Medal Count']].rename(columns={'Year': 'ds', 'Medal Count': 'y'})
    return data

def predict_future_medals_prophet(data, season, continent):
    data = data[data['Continent'] == continent]
    prophet_data = prepare_data_for_prophet(data)
    
    model = Prophet()
    model.fit(prophet_data)
    
    future = model.make_future_dataframe(periods=5, freq='Y')
    forecast = model.predict(future)
    
    results = prophet_data.copy()
    future_results = forecast[['ds', 'yhat']].rename(columns={'ds': 'Year', 'yhat': 'Medal Count'})
    
    results = pd.concat([results.rename(columns={'ds': 'Year', 'y': 'Medal Count'}), future_results])
    results = results.drop_duplicates(subset=['Year'], keep='last')
    
    return results, future_results

# Generowanie przewidywań i wykresów dla każdego kontynentu i sezonu przy użyciu Prophet
figures = []
for continent in continents:
    summer_results, future_summer_results = predict_future_medals_prophet(summer_data, 'Summer', continent)
    winter_results, future_winter_results = predict_future_medals_prophet(winter_data, 'Winter', continent)
    
    summer_fig = px.line(summer_results, x='Year', y='Medal Count', title=f'Przewidywanie liczby medali w czasie - sezon letni - {continent}')
    winter_fig = px.line(winter_results, x='Year', y='Medal Count', title=f'Przewidywanie liczby medali w czasie - sezon zimowy - {continent}')
    
    summer_fig.add_scatter(x=summer_results['Year'], y=summer_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=winter_results['Year'], y=winter_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    
    # Dodanie przewidywanych danych w innym kolorze
    summer_fig.add_scatter(x=future_summer_results['Year'], y=future_summer_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=future_winter_results['Year'], y=future_winter_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    
    # Zmiana tła i koloru tekstu
    summer_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    winter_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    
    figures.append((continent, 'Summer', summer_fig))
    figures.append((continent, 'Winter', winter_fig))

    summer_dir = os.path.join('Wykresy', continent, 'Prophet')
    winter_dir = os.path.join('Wykresy', continent, 'Prophet')

    os.makedirs(summer_dir, exist_ok=True)
    os.makedirs(winter_dir, exist_ok=True)
    
    summer_fig.write_image(os.path.join(summer_dir, 'summer_prophet.png'))
    winter_fig.write_image(os.path.join(winter_dir, 'winter_prophet.png'))

# Wyświetlenie wykresów
for continent, season, fig in figures:
    fig.show()



# Funkcja do trenowania modelu sieci neuronowej i przewidywania na przyszłe lata
def predict_future_medals_nn(data, season, continent):
    data = data[data['Continent'] == continent]
    X = data[['Year', 'Year_sin', 'Year_cos', 'Athlete Count', 'Avg Age']].values
    y = data['Medal Count'].values
    
    # Budowa modelu sieci neuronowej
    model = Sequential()
    model.add(Dense(64, input_dim=X.shape[1], activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1, activation='linear'))
    model.compile(optimizer='adam', loss='mean_squared_error')
    
    model.fit(X, y, epochs=200, batch_size=10, verbose=0)
    
    future_years = pd.DataFrame({'Year': [2020, 2024, 2028, 2032, 2036]})
    future_years['Year_sin'] = np.sin(2 * np.pi * future_years['Year'] / np.max(data['Year']))
    future_years['Year_cos'] = np.cos(2 * np.pi * future_years['Year'] / np.max(data['Year']))
    
    # Przypisanie przybliżonych wartości dla liczby sportowców i średniego wieku
    future_years['Athlete Count'] = data['Athlete Count'].mean()
    future_years['Avg Age'] = data['Avg Age'].mean()
    
    future_predictions = model.predict(future_years[['Year', 'Year_sin', 'Year_cos', 'Athlete Count', 'Avg Age']].values)
    
    # Łączenie danych historycznych z przewidywanymi
    future_results = pd.DataFrame({
        'Year': future_years['Year'],
        'Medal Count': future_predictions.flatten()
    })
    
    results = pd.concat([data[['Year', 'Medal Count']], future_results])
    
    return results, future_results

# Generowanie przewidywań i wykresów dla każdego kontynentu i sezonu przy użyciu sieci neuronowej
for continent in continents:
    summer_results, future_summer_results = predict_future_medals_nn(summer_data, 'Summer', continent)
    winter_results, future_winter_results = predict_future_medals_nn(winter_data, 'Winter', continent)
    
    summer_fig = px.line(summer_results, x='Year', y='Medal Count', title=f'Przewidywanie liczby medali w czasie - sezon letni - {continent}')
    winter_fig = px.line(winter_results, x='Year', y='Medal Count', title=f'Przewidywanie liczby medali w czasie - sezon zimowy - {continent}')
    
    summer_fig.add_scatter(x=summer_results['Year'], y=summer_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=winter_results['Year'], y=winter_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    
    # Dodanie przewidywanych danych w innym kolorze
    summer_fig.add_scatter(x=future_summer_results['Year'], y=future_summer_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=future_winter_results['Year'], y=future_winter_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    
    # Zmiana tła i koloru tekstu
    summer_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    winter_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    
    figures.append((continent, 'Summer', summer_fig))
    figures.append((continent, 'Winter', winter_fig))

    summer_dir = os.path.join('Wykresy', continent)
    winter_dir = os.path.join('Wykresy', continent)

    os.makedirs(summer_dir, exist_ok=True)
    os.makedirs(winter_dir, exist_ok=True)
    
    summer_fig.write_image(os.path.join(summer_dir, 'summer_neuralnetwork.png'))
    winter_fig.write_image(os.path.join(winter_dir, 'winter_neuralnetwork.png'))




def predict_future_medals_svr(data, season, continent):
    data = data[data['Continent'] == continent]
    X = data[['Year', 'Year_sin', 'Year_cos', 'Athlete Count', 'Avg Age']].values
    y = data['Medal Count'].values
    
    model = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=0.1)
    model.fit(X, y)
    
    future_years = pd.DataFrame({'Year': [2020, 2024, 2028, 2032, 2036]})
    future_years['Year_sin'] = np.sin(2 * np.pi * future_years['Year'] / np.max(data['Year']))
    future_years['Year_cos'] = np.cos(2 * np.pi * future_years['Year'] / np.max(data['Year']))
    
    # Przypisanie przybliżonych wartości dla liczby sportowców i średniego wieku
    future_years['Athlete Count'] = data['Athlete Count'].mean()
    future_years['Avg Age'] = data['Avg Age'].mean()
    
    future_predictions = model.predict(future_years[['Year', 'Year_sin', 'Year_cos', 'Athlete Count', 'Avg Age']].values)
    
    # Łączenie danych historycznych z przewidywanymi
    future_results = pd.DataFrame({
        'Year': future_years['Year'],
        'Medal Count': future_predictions
    })
    
    results = pd.concat([data[['Year', 'Medal Count']], future_results])
    
    return results, future_results
figures = []
# Generowanie przewidywań i wykresów dla każdego kontynentu i sezonu przy użyciu SVR
for continent in continents:
    summer_results, future_summer_results = predict_future_medals_svr(summer_data, 'Summer', continent)
    winter_results, future_winter_results = predict_future_medals_svr(winter_data, 'Winter', continent)
    
    summer_fig = px.line(summer_results, x='Year', y='Medal Count', title=f'Przewidywanie liczby medali w czasie - sezon letni - {continent}')
    winter_fig = px.line(winter_results, x='Year', y='Medal Count', title=f'Przewidywanie liczby medali w czasie - sezon zimowy - {continent}')
    
    summer_fig.add_scatter(x=summer_results['Year'], y=summer_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=winter_results['Year'], y=winter_results['Medal Count'],
                           mode='lines+markers', name='Dane rzeczywiste', line=dict(color=px.colors.sequential.Aggrnyl[3], width=4), marker=dict(size=10))
    
    # Dodanie przewidywanych danych w innym kolorze
    summer_fig.add_scatter(x=future_summer_results['Year'], y=future_summer_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    winter_fig.add_scatter(x=future_winter_results['Year'], y=future_winter_results['Medal Count'],
                           mode='lines+markers', name='Przewidywanie', line=dict(color=px.colors.sequential.Reds[-3], width=4), marker=dict(size=10))
    
    # Zmiana tła i koloru tekstu
    summer_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    winter_fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', plot_bgcolor='rgba(250, 250, 250, 0.95)', font=dict(color='white'), xaxis_title='Rok', yaxis_title='Liczba medali')
    
    figures.append((continent, 'Summer', summer_fig))
    figures.append((continent, 'Winter', winter_fig))

    summer_dir = os.path.join('Wykresy', continent)
    winter_dir = os.path.join('Wykresy', continent)

    os.makedirs(summer_dir, exist_ok=True)
    os.makedirs(winter_dir, exist_ok=True)
    
    summer_fig.write_image(os.path.join(summer_dir, 'summer_svr.png'))
    winter_fig.write_image(os.path.join(winter_dir, 'winter_svr.png'))
    '''