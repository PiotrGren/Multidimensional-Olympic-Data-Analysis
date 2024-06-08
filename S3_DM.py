from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
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
from sklearn.ensemble import RandomForestClassifier
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

except Exception as e:
    print(f"Wystąpił błąd podczas próby wczytania danych:\n\n{e}")


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

df_final = df_kpi3.filter(col('Year') >= 1945).groupBy('Team', 'Sport', 'Sex','Height', 'Weight','Age', 'Age Bin','BMI', 'BMI Bin', 'Medal').agg(count('Medal').alias('MedalCount')).orderBy('Team', 'Sport', 'Sex')
df_final = df_final.withColumn('Team', when(df_final['Team'] == 'Poland-1', 'Poland').otherwise(df_final['Team']))

df_final = df_final.toPandas()

le = LabelEncoder()
df_final['Sport_Encoded'] = le.fit_transform(df_final['Sport'])

df_final.head(20)
df_final.info()




# Przekształcenie etykiet kolumny 'Medal' na 'No medal' lub 'Medal'
df_final['Medal'] = df_final['Medal'].apply(lambda x: 0 if x == 'No medal' else 1)
df_final['Sex_Encoded'] = le.fit_transform(df_final['Sex'])
df_final
# Podział danych na cechy (X) i etykiety (y)
X = df_final[['Sport_Encoded', 'Sex_Encoded', 'Height', 'Weight', 'Age', 'BMI']]
y = df_final['Medal']

# Zakodowanie etykiet kategorialnych cech za pomocą LabelEncodera
#le = LabelEncoder()
#X['Sport_Encoded'] = le.fit_transform(X['Sport_Encoded'])

# Podział danych na zbiory treningowy i testowy
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.9, random_state=42)
len(X_train)
len(X)

1440*0.9
# Tworzenie modelu klasyfikacji, np. Random Forest Classifier
model = RandomForestClassifier()

# Trenowanie modelu na danych treningowych
model.fit(X_train, y_train)

# Predykcja na danych testowych
y_pred = model.predict(X_test)
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.preprocessing import LabelEncoder

# Ewaluacja modelu
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, pos_label=1)
recall = recall_score(y_test, y_pred, pos_label=1)

print("Accuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)

import joblib

model_filename = f'assets/models/model_sc3.joblib'

joblib.dump(model, model_filename)


import plotly.express as px

# Stworzenie DataFrame z wartościami rzeczywistymi i przewidywanymi
df_results = pd.DataFrame({'Sport_Encoded': X_test['Sport_Encoded'],
                           'Sex_Encoded': X_test['Sex_Encoded'],
                           'Height': X_test['Height'],
                           'Weight': X_test['Weight'],
                           'Age': X_test['Age'],
                           'BMI': X_test['BMI'],
                           'Actual': y_test,
                           'Predicted': y_pred})

# Przekształcenie wartości etykiet na czytelne nazwy
df_results['Actual'] = df_results['Actual'].apply(lambda x: 'Medal' if x == 1 else 'No medal')
df_results['Predicted'] = df_results['Predicted'].apply(lambda x: 'Medal' if x == 1 else 'No medal')

# Definicja kolorów
color_good_pred = px.colors.sequential.Emrld[4]
color_bad_pred = px.colors.sequential.RdBu[2]

# Stworzenie interaktywnego wykresu za pomocą Plotly Express
fig = px.scatter_3d(df_results, x='Height', y='Weight', z='Age', color='Actual', symbol='Predicted', opacity=0.7, 
                    title="Wartości rzeczywiste i przewidywane w zależności od cech antropometrycznych",
                    labels={'Height': 'Wzrost', 'Weight': 'Waga', 'Age': 'Wiek', 'Actual': 'Wartość rzeczywista', 'Predicted': 'Wartość przewidywana'},
                    width=1100)

# Dostosowanie wyglądu wykresu
fig.update_layout(paper_bgcolor='rgba(50, 50, 50, 0.9)', 
                  plot_bgcolor='rgba(250, 250, 250, 0.95)', 
                  font=dict(color='white'))

# Dostosowanie legendy
fig.update_traces(marker=dict(color=color_good_pred, symbol='circle'), selector=dict(mode='markers', name='Medal, Medal'))
fig.update_traces(marker=dict(color=color_good_pred, symbol='diamond'), selector=dict(mode='markers', name='Brak medalu, Brak medalu'))
fig.update_traces(marker=dict(color=color_bad_pred, symbol='diamond'), selector=dict(mode='markers', name='Brak medalu, Medal'))
fig.update_traces(marker=dict(color=color_bad_pred, symbol='circle'), selector=dict(mode='markers', name='Medal, Brak medalu'))

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

# Wyświetlenie wykresu
fig.show()















# Importowanie niezbędnych bibliotek
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report

# Podział danych na cechy (X) i etykiety (y)
X = df_final[['Height', 'Weight', 'Age', 'BMI', 'Sport_Encoded']]
y = df_final['Medal']

# Podział danych na zbiór treningowy i testowy (80% treningowy, 20% testowy)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Inicjalizacja modelu drzewa decyzyjnego
model = DecisionTreeClassifier(random_state=42)

# Trenowanie modelu na danych treningowych
model.fit(X_train, y_train)

# Predykcja na zbiorze testowym
y_pred = model.predict(X_test)

# Ocena wydajności modelu
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print("Dokładność modelu:", accuracy)
print("Raport klasyfikacji:\n", report)

