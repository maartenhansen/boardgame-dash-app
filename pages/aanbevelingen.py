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

dash.register_page(__name__, path='/recommender/')







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
    style_as_list_view=True,
    markdown_options={"html": True}
)

##### Create recommended boardgames (initially all boardgames, but will only be returned filtered with recommended games)
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





##### layout
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






#### Define function that will be used in callback
printed_games = set() # WILL BE ACCESSED IN FUCNTION BELOW AS GLOBAL VARIABLE
printed_amount = 0 # WILL BE ACCESSED IN FUCNTION BELOW AS GLOBAL VARIABLE

def get_recommendations_by_callback(bgg_username):
    #### GET BGG USERDATA
    # make a request to retrieve the XML data
    url = 'https://boardgamegeek.com/xmlapi2/collection?username=' + bgg_username + '&rated=1&subtype=boardgame&stats=1'
    response = requests.get(url)
    print(url)

        # retry until a successful response is received
    while response.status_code == 202:
        print("Request processing...retrying in 1 seconds.")
        time.sleep(1)
        response = requests.get(url)

    # raise an exception if the response was not successful
    response.raise_for_status()




    # parse the XML data
    root = ET.fromstring(response.content)

    # create an empty list to store the data
    data = []

    # loop through each 'item' element and extract the desired data
    for item in root.iter('item'):
        objectid = item.attrib['objectid']
        game_name = item.find('name').text
        rating_value = item.find(".//rating").attrib['value']
        # only include games with rating of 7 or above
        if float(rating_value) >= float(7):
            data.append({'objectid': objectid, 'name': game_name, 'rating_value': rating_value})

    # create a pandas DataFrame from the data
    df_user = pd.DataFrame(data)

    #### DEFINE SERVER CONNECTION & GET BGG GAME DATA
        # define servername & database name
    server = 'DESKTOP-4K7IERR\SYNTRA_MAARTEN'
    database = 'BoardgameProject'

    # create engine for connection with database
    engine = create_engine("mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=" + server + ";DATABASE=" + database + ";Trusted_Connection=yes;")

    # create initial dataframe from fact table
    with engine.connect() as conn:
        # only select maxplaytime, because minplaytime & maxplaytime will always be similar, so we would count the value double
        stmt = text("select ID, BgNumber, BgName, MinPlayers, MaxPlayers, MaxPlaytime, Complexity from Fct_Boardgame Where RowEndDate IS NULL AND Ranking < 1500 AND YearPublished != 0 ORDER BY BgNumber Asc")
        df = pd.read_sql(stmt, conn)
        
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
            df[f"{dim}List"] = df_temp[f"{dim}List"]

    ### Put necessary fact columns in buckets              
    # Group complexity
    def group_complexity(x):
        if x > 4:
            return "VeryComplex"
        elif x > 3:
            return "Complex"
        elif x > 2:
            return "ModeratelyComplex"
        elif x > 1:
            return "Easy"
        elif x > 0:
            return "VeryEasy"
        else:
            return "UnknonwComplexity"

    df['Complexity'] = df['Complexity'].apply(lambda x: group_complexity(x))

    # Group playercount
    def group_playercount(x, minmax):
        # Try Except is neccesary because it will throw an error if the code is ran twice, because the values will no longer be integers (but strings)
        try:
            if x == 1:
                return minmax + "SoloPlayer"
            elif x == 2:
                return minmax + "TwoPlayer"
            elif x == 3:
                return minmax + "ThreePlayer"
            elif x <= 5:
                return minmax + "FourFivePlayer"
            elif x == 6:
                return minmax + "SixPlayer"
            elif x > 6:
                return minmax + "ManyPlayer"
            else:
                return minmax + "PlayerCountUnknown"
        except Exception as err:
            print(err)

    df['MinPlayers'] = df['MinPlayers'].apply(lambda x: group_playercount(x, 'min'))
    df['MaxPlayers'] = df['MaxPlayers'].apply(lambda x: group_playercount(x, 'max'))

    # Group duration
    def group_playtime(x):
        # Try Except is neccesary because it will throw an error if the code is ran twice, because the values will no longer be integers (but strings)
        try:
            if x <= 30:
                return "UnderThirtyMinutes"
            elif x <= 60:
                return "UnderOneHour"
            elif x <= 90:
                return "UnderNinetyMinutes"
            elif x <= 120:
                return "UnderTwoHours"
            elif x <= 240:
                return "UnderFourHours"
            elif x > 240:
                return "LotsOfHours"
            else:
                return "DurationUnknown"
        except Exception as err:
            print(err)

    df['MaxPlaytime'] = df['MaxPlaytime'].apply(lambda x: group_playtime(x))



    ### Vectorize data
    # Clean strings - remove Spaces (eacht keyword / attribute should be one word, as we will vectorize these strings)
    def clean_text(x):
        result = str(x).lower()
        return(result.replace(' ','').replace('/', '').replace(',-,', ' '))

    columns_toclean = ['MinPlayers', 'MaxPlayers', 'MaxPlaytime', 'Complexity', 'CategoryList', 'DesignerList', 'IllustratorList', 'MechanicList', 'SubdomainList', 'PublisherList']

    # Split data into large strings with keywords divided by spaces
    for column in columns_toclean:
        df[column] = df[column].apply(lambda x: clean_text(x))
        
    df['CombinedData'] = df[df.columns[3:]].apply(
        lambda x: ' '.join(x.dropna().astype(str)),
        axis=1
    )

    # Vectorize the dataframe
    from sklearn.feature_extraction.text import CountVectorizer

    vectorizer = CountVectorizer()
    vectorized = vectorizer.fit_transform(df['CombinedData'])

    # Define similarities (Using Cosine similarity)
    from sklearn.metrics.pairwise import cosine_similarity

    similarities = cosine_similarity(vectorized, vectorized)


    # only keep rated games where the data is known in the boardgames df
    df_user['objectid'] = df_user['objectid'].astype(int)
    df['BgNumber'] = df['BgNumber'].astype(int)
    df_user = df_user[df_user['objectid'].isin(df['BgNumber'])]


    #### START ANALYSIS
    # Step 1: Get the user's top-rated games
    df_user['rating_value'] = df_user['rating_value'].astype(float)
    top_rated_games = df_user.sort_values(by='rating_value', ascending=False)['objectid'].tolist()
    top_rated_games = top_rated_games[:15]

    # Function that takes in game title as input and outputs most similar games
    def get_recommendations(game, similarities=similarities):
        # Get the index of the name that matches the game_name
        try:
            game = int(game)
            idx = df.loc[df['BgNumber'] == game].index[0]

            # Get the pairwsie similarity scores of all games with that game
            sim_scores = list(enumerate(similarities[idx]))

            # Sort the games based on the similarity scores
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

            # Get the scores of the 15 most similar games
            sim_scores = sim_scores[1:16]

            # Get the game indices
            game_indices = [i[0] for i in sim_scores]
            game_ids = [df['BgNumber'].iloc[i] for i in game_indices]
            game_names = [df['BgName'].iloc[i] for i in game_indices]
            similarities = [i[1] for i in sim_scores]
            
        except IndexError:
            pass
        except Exception:
            idx = df.loc[df['BgName'] == game].index[0]

        # Return the top most similar games
        return [(game_ids[i], game_names[i], similarities[i]) for i in range(len(game_indices))]
    

    # Step 2: Find similar games for each of the user's top-rated games
    similar_games = []
    for objectid in top_rated_games:
        # Get the similarity scores for this game
        game_similarities = get_recommendations(objectid)
        # Sort the games by similarity score, and keep the top 5
        similar_games.extend(sorted(enumerate(game_similarities), key=lambda x: x[1], reverse=True)[:15])

    sorted_recommendations = sorted(similar_games, key=lambda x: x[1][2], reverse=True)

        # Step 4: Remove duplicates
    sorted_recommendations = list(dict.fromkeys(sorted_recommendations))

    # Step 5: Remove games that have already been rated
    user_objectids = set(df_user['objectid'])
    filtered_recommendations = [(idx, rec) for idx, rec in sorted_recommendations if rec[0] not in user_objectids]


    printed_games = set()
    for game in filtered_recommendations:
        # do not print duplicate games
        if game[1][1] not in printed_games:
            printed_games.add(game[1][1])


    #printed_games = set() -> IN THIS PROGRAM DEFINED OUTSIDE OF OVERARCHING FUNCTION
    #printed_amount = 0 -> IN THIS PROGRAM DEFINED OUTSIDE OF OVERARCHING FUNCTION

    def add_recommended_games():
        global printed_games
        global printed_amount
        
        random_recommendations = random.choices(filtered_recommendations, k=(10 - printed_amount))
        for game in random_recommendations:
            name = game[1][1]
            if name not in printed_games:
                printed_games.add(name)
                printed_amount += 1

    add_recommended_games()

    return printed_games






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
        recommendations = get_recommendations_by_callback(bgg_user)

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









        

