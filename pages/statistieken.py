import dash
from dash import html

# import custom handwritten functions
import sys
sys.path.append('C:/Users/maart/OneDrive/Bureaublad/Syntra/Eindwerk/Dash-Plotly') # make sure python will look into the entire 'Dash-Plotly' folder as well
from functions.sql_bg_dash import create_db_connection, create_initial_df

# Define page & path
dash.register_page(__name__, path='/stats/') # '/' = homepage

##### Incorporporate data into app
# define servername & database name
server = 'DESKTOP-4K7IERR\SYNTRA_MAARTEN'
database = 'BoardgameProject'

# create engine for connection with database
engine = create_db_connection(server, database)

# create initial dataframe from fact table
bgg_df = create_initial_df(engine)


layout = html.Div([
    html.Div([
        html.H1(children='Statistieken'),
    ], style={'padding': 40, 'flex': 1})
])
