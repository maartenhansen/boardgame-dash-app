import dash
from dash import Dash, dcc, Output, Input, dash_table, html, callback # dcc = Dash Core Component
import dash_bootstrap_components as dbc #pip install dash_bootstrap_components
import plotly.express as px
import duckdb

import pandas as pd

from sqlalchemy import create_engine, text, Table, MetaData, Column, Integer, insert, select
from sqlalchemy.exc import IntegrityError

##### Incorporporate data into app
# define servername & database name
server = 'DESKTOP-4K7IERR\SYNTRA_MAARTEN'
database = 'BoardgameProject'

# create engine for connection with database
engine = create_engine("mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=" + server + ";DATABASE=" + database + ";Trusted_Connection=yes;")

# create initial dataframe from fact table
with engine.connect() as conn:
    # only select maxplaytime, because minplaytime & maxplaytime will always be similar, so we would count the value double
    stmt = text("select ID, BgNumber, BgName, MinPlayers, MaxPlayers, MaxPlaytime, Complexity, Ranking from Fct_Boardgame Where RowEndDate IS NULL AND Ranking < 1500 AND YearPublished != 0 ORDER BY Ranking Asc")
    bgg_df = pd.read_sql(stmt, conn)

# Create list with all the Dim columns that need to be added
dim_list = ['Category', 'Designer', 'Illustrator', 'Mechanic', 'Subdomain', 'Publisher']
    
# Run a query to add dimension values to dataframe
with engine.connect() as conn:
    for dim in dim_list: # Run the query for each Dimension in dim_list
        # sql statement that returns all values for each game concatenated (divided using ,-,)
        stmt = text(f"select Fct.BgNumber, STRING_AGG(CONVERT(VARCHAR(max), Dim.{dim}Name), ', ') AS {dim}List, Fct.Ranking from Fct_Boardgame as Fct left join Dim_Boardgame_{dim} as Joi on Joi.Boardgame_ID=Fct.ID left join Dim_{dim} as Dim on Joi.{dim}_ID=Dim.ID Where RowEndDate IS NULL AND Ranking < 1500 AND YearPublished != 0 Group By Fct.BgNumber, Fct.Ranking Order by Fct.Ranking Asc")
        # create temporary df
        df_temp = pd.read_sql(stmt, conn)
        # add dimension column form temporary df to final df
        bgg_df[f"{dim}List"] = df_temp[f"{dim}List"]
    
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
#app = Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])
#app.title = "Maarten's Boardgames"
dash.register_page(__name__, path='/') # '/' = homepage

h1 = dcc.Markdown(children="# Alle bordspellen") 

### Define filters
filter_ranking = dcc.Dropdown(['Top 100', 'Top 250', 'Top 1000', 'Alle bordspellen'], 'Top 1000', id='filter_ranking')
filter_players = dcc.Dropdown(['1', '2', '3','4', '5', '6', '7+'], id='filter_players')

max_playtime = bgg_df['MaxPlaytime'].max()
filter_playtime = dcc.RangeSlider(0, 180,
        id='filter_playtime',
        value=[0, 180],
        marks={
            0: "0'",
            20: "20'",
            40: "40'",
            60: "1u",
            120: "2u",
            180: "3u+"
        },
        dots=False,
        step=10,
        updatemode='drag',
        tooltip={"placement": "bottom"}
    )

filter_complexity = dcc.RangeSlider(0,5, 
            value=[0,5], 
            step=0.1, 
            id='filter_complexity',
            updatemode='drag', 
            tooltip={"placement": "bottom"}, 
            marks={
            0: "0",
            1: "1",
            2: "2",
            3: "3",
            4: "4",
            5: "5"
    })

# Create list containing all unique designers
all_designers = []
def get_designer_list(string):
    global all_designers
    try:
        temp_list = string.split(', ')
        for substring in temp_list:
            if substring not in all_designers:
                all_designers.append(substring)
    except Exception as err:
        pass

bgg_df['DesignerList'].apply(lambda x: get_designer_list(x))

# Create filter based on list with all unique designers
filter_designer = dcc.Dropdown(
    options=all_designers,
    multi=True,
    id='filter_designer'
)

# Create list containing all unique subdomains
all_subdomains = []
def get_subdomain_list(string):
    global all_subdomains
    try:
        temp_list = string.split(', ')
        for substring in temp_list:
            if substring not in all_subdomains:
                all_subdomains.append(substring)
    except Exception as err:
        pass

