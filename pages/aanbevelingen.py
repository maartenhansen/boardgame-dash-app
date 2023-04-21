import dash
from dash import html, dcc, dash_table, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

import pandas as pd
import xml.etree.ElementTree as ET
import requests
from sqlalchemy import create_engine, text, Table, MetaData, Column, Integer, insert, select
from sqlalchemy.exc import IntegrityError
import pyodbc
import re
import random
import duckdb
import time

# import custom handwritten functions
import sys
sys.path.append('C:/Users/maart/OneDrive/Bureaublad/Syntra/Eindwerk/Dash-Plotly') # make sure python will look into the entire 'Dash-Plotly' folder as well
from functions.sql_bg_dash import create_db_connection, create_initial_df
from functions.recommendation_engine_bg_dash import get_recommendations

# Define page & path
dash.register_page(__name__, path='/recommender/')




##### Incorporporate data into app
# define servername & database name
server = 'DESKTOP-4K7IERR\SYNTRA_MAARTEN'
database = 'BoardgameProject'

# create engine for connection with database --> Can't be handled in the callback only because the compoment with the columns to display needs to be created
engine = create_db_connection(server, database)

# create initial dataframe from fact table
bgg_df = create_initial_df(engine)

# define columns to be displayed in the datatable    
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



##### CREATE COMPONENT: recommended boardgames datatable (initially all boardgames, but will only be returned filtered with recommended games when displayed)
rec_table = dash_table.DataTable(
    data=bgg_df.to_dict('records'),
    columns=bgg_df_cols_to_display,
    page_size=20,
    id='rec_table',

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





##### LAYOUT: define layout of page
layout = html.Div([
    html.Div([
        html.H1(children='Aanbevelingstool'),
        html.Br(),
        html.H3(children='Vul je BGG-gebruikersnaam in'),
        html.Div([
            dcc.Input(id='input_bgg_user', type='text', placeholder='Gebruikersnaam', style={'width': '15%', 'height': '40px', 'display': 'inline-block', 'marginRight': '10px', 'marginTop': '10px'}),
            dmc.Button('Zoeken', id='button_bgg_user',style={'width': 'auto', 'height': '40px', 'display': 'inline-block', 'marginRight': '1x', 'marginTop': '10px'})
        ]),
        html.Br(),
        html.H4(children="Deze spellen zijn echt iets voor jou!", id="header_after_rec", style={'display': 'none'}), # hidden at first, so it will only show up when the callback is fired (display: none)
        # datatable contained in a spinner that will fire when the callback to load the table is performed
        dbc.Spinner(children=[html.Div(rec_table, id='div_rec_table',style={'margin-top': '1%', 'display': 'none'})], spinnerClassName='spinner'), # Div containing rec_table is hidden at first, so it will only show up when the callback is fired (display: none)
    ], style={'padding': 40, 'flex': 1})
])


    


#### define callback
@callback(
    Output(component_id='header_after_rec', component_property='style'), # to be able to show (unhide) the label
    Output(component_id='div_rec_table', component_property='style'), # to be able to show (unhide) the datatable Div
    Output(component_id='rec_table', component_property='data'),
    Output(component_id='rec_table', component_property='tooltip_data'),
    Input(component_id='button_bgg_user', component_property='n_clicks'),
    State(component_id='input_bgg_user', component_property='value')
)
def update_rec_table(clicks, bgg_user):
    if clicks is None or clicks == 0:
        raise PreventUpdate
    else:
        recommendations = get_recommendations(bgg_user)

        # filter based on boardgames
        gamelist = bgg_df[0:0] # create empyt dataframe with same columns as df_temp to append the necessary rows to
        for game in recommendations:
            # Handling ' or " in game name: In this example, the ? is a placeholder for the game name. When you pass the game name as a parameter, the database engine will automatically handle any special characters in the name.
            game_name = game.replace("'", "''") # escape single quotes by doubling them up
            query = "SELECT * FROM bgg_df WHERE BgName LIKE '{}'".format(game_name)
            df_to_add = duckdb.query(query).to_df()
   
            gamelist = pd.concat([gamelist, df_to_add]).sort_values("Ranking")        

        # return dataframe
        gamelist = gamelist.drop_duplicates(subset='BgNumber', keep='first') # drop duplicates (if one game is contained in the list of 2 designers)
        gamelist = gamelist.drop_duplicates(subset='BgName', keep='first') # drop duplicates (if one game exists in BGG twice)
        gamelist = gamelist.sample(n=10).sort_values("Ranking") # randomly select 10 games from the dataframe which contained all games

        # adjust tooltip data to match new dataframe
        tooltip_data=[
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in gamelist.to_dict('records')
        ]

        # return data into output
        return {'display': 'block'}, {'display': 'block'}, gamelist.to_dict('records'), tooltip_data # {'display': 'block'} is necessary to unhide (show) the  label when the request is made, Hidden=False is necessary for the datatable









        

