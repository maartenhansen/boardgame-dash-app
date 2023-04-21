import requests
import time
import pandas as pd
import xml.etree.ElementTree as ET
import random

import sys
sys.path.append('C:/Users/maart/OneDrive/Bureaublad/Syntra/Eindwerk/Dash-Plotly/functions') # make sure python will look into the 'functions' folder as well in order to find 'sql_bgdash' module
from sql_bg_dash import create_initial_df, create_db_connection, create_engine

#### Define necessarry variables for function used in callback (necessary as global variables) ---> DO NOT DELETED: IS ASSOSCIATED WITH (get_recommendations)
#printed_games = set() # WILL BE ACCESSED IN FUCNTION BELOW AS GLOBAL VARIABLE
#printed_amount = 0 # WILL BE ACCESSED IN FUCNTION BELOW AS GLOBAL VARIABLE

######### FUNCTION TO GET ALL RECOMMENDATIONS: WILL BE USED IN THE CALLBACK FUNCTION
def get_recommendations(bgg_username):
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
    engine = create_db_connection(server, database)

    # create initial dataframe from fact table
    df = create_initial_df(engine)


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
    
    # Step 6, return only the game names so that they can be filtered
    rec_names = set()
    for game in filtered_recommendations:
        # do not print duplicate games
        if game[1][1] not in rec_names:
            rec_names.add(game[1][1])

    return rec_names