bgg_df['SubdomainList'].apply(lambda x: get_subdomain_list(x))

# Create filter based on list with all unique subdomains
filter_subdomain = dcc.Dropdown(
    options=all_subdomains,
    multi=True,
    id='filter_subdomain'
)

# Create list containing all unique mechanics
all_mechanics = []
def get_mechanic_list(string):
    global all_mechanics
    try:
        temp_list = string.split(', ')
        for substring in temp_list:
            if substring not in all_mechanics:
                all_mechanics.append(substring)
    except Exception as err:
        pass

bgg_df['MechanicList'].apply(lambda x: get_mechanic_list(x))

# Create filter based on list with all unique subdomains
filter_mechanic = dcc.Dropdown(
    options=all_mechanics,
    multi=True,
    id='filter_mechanic'
)

# Create data_table
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
    if value_ranking == 'Top 100':
        value_ranking = 100
    elif value_ranking == 'Top 250':
        value_ranking = 250
    elif value_ranking == 'Top 1000':
        value_ranking = 1000
    else:
        value_ranking = 999999999
    df_temp = bgg_df.query('Ranking <= {}'.format(value_ranking)) # only the first query will be executed on the full dataframe, the following will be filtered from df_temp in order not to override (forget/undo) previous filters

    # filter players
    if value_players == '7+':
        players = 7
        df_temp = df_temp.query('MaxPlayers >= {}'.format(players)) # filtered from df_temp in order not to override (forget/undo) previous filters
    elif value_players != None:
        print(value_players)
        min_players = int(value_players)
        max_players = min_players
        df_temp = df_temp.query('(MinPlayers <= {}) & (MaxPlayers >= {})'.format(min_players, max_players)) # filtered from df_temp in order not to override (forget/undo) previous filters
    
    # filter playtime
    min_time = value_playtime[0]
    if value_playtime[1] == 180:
        max_time = 99999999
    else:
        max_time = value_playtime[1]
    df_temp = df_temp.query('(MaxPlaytime >= {}) & (MaxPlaytime <= {})'.format(min_time, max_time))

    # filter complexity
    min_complexity = value_complexity[0]
    max_complexity = value_complexity[1]
    df_temp = df_temp.query('(Complexity >= {}) & (Complexity <= {})'.format(min_complexity, max_complexity))

    # filter designer
    if value_designer != None and value_designer != []:
        designer_df = df_temp[0:0] # create empyt dataframe with same columns as df_temp to append the necessary rows to
        for designer in value_designer:
            df_to_add = duckdb.query("SELECT * FROM df_temp WHERE DesignerList LIKE '%{}%'".format(designer)).to_df() # find all games related to the designer, repeat for each designer
            designer_df = pd.concat([designer_df, df_to_add]).sort_values("Ranking")
        designer_df = designer_df.drop_duplicates(subset='BgNumber', keep='first') # drop duplicates (if one game is contained in the list of 2 designers)
        df_temp = designer_df
    else:
        df_temp = df_temp
            

    # filter subdomain
    if value_subdomain != None and value_subdomain != []:
        subdomain_df = df_temp[0:0] # create empyt dataframe with same columns as df_temp to append the necessary rows to
        for subdomain in value_subdomain:
            df_to_add = duckdb.query("SELECT * FROM df_temp WHERE SubdomainList LIKE '%{}%'".format(subdomain)).to_df() # find all games related to the designer, repeat for each designer
            subdomain_df = pd.concat([subdomain_df, df_to_add]).sort_values("Ranking")
        subdomain_df = subdomain_df.drop_duplicates(subset='BgNumber', keep='first') # drop duplicates (if one game is contained in the list of 2 designers)
        df_temp = subdomain_df
    else:
        df_temp = df_temp

    # filter mechanism
    if value_mechanism != None and value_mechanism != []:
        mechanism_df = df_temp[0:0] # create empyt dataframe with same columns as df_temp to append the necessary rows to
        for mechanism in value_mechanism:
            df_to_add = duckdb.query("SELECT * FROM df_temp WHERE MechanicList LIKE '%{}%'".format(mechanism)).to_df() # find all games related to the designer, repeat for each designer
            mechanism_df = pd.concat([mechanism_df, df_to_add]).sort_values("Ranking")
        mechanism_df = mechanism_df.drop_duplicates(subset='BgNumber', keep='first') # drop duplicates (if one game is contained in the list of 2 designers)
        df_temp = mechanism_df
    else:
        df_temp = df_temp
            


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