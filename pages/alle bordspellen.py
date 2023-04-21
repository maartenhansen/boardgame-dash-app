import dash
from dash import Dash, dcc, Output, Input, dash_table, html, callback # dcc = Dash Core Component
import dash_bootstrap_components as dbc #pip install dash_bootstrap_components
import plotly.express as px
import duckdb

import pandas as pd

from sqlalchemy import create_engine, text, Table, MetaData, Column, Integer, insert, select
from sqlalchemy.exc import IntegrityError

# import custom handwritten functions
import sys
sys.path.append('C:/Users/maart/OneDrive/Bureaublad/Syntra/Eindwerk/Dash-Plotly') # make sure python will look into the entire 'Dash-Plotly' folder as well
from functions.sql_bg_dash import create_db_connection, create_initial_df
from functions.filters import * # import functions for defining/creating filter components
from settings.config import * # import global variables defined in 'config.py'

# Define page & path
dash.register_page(__name__, path='/') # '/' = homepage

##### Incorporporate data into app
# define servername & database name
server = 'DESKTOP-4K7IERR\SYNTRA_MAARTEN'
database = 'BoardgameProject'

# create engine for connection with database
engine = create_db_connection(server, database)

# create initial dataframe from fact table
bgg_df = create_initial_df(engine)

# define columns that need to be displayed in the datatable component  below    
bgg_df_cols_to_display = [
    {"name": "BGG-ranking", "id": "Ranking"},
    {"name": "Titel", "id": "BgName"},
    {"name": "Min. Spelers", "id": "MinPlayers"},
    {"name": "Max. Spelers", "id": "MaxPlayers"},
    {"name": "Max. Speeltijd", "id": "MaxPlaytime"},
    {"name": "Complexiteit", "id": "Complexity"},
    {"name": "Ontwerper", "id": "DesignerList"},
    {"name": "Mechanisme", "id": "MechanicList"},
    {"name": "Hoofdcategorie", "id": "SubdomainList"}
    ]

###### Build components

h1 = dcc.Markdown(children="# Alle bordspellen") 

### Define filters
filter_ranking = comp_filter_ranking()

filter_players = comp_filter_players()

max_playtime = bgg_df['MaxPlaytime'].max() # used in callback function
filter_playtime = comp_filter_playtime()

filter_complexity = comp_filter_complexity()

filter_designer = comp_filter_from_jointable(bgg_df, 'DesignerList', all_designers, 'filter_designer')

filter_subdomain = comp_filter_from_jointable(bgg_df, 'SubdomainList', all_subdomains, 'filter_subdomain')

filter_mechanic = comp_filter_from_jointable(bgg_df, 'MechanicList', all_mechanics, 'filter_mechanic')


### Create data_table
bgg_table = dash_table.DataTable(
    data=bgg_df.to_dict('records'),
    columns=bgg_df_cols_to_display,
    page_size=20,
    id='bgg_table',

    tooltip_data=[
    {
        column: {'value': str(value), 'type': 'markdown'}
        for column, value in row.items()
    } for row in bgg_df.to_dict('records')
    ],
    style_header={
        'backgroundColor': '#0E1012',
        'fontWeight': 'bold'
    },
    style_table={'overflowX': 'scroll'},
    css=[{
        'selector': '.dash-table-tooltip',
        'rule': 'background-color: grey; font-family: monospace; color: white'
    }],


    style_cell={
    'font-family': 'sans-serif',
    'font-size': '0.9rem',
    'text-align': 'left',
    'backgroundColor': '#0F2537',
    'color': 'white'
    },

    style_cell_conditional=[
    {    
        'if': {'column_id': 'BgName'},
        'maxWidth': '300px',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    },
    {    
        'if': {'column_id': 'DesignerList'},
        'maxWidth': '300px',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    },
    {    
        'if': {'column_id': 'SubdomainList'},
        'maxWidth': '300px',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    },
    {    
        'if': {'column_id': 'MechanicList'},
        'maxWidth': '300px',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    }
    ],
    tooltip_delay=0,
    tooltip_duration=None,
    style_as_list_view=True
)

###### Customize layout
layout = html.Div([
    html.Div([
        html.H1(children='Alle bordspellen'),
        html.Br(),
        html.Div([
            dcc.Markdown(children='Weergave'),
            filter_ranking
        ], style={'width': '8%', 'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Markdown(children='Aantal spelers'),
            filter_players
        ], style={'width': '8%', 'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Markdown(children='Maximale spelduur'),
            filter_playtime
        ], style={'width': '12%', 'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Markdown(children='Complexiteit'),
            filter_complexity
        ], style={'width': '12%', 'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Markdown(children='Ontwerper'),
            filter_designer
        ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Markdown(children='Hoofdcategorie'),
            filter_subdomain
        ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '10px'}),
        html.Div([
            dcc.Markdown(children='Mechanisme'),
            filter_mechanic
        ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '10px'}),
        html.Br(),
        html.Div(bgg_table, style={'margin-top': '1%'}
        )
    ], style={'padding': 40, 'flex': 1})
])


###### Add callbacks (allows components to interact)
@callback(
    Output(component_id='bgg_table', component_property='data'),
    Output(component_id='bgg_table', component_property='tooltip_data'),
    Input(component_id='filter_ranking', component_property='value'),
    Input(component_id='filter_players', component_property='value'),
    Input(component_id='filter_playtime', component_property='value'),
    Input(component_id='filter_complexity', component_property='value'),
    Input(component_id='filter_designer', component_property='value'),
    Input(component_id='filter_subdomain', component_property='value'),
    Input(component_id='filter_mechanic', component_property='value')
)
def update_bgg_table(value_ranking, value_players, value_playtime, value_complexity, value_designer, value_subdomain, value_mechanism): # values are the inputs in the order they are assigned above
    # filter ranking
    df_temp = exe_filter_ranking(value_ranking, bgg_df)

    # filter players
    df_temp = exe_filter_players(value_players, df_temp)
    
    # filter playtime
    df_temp = exe_filter_playtime(value_playtime, df_temp)

    # filter complexity
    df_temp = exe_filter_complexity(value_complexity, df_temp)

    # filter designer
    df_temp = exe_filter_from_jointable(value_designer, df_temp, 'DesignerList')
            

    # filter subdomain
    df_temp = exe_filter_from_jointable(value_subdomain, df_temp, 'SubdomainList')

    # filter mechanism
    df_temp = exe_filter_from_jointable(value_mechanism, df_temp, 'MechanicList')
            


    # return dataframe
    df_temp = df_temp.drop_duplicates(subset='BgNumber', keep='first') # drop duplicates (if one game is contained in the list of 2 designers)

    # adjust tooltip data to match new dataframe
    tooltip_data=[
    {
        column: {'value': str(value), 'type': 'markdown'}
        for column, value in row.items()
    } for row in df_temp.to_dict('records')
    ]

    return df_temp.to_dict('records'), tooltip_data