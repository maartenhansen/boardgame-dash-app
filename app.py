from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc #pip install dash_bootstrap_components


app = Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO], use_pages=True)


# styling the sidebar
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#0E1012",
}

PAGE_CONTAINER_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    }


# create sidebar component
sidebar = html.Div(
	[
    html.H2("Bordspel app", className='display-4'), # display-4 refers to bootstrap cheatsheet and changes size of text
    html.Br(),
    html.P("Maarten zijn data-app over bordspellen", className="lead"),
    dbc.Nav(
        [
            dbc.NavLink("Alle bordspellen", href="/", active="exact"), # active --> If selected, it will be shown e.g. highlighted
            dbc.NavLink("Aanbevelingen", href='/recommender/', active="exact")
        ],
	vertical=True,
	pills=True # pills maakt er een lange balk van bij weergave van actieve pagina (ipv enkel een link)
    ),
    ],
    style=SIDEBAR_STYLE,
)

app.layout = html.Div(
	    [
            dcc.Location(id="url"),
            sidebar,
	        html.Div(dash.page_container, style=PAGE_CONTAINER_STYLE)
        ]
	)

if __name__ == '__main__':
	app.run_server(port=8051, debug=True)