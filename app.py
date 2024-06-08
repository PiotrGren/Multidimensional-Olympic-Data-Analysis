import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])

app.layout = html.Div([
    html.Div([
        html.H1('WIELOWYMIAROWA   ANALIZA   DANYCH   OLIMPIJSKICH'),
        html.H5('Przygotowali:  Kiwacka Gabriela,  Greń Piotr')
    ], style = {'padding': '1%', 'margin':'2%', 'textAlign':'center'}),

    html.Div([
        html.Div(
            list(map(lambda page: html.Div([
                dcc.Link(f"{page['title']}", href=page["relative_path"])
            ], className='menu-element'), dash.page_registry.values()))
        )
    ], className='menu-container'),
    dash.page_container
])

app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

if __name__ == '__main__':
    app.run(debug=True)