import pandas as pd

#Przepływ nr. 1. Importowanie Danych oraz czyszczenie ich
df = pd.read_csv("Dane/athlete_events.csv")

df.isnull().sum()
df.head()

df_cleaned = df.dropna(subset=['Age'])

print(df_cleaned.isnull().sum())
print(f"Rozmiar danych przed czyszczeniem: {len(df)}\nRozmiar danych po wyczyszczeniu: {len(df_cleaned)}")



#Przepływ nr. 2. Uzupełnianie brakujących danych wzrostu oraz wagi na podstawie zmiennych zależnych
df_cleaned['Height'] = df_cleaned.groupby('Sport')['Height'].apply(lambda x: x.fillna(x.mean()))


weight_means = df_cleaned.groupby(['Sport', 'Height'])['Weight'].transform('mean')
df_cleaned['Weight'] = df_cleaned['Weight'].fillna(weight_means)

df_cleaned['Weight'] = df_cleaned.groupby('Sport')['Weight'].apply(lambda x: x.fillna(x.mean()))

df_cleaned = df_cleaned.dropna(subset=['Height', 'Weight'])

df_cleaned.isnull().sum()



#Przepływ nr. 3. Transformacja danych - stworzenie grup wiekowych sportowców
bins = [i for i in range(0, 101, 10) if i != 10]

labels = [str(bins[i-1] + 1) + "-" + str(bins[i]) for i in range(1, len(bins))]

df_cleaned.insert(df_cleaned.columns.get_loc('Age') + 1, 'AgeGroup', pd.cut(df_cleaned['Age'], bins, labels=labels))

print(df_cleaned[['Name', 'Age', 'AgeGroup']].head())


#Przepływ nr. 4. Agregacja danych - zliczenie zdobytych medali według kraju
medals_by_country = df_cleaned[df_cleaned['Medal'].notna()].groupby('NOC')['Medal'].count().reset_index()

medals_by_country = medals_by_country.rename(columns={'Medal': 'MedalCount'})

print(medals_by_country)
print(len(medals_by_country))

df_cleaned = df_cleaned.merge(medals_by_country, on='NOC', how='left')

print(df_cleaned.head())


#Przepływ nr. 5. Analiza trendów - średni wiek sportowców w różnych dyscyplinach na przestrzeni lat
avg_age_per_sport_year = df_cleaned.groupby(['Year', 'Sport'])['Age'].mean().reset_index()

avg_age_per_sport_year.columns = ['Year', 'Sport', 'AvarageAge']
avg_age_per_sport_year['AvarageAge'] = round(avg_age_per_sport_year['AvarageAge'], 2)

df_cleaned = df_cleaned.merge(avg_age_per_sport_year, on=['Year', 'Sport'], how='left')



#Przepływ nr. 6. Wzbogacanie danych poprzez stworzenie nowej kolumny z kontynentami
continents = pd.read_csv("Dane/country-codes.csv")

continents.head()

present = 0
for noc in df_cleaned['NOC'].unique():
    if noc in continents['IOC'].values:
        present += 1

print("Wszystkie kody są dostępne") if present == len(df_cleaned['NOC'].unique()) else print("Brakuje kodów")    

country_to_continent = dict(zip(continents['IOC'], continents['Continent']))

df_cleaned.insert(df_cleaned.columns.get_loc('NOC') + 1, 'CC', df_cleaned['NOC'].map(country_to_continent))
df_cleaned['CC'].fillna('NA', inplace=True)

df_cleaned[['NOC', 'Team', 'CC']].head()
df_cleaned['CC'].unique()

code_to_name = {'AS': 'Asia', 'EU': 'Europe', "AF": 'Africa', 'SA': 'South America', 'NA': 'North America', 'OC': 'Oceania', 'UT': 'Unified Team'}
df_cleaned.insert(df_cleaned.columns.get_loc('CC'), 'Continent', df_cleaned['CC'].map(code_to_name))


df_cleaned[['NOC', 'Team', 'CC', 'Continent']].head()


#Zapis do pliku
df_cleaned.to_csv('olimpic_data_prepared.csv', index=False)

