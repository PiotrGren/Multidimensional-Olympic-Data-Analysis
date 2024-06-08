**Choose your language / Wybierz język**

[EN](#english) / [PL](#polski)

#### English

# Multidimensional Olympic Data Analysis

## Table of Contents

1. [Description](#description)
2. [Required before use (important)](#required-before-use-(important))
3. [Data and ETL processes](#data-and-etl-processes)
4. [Docker and MS SQL Server](#docker-and-ms-sql-server)
5. [KPI File](#kpi-file)
6. [Dash Application](#dash-application)
7. [Data Mining](#data-mining)
8. [License](#license)
9. [Authors](#authors)

## Description



## Required before use (important)

If you want to run this project on your computer or create your own similar one, you must meet several requirements:

1. Make sure you have HADOOP installed on your computer. If not you can install it by following this tutorial:
   ```sh
   https://www.youtube.com/watch?v=knAS0w-jiUk
   ```

2. Make sure you have Apache Spark installed on your computer. If not you can install it by following this tutorial:
   ```sh
   https://www.youtube.com/watch?v=OmcSTQVkrvo
   ```
3. Make sure you have Docker Desktop installed on your computer. If not, you can install it by downloading the installer from the official Docker website:
   ```sh
   https://www.docker.com/products/docker-desktop/
   ```

4. Make sure you have docker compose module installed on your computer. If not, you can install it by following this tutorial:
   ```sh
   [WINDOWS] - https://www.ionos.com/digitalguide/server/configuration/install-docker-compose-on-windows/

   [LINUX] - https://gcore.com/learning/how-to-install-docker-compose-on-linux/
   ```
   
5. Make sure you have installed the required Python libraries used in the project. If not you can install them by downloading the `requirements.txt` file and running the following command:
   ```sh
   pip install -r requirements.txt
   ```
6. Clone the repository to your local computer:
   ```sh
   git clone https://github.com/PiotrGren/Multidimensional-Olympic-Data-Analysis
   cd Multidimensional-Olympic-Data-Analysis
   ```

## Data and ETL processes

The repository uses Olympic data, which can be found in a CSV file in the Dane/ directory. The main data files are:

 - athlete_events.csv: Contains information about athletes, Olympic events, achievements, etc. spanning the years 1890-2016.
 - country-codes.csv: Contains information about abbreviations of countries and the continents they are from (needed to create a new column with continents in the data frame used).

### ETL

ETL processes carried out on the original data frame loaded using the pandas library are carried out in the `ETL.ipynb` file. The file contains processes such as data transformation (e.g., converting M, F values in the Sex column to Male, Female, or converting ages to age ranges), generating new columns (e.g., by splitting the Games column, or adding a new column with continents, or converting the data type (e.g., from str to integer).

## Docker and MS SQL Server

### docker-compose.yml

The docker-compose.yml file in the repository is used to define and run multi-container applications using Docker. In this case, this file configures a container with Microsoft SQL Server.

**How to Run**

1 Make sure you have installed Docker Desktop and docker-compose correctly.
2.Make sure you have cloned the repository to your computer or created your own with your own docker-compose file and downloaded the `mssql-jdbc-12.6.1.jre8` driver (or your corresponding version).
3 Go to the folder with the docker-compose file.
   ```sh
   cd path/to/your/folder
   ```
4. Make sure you have Docker Engine running (run Docker Desktop on your computer).
5. Run docker-compose by running the command:
   ```sh
   docker-compose up
   ```
6. If you have run the process correctly, from now on, a new container should appear in Docker Desktop. From now on, you can start and stop it in the application.

### MS SQL Server

Microsoft SQL Server is a relational database management system (RDBMS) developed by Microsoft. It is used to store and manage data and supports a wide range of operations, including SQL queries, data analysis, report generation and integration with other applications.

In this project, MS SQL Server will be used to store processed Olympic data, which will then be used for analysis and visualization.

#### Benefits of running MS SQL Server in a container

1 **Isolation**: Containers isolate applications and their dependencies, allowing multiple versions of SQL Server to run side-by-side without conflicts.
2 **Portability**: Containers can be easily moved between different environments (e.g., development, test and production).
3. **Speed of deployment**: Containers allow rapid deployment and scaling of applications.
4. **Consistency**: Using containers ensures that the application runs the same in all environments, eliminating system configuration issues.

### Python files to start with

1. **CREATE_DATABASE.py** - This script is used to create a database in MS SQL Server. It executes SQL statements that create a new database and then creates the tables needed to store the Olympic data.

2. **LOAD_DATA.py** - This script loads the processed data into the MS SQL Server database. It uses the pandas library to load the data from the CSV files and then writes it to the appropriate tables in the database.

3. **CHECK_DATABASE.py** - This script checks whether the database exists, and whether it contains the required tables. This is useful for verifying the state of the database before starting data operations.

4. **DROP_DATABASE_OPTIONAL.py** = This is an optional script that removes the database if it exists. This is useful for cleaning up the environment before restarting ETL processes or testing or deleting the database if you make a mistake or break something.

## KPI File

The KPI.ipynb file is a Jupyter notebook that is used to perform major analysis of Olympic data in the project. In this file, various multivariate analyses are performed to understand the key indicators related to the participation and performance of athletes in the Olympic Games. The analysis is carried out divided into 4 scenarios, respectively:

1. **Scenario 1**: Athletes' achievements gained - continental analysis.
2. **Scenario 2**: Medals won - analysis of age patterns in the most popular seasonal sports of the 21st century.
3. **Scenario 3**: Analysis of the anthropometric profile of Polish athletes in the context of their achievements at the Olympic Games after World War II.
4. **Scenario 4**: Analysis of patterns among double gold medalists from Europe who won double gold in one sport.

### Purpose and content

The KPI.ipynb file is used to perform preliminary data analysis and test various scenarios that are later implemented in the Dash application. It is a test file that allows you to experiment with data and create and visualize various metrics and anaiz before their final implementation.

Each scenario is analyzed in detail, and the results are visualized using charts and tables. As a result of these analyses, preliminary versions of charts and reports are created, which serve as the basis for further development and implementation in the Dash application.

### Remember

Keep in mind that KPI.ipynb is a test file that is used to experiment and test different approaches to data analysis. The final versions of all analytical processes and charts created and run in this file are included in the Dash application. The Dash app integrates these analyses into an interactive and user-friendly environment, allowing dynamic viewing and analysis of Olympic data.

The KPI.ipynb file plays a key role in the project lifecycle, enabling rapid prototyping and testing of ideas, which are then transferred to the final Dash application.

## Dash application

The Dash application in this project is an interactive platform for visualizing and analyzing Olympic data. Dash, developed by Plotly, is a framework for building analytical web applications using Python. It allows the creation of interactive charts and dashboards that can be easily integrated with various data sources.

### Application Structure

The structure of the Dash application in this project consists of the following:

1. application main file (`app.py`):
    - The main file responsible for running the application.
    - Dash application configuration, including layout and styling.

2. layout:
    - Defines the layout of the application, including the arrangement of components on the page.
    - It consists of containers, rows and columns that organize the various UI elements.

3. Styles:
    - Application styling is implemented using CSS, which can be included directly in Python code or in a separate CSS file (if in a separate file, place it in the assets folder).
    - External CSS libraries are used, such as Dash Bootstrap Components, which provide ready-made UI components.

4 Components:
    - Dash components are UI elements such as charts, tables, forms, buttons and more.
    - Each component is created using the Dash library and can be interactive.

5 Callbacks:
    - Callbacks are functions that define the interactivity of an application.
    - They respond to user actions such as clicks, typing text, changing values on sliders, etc.
    - Callbacks update components in real time based on user inputs.

### Files in the Project

1. `app.py`:
    - This file contains the main configuration of the Dash application.
    - It defines the application layout and initializes the components.

2. assets/:
    - A directory containing CSS files and other static resources.
    - CSS files in this directory are automatically loaded by Dash.

3. data/:
    - A directory containing data used by the application.
    - Data can be loaded from CSV files, databases or other sources.

4. pages/:
    - A directory containing the sub-pages of the Dash application.
    - Sub-pages contained in this directory are automatically visible to the application
    1. `pages/scc1.py` - a file that performs analysis according to [first scenario](#scenario-1) and generates charts from the performed analysis, everything is combined into an interactive dashboard of the performed and visualized analysis
    2. `pages/scc2.py` - a file that performs the analysis according to [the second scenario](#scenario-2) and generates graphs from the analysis performed, the results are also presented on an interactive dashboard
    3. `pages/scc3.py` - another file that performs the analysis according to [the third scenario](#scenario-3) and generates an interactive dashboard with graphs from the analyses performed
    4. `pages/scc4.py` - the last file performing analyses and generating an interactive dashboard based on them, the file performs a multivariate analysis according to [the last scenario](#scenario-4)
    5. `pages/home.py` - a file that generates a home subpage, which contains a very brief description of the issue being pursued
  
### How to Edit an Application

1 Editing the Layout:
    - You can edit the layout of the application by modifying the layout section in the `app.py` file or by changing the layout of each subpage separately in its file in the pages/ directory.
    - Adding new components, changing existing ones, organizing them into containers, rows and columns.

2 Adding New Components:
    - New components can be added in the layout section.
    - You need to define component properties such as id, styles and their contents.

3. Modifying Styles:
    - Styles can be edited by modifying CSS files in the assets/ directory, or by adding styles to components while still in the source code in Python.
    - New styles can be added or existing styles can be modified to customize the look of the application.

4 Adding New Functionality:
    - New functionalities can be added by defining new callbacks in the sceanriusze files in the pages/ directory.
    - Callbacks connect the user interface to the application logic, enabling interactivity and dynamic updates.

5 Adding new application pages
    - New pages can be added by creating a new page in Python (e.g., along the lines of existing ones) and saving it in the pages/ directory.
    - To make the Dash application automatically see the page, place it in pages/ catalog and add the following line in the code:
      ```sh
      dash.register_page(__name__, title='[your_page_title]')
      ```

## Data Mining

Data Mining is the process of discovering patterns, correlations, and anomalies within large datasets to predict outcomes. Using a variety of techniques such as machine learning, statistics, and database systems, Data Mining transforms raw data into useful information. It is a crucial aspect of data analysis, enabling data-driven decision-making by identifying trends and relationships that may not be immediately evident.

### Purpose of Data Mining in This Application

In the context of this Olympic data analysis application, Data Mining is employed to uncover valuable insights from the historical performance data of athletes, countries, and events. The main objectives include:

1. Identifying trends and patterns in the performance of countries and athletes over time.

2. Predicting future outcomes based on historical data.

3. Highlighting significant factors contributing to athletic success.

4. Visualizing complex datasets to facilitate easy interpretation and analysis.

### Implementation of data mining in the application.

Data mining processes are implemented in 4 scripts in the repository, each script performs Data Mining for a separate scenario.

These files are respectively: `S1_DM.py`, `S2_DM.py`, `S3_DM.py`, `S4_DM.py`.

Each file performs the Data Mining process using machine learning models such as ARIMA, Random Forest, etc. The results of the process are presented in graphs, and these are exported to files with .png extension.
Ultimately, we can view the results in the Dash application because they are added there.

**Exception**: The only exception is the DataMining process in Scenario 3, in which it is carried out in the app, and then an interactive 3D graph is generated showing the relationships between certain anthropometric characteristics of the athletes and their chances of winning a medal.

By leveraging Data Mining techniques, this application provides a robust platform for analyzing Olympic data, offering valuable insights and predictions that can be used by researchers, analysts, and sports enthusiasts.

## License

This project is licensed under the MIT License. See the LICENSE.txt file for details.

## Authors

Piotr Greń = Co-developer - https://github.com/PiotrGren

Gabriela Kiwacka - Co-developer - https://github.com/GabrielaKiwacka



#### Polski

# Wielowymiarowa Analiza Danych Olimpijskich

## Spis treści

1. [Opis](#opis)
2. [Wymagane przed użyciem (ważne)](#wymagane-przed-użyciem-(ważne))
3. [Dane i procesy ETL](#dane-i-procesy-etl)
4. [Docker i MS SQL Server](#docker-i-ms-sql-server)
5. [Plik KPI](#plik-kpi)
6. [Aplikacja Dash](#aplikacja-dash)
7. [Data Mining](#data-mining)
8. [Licencja](#licencja)
9. [Autorzy](#autorzy)

## Opis



## Wymagane przed użyciem (ważne)

Jeżeli chcesz uruchomić ten projekt u siebie na komputerze lub stworzyć własny podobny musisz spełnić kilka wymogów:

1. Upewnij się, że masz zainstalowany HADOOP na swoim komputerze. Jeżeli nie, to możesz go zainstalować wykonując ten tutorial:
   ```sh
   https://www.youtube.com/watch?v=knAS0w-jiUk
   ```

2. Upewnij się, że masz zainstalowany Apache Spark na swoim komputerze. Jeżeli nie, to możesz go zainstalować wykonując ten tutorial:
   ```sh
   https://www.youtube.com/watch?v=OmcSTQVkrvo
   ```

3. Upewnij się, że masz zainstalowany Docker Desktop na swoim komputerze. Jeżeli nie, to możesz go zainstalować pobierając instalator z oficjalnej strony Docker:
   ```sh
   https://www.docker.com/products/docker-desktop/
   ```

4. Upewnij się, że masz zainstalowany moduł docker compose na swoim komputerze. Jeżeli nie, to możesz go zainstalować wykonując wybrany tutorial:
   ```sh
   [WINDOWS] - https://www.ionos.com/digitalguide/server/configuration/install-docker-compose-on-windows/

   [LINUX] - https://gcore.com/learning/how-to-install-docker-compose-on-linux/
   ```

5. Upewnij się, że masz zainstalowane wymagane biblioteki Python, użyte w projekcie. Jeżeli nie możesz je zainstalować pobierając plik `requirements.txt` i wykonując poniższe polecenie:
   ```sh
   pip install -r requirements.txt
   ```

6. Sklonuj repozytorium na swój lokalny komputer:
   ```sh
   git clone https://github.com/PiotrGren/Multidimensional-Olympic-Data-Analysis
   cd Multidimensional-Olympic-Data-Analysis
   ```

## Dane i procesy ETL

Repozytorium wykorzystuje dane olimpijskie, które można znaleźć w pliku CSV w katalogu Dane/. Główne pliki z danymi to:

 - athlete_events.csv: Zawiera informacje o sportowcach, wydarzeniach olimpijskich, osiągnięciach itd. w zakrasie lat 1890-2016.
 - country-codes.csv: Zawiera informacje o skrótach państw oraz kontynentach, z których pochodzą (potrzebne do utworzenia nowej kolumny z kontynentami w wykorzystanej ramce danych).

### ETL

Procesy ETL przeprowadzone na oryginalnej ramce danych, wczytanej przy pomocy biblioteki pandas są przeprowadzone w pliku `ETL.ipynb`. Plik zawiera takie procesy jak transformacja danych (np. zamiana wartości M, F w kolumnie Sex na Male, Female lub zamianę wieku na przedziały wiekowe), generowanie nowych kolumn (np. poprzez rozdzielenie kolumny Games, lub dodanie nowej kolumny z kontynentami czy też konwersja typu danych (np. z str na integer).

## Docker i MS SQL Server

### docker-compose.yml

Plik docker-compose.yml w repozytorium służy do definiowania i uruchamiania aplikacji wielokontenerowych przy użyciu Docker. W tym przypadku, plik ten konfiguruje kontener z Microsoft SQL Server.

**Jak uruchomić**

1. Upewnij się, że zainstalowałeś poprawnie Docker Desktop oraz docker-compose.
2. Upewnij się, że sklonowałeś repozytorium na swój komputer lub utworzyłeś własne z własnym plikiem docker-compose i pobrałeś sterownik `mssql-jdbc-12.6.1.jre8` (lub swoją odpowiadającą wymaganiom wersję).
3. Przejdź do folderu z plikiem docker-compose.
   ```sh
   cd sciezka/do/twojego/folderu
   ```
4. Upewnij się, że masz uruchomiony Docker Engine (włącz Docker Desktop na komputerze).
5. Uruchom docker-compose wykonując polecenie:
   ```sh
   docker-compose up
   ```
6. Jeżeli poprawnie przeprowadziłeś proces, od teraz w aplikacji Docker Desktop powinien pojawić się nowy kontener. Od teraz możesz uruchamiać i zatrzymywać go w aplikacji.

### MS SQL Server

Microsoft SQL Server to system zarządzania relacyjnymi bazami danych (RDBMS) opracowany przez firmę Microsoft. Jest używany do przechowywania i zarządzania danymi oraz wspiera szeroki zakres operacji, w tym zapytania SQL, analizy danych, tworzenie raportów i integrację z innymi aplikacjami.

W tym projekcie, MS SQL Server będzie używany do przechowywania przetworzonych danych olimpijskich, które następnie będą wykorzystywane do analiz i wizualizacji.

#### Korzyści ze stawiania MS SQL Server w kontenerze

1. **Izolacja**: Kontenery izolują aplikacje i ich zależności, co pozwala na uruchamianie wielu wersji serwera SQL obok siebie bez konfliktów.
2. **Przenośność**: Kontenery mogą być łatwo przenoszone między różnymi środowiskami (np. deweloperskim, testowym i produkcyjnym).
3. **Szybkość wdrożenia**: Kontenery pozwalają na szybkie wdrażanie i skalowanie aplikacji.
4. **Spójność**: Użycie kontenerów zapewnia, że aplikacja działa tak samo we wszystkich środowiskach, co eliminuje problemy związane z konfiguracją systemu.

### Pliki Pythona, od których należy zacząć

1. **CREATE_DATABASE.py** - Ten skrypt służy do tworzenia bazy danych w MS SQL Server. Wykonuje on polecenia SQL, które tworzą nową bazę danych, a następnie tworzy tabele potrzebne do przechowywania danych olimpijskich.

2. **LOAD_DATA.py** - Ten skrypt ładuje przetworzone dane do bazy danych MS SQL Server. Korzysta z biblioteki pandas do wczytania danych z plików CSV, a następnie zapisuje je do odpowiednich tabel w bazie danych.

3. **CHECK_DATABASE.py** - Ten skrypt sprawdza, czy baza danych istnieje, oraz czy zawiera wymagane tabele. Jest to przydatne do weryfikacji stanu bazy danych przed rozpoczęciem operacji na danych.

4. **DROP_DATABASE_OPTIONAL.py** = Jest to opcjonalny skrypt, który usuwa bazę danych, jeśli istnieje. Jest to przydatne do czyszczenia środowiska przed ponownym uruchomieniem procesów ETL lub testowaniem lub usunięciem bazy jeżeli popełnimy błąd lub coś zepsujemy.

## Plik KPI

Plik KPI.ipynb jest notebookiem Jupyter, który służy do przeprowadzania głównych analiz danych olimpijskich w projekcie. W tym pliku wykonywane są różne analizy wielowymiarowe mające na celu zrozumienie kluczowych wskaźników związanych z uczestnictwem i osiągnięciami sportowców w Igrzyskach Olimpijskich. Analiza przeprowadzana jest z podziałem na 4 scenariusze, odpowiednio:

1. **Scenariusz 1**: Zdobyte osiągnięcia sportowców - analiza kontynentalna.
2. **Scenariusz 2**: Zdobyte medale - analiza wzorców wiekowych w najpopularniejszych dyscyplinach sezonowych XXI w.
3. **Scenariusz 3**: Analiza profilu antropometrycznego polskich sportowców w kontekście zdobytych osiągnięć na igrzyskach olimpijskich po II WŚ.
4. **Scenariusz 4**: Analiza wzorców wśród podwójnych złotych medalistów z Europy, którzy zdobyli podwójne złoto w jednej dziedzinie sportowej.

### Cel i zawartość

Plik KPI.ipynb jest wykorzystywany do przeprowadzenia wstępnych analiz danych oraz testowania różnych scenariuszy, które później są implementowane w aplikacji Dash. Jest to plik testowy, który pozwala na eksperymentowanie z danymi oraz tworzenie i wizualizację różnych wskaźników oraz anaiz przed ich ostateczną implementacją.

Każdy z tych scenariuszy jest szczegółowo analizowany, a wyniki są wizualizowane przy użyciu wykresów i tabel. W wyniku tych analiz powstają wstępne wersje wykresów i raportów, które służą jako podstawa do dalszego rozwoju i implementacji w aplikacji Dash.

### Pamiętaj

Nleży pamiętać, że KPI.ipynb jest plikiem testowym, który służy do eksperymentowania i testowania różnych podejść do analizy danych. Ostateczne wersje wszystkich procesów analitycznych oraz wykresów tworzonych i przeprowadzanych w tym pliku są zawarte w aplikacji Dash. Aplikacja Dash integruje te analizy w interaktywne i przyjazne dla użytkownika środowisko, umożliwiając dynamiczne przeglądanie i analizowanie danych olimpijskich.

Plik KPI.ipynb odgrywa kluczową rolę w cyklu życia projektu, umożliwiając szybkie prototypowanie i testowanie pomysłów, które są następnie przenoszone do ostatecznej aplikacji Dash.

## Aplikacja Dash

Aplikacja Dash w tym projekcie jest interaktywną platformą do wizualizacji i analizy danych olimpijskich. Dash, opracowany przez Plotly, jest frameworkiem do budowy analitycznych aplikacji webowych przy użyciu Pythona. Umożliwia tworzenie interaktywnych wykresów i dashboardów, które można łatwo integrować z różnymi źródłami danych.

### Struktura Aplikacji

Struktura aplikacji Dash w tym projekcie składa się z następujących elementów:

1. Plik główny aplikacji (`app.py`):
    - Główny plik odpowiedzialny za uruchomienie aplikacji.
    - Konfiguracja aplikacji Dash, w tym layout i stylizacja.

2. Layout:
    - Definiuje układ aplikacji, w tym rozmieszczenie komponentów na stronie.
    - Składa się z kontenerów, rzędów i kolumn, które organizują różne elementy interfejsu użytkownika.

3. Style:
    - Stylizacja aplikacji jest realizowana przy użyciu CSS, które może być załączone bezpośrednio w kodzie Pythona lub w osobnym pliku CSS (jeżeli w osobnym pliku należy umieścić go w folderze assets).
    - Używane są zewnętrzne biblioteki CSS, takie jak Dash Bootstrap Components, które dostarczają gotowe komponenty UI.

4. Komponenty:
    - Komponenty Dash to elementy interfejsu użytkownika, takie jak wykresy, tabele, formularze, przyciski i inne.
    - Każdy komponent jest tworzony przy użyciu biblioteki Dash i może być interaktywny.

5. Callbacki:
    - Callbacki to funkcje, które definiują interaktywność aplikacji.
    - Odpowiadają na działania użytkownika, takie jak kliknięcia, wpisywanie tekstu, zmiana wartości na suwakach, itp.
    - Callbacki aktualizują komponenty w czasie rzeczywistym na podstawie wejść użytkownika.
  
### Pliki w Projekcie

1. `app.py`:
    - Plik ten zawiera główną konfigurację aplikacji Dash.
    - Definiuje układ aplikacji i inicjalizuje komponenty.

2. assets/:
    - Katalog zawierający pliki CSS i inne zasoby statyczne.
    - Pliki CSS w tym katalogu są automatycznie ładowane przez Dash.

3. Dane/:
    - Katalog zawierający dane wykorzystywane przez aplikację.
    - Dane mogą być ładowane z plików CSV, baz danych lub innych źródeł.

4. pages/:
    - Katalog zawierający podstrony aplikacji Dash
    - Podstrony zawarte w tym katalogu są automatycznie widoczne dla aplikacji
    1. `pages/scc1.py` - plik przeprowadzający analizę według [pierwszego scenariusza](#Scenariusz-1) oraz generujący wykresy z przeprowadzonych analiz, wszystko połączone jest w interaktywny dashboard z przeprowadzonej i zwizualizowanej analizy
    2. `pages/scc2.py` - plik przeprowadzający analizę według [drugiego scenariusza](#Scenariusz-2) oraz generujący wykresy z przeprowadzonych analiz, wyniki również przedstawione są na interaktywnym dashboardzie
    3. `pages/scc3.py` - kolejny plik przeprowadzający analizę według [trzeciego scenariusza](#Scenariusz-3) oraz generujący  interaktywny dashboard z wykresami z przeprowadzonych analiz
    4. `pages/scc4.py` - ostatni plik przeprowadzający analizy i generujący na ich podstawie interaktywny dashboard, plik realizuje wielowmiarową nalizę według [ostatniego scenariusza](#Scenariusz-4)
    5. `pages/home.py` - plik generujący podstronę domową, na której zawarty jest bardzo krótki opis realizowanego zagadnienia
  
### Jak Edytować Aplikację

1. Edytowanie Layoutu:
    - Layout aplikacji można edytować, modyfikując sekcję layout w pliku `app.py` lub poprzez zmianę layoutu każdej podstrony z osobna w jej pliku w katalogu pages/.
    - Dodawanie nowych komponentów, zmiana istniejących, organizowanie ich w kontenery, rzędy i kolumny.

2. Dodawanie Nowych Komponentów:
    - Nowe komponenty można dodać w sekcji layout.
    - Należy zdefiniować właściwości komponentów, takie jak id, style oraz ich zawartość.

3. Modyfikacja Stylów:
    - Style można edytować, modyfikując pliki CSS w katalogu assets/, lub poprzez dodanie styli do komponentów jeszcze w kodzie źródłowym w Pythonie.
    - Można dodać nowe style lub zmienić istniejące, aby dostosować wygląd aplikacji.

4. Dodawanie Nowych Funkcjonalności:
    - Nowe funkcjonalności można dodać, definiując nowe callbacki w plikach sceanriuszy w katalogu pages/.
    - Callbacki łączą interfejs użytkownika z logiką aplikacji, umożliwiając interaktywność i dynamiczne aktualizacje.

5. Dodawanie nowych stron aplikacji
    - Nowe strony można dodać poprzez stworzenie nowej strony w Pythonie (np na wzór już istniejących) i zapisanie jej w katalogu pages/
    - Aby aplikacja Dash automatycznie widziała stronę należy umieścić ją w katalogu pages/ oraz dodać w kodzie poniższą linijkę:
      ```sh
      dash.register_page(__name__, title='[twój_tytuł_strony]')
      ```

## Data Mining

Data Mining to proces odkrywania wzorców, korelacji i anomalii w dużych zbiorach danych w celu przewidywania wyników. Korzystając z różnych technik, takich jak uczenie maszynowe, statystyka i systemy baz danych, Data Mining przekształca surowe dane w przydatne informacje. Jest to kluczowy aspekt analizy danych, umożliwiający podejmowanie decyzji w oparciu o dane poprzez identyfikację trendów i relacji, które mogą nie być od razu widoczne.

### Cel Data Mining w tej aplikacji

W kontekście tej aplikacji do analizy danych olimpijskich, eksploracja danych (Data Mining) jest wykorzystywana do odkrywania cennych spostrzeżeń z historycznych danych dotyczących wyników sportowców, krajów i wydarzeń. Główne cele obejmują:

1. Identyfikacja trendów i wzorców w wynikach krajów i sportowców w czasie.

2. Przewidywanie przyszłych wyników na podstawie danych historycznych.

3. Podkreślanie istotnych czynników przyczyniających się do sukcesu sportowego.

4. Wizualizacja złożonych zestawów danych w celu ułatwienia interpretacji i analizy.

### Implementacja eksploracji danych w aplikacji

Procesy eksploracji danych są zaimplementowane w 4 skryptach w repozytoirum, każdy skrypt przeprowadza Data Mining dla osobnego scenariusza.

Te pliki to odpowiednio: `S1_DM.py`, `S2_DM.py`, `S3_DM.py`, `S4_DM.py`

Każdy plik przeprowadza proces Data Mining z wykorzystaniem modeli nauczania maszynowego takich jak np. ARIMA, Random Forest itp. Wyniki procesu przedstawiane są na wykresach, a te eksportowane są do plików z rozszerzeniem .png.
Ostatecznie wyniki możemy przeglądać w aplikacji Dash ponieważ są one tam dodane.

**Wyjątek**: Jedynym wyjątkiem jest proces DataMining w scenariuszu 3, w którym to jest on przeprowadzany w aplikacji, a następnie generowany jest interaktywny wykres 3D przedstawiający zależności pomiędzy niektórymi cechami antropometrycznymi sportowców, a ich szansą na zdobycie medalu.

Wykorzystując techniki Data Mining, aplikacja ta zapewnia solidną platformę do analizy danych olimpijskich, oferując cenne spostrzeżenia i prognozy, które mogą być wykorzystywane przez badaczy, analityków i entuzjastów sportu.

## Licencja

Ten projekt jest dostępny na licencji MIT. Szczegóły można znaleźć w pliku `LICENSE.txt`.

## Autorzy

Piotr Greń - Co-developer - https://github.com/PiotrGren

Gabriela Kiwacka - Co-developer - https://github.com/GabrielaKiwacka
