from dash import dcc

import sys
sys.path.append('C:/Users/maart/OneDrive/Bureaublad/Syntra/Eindwerk/Dash-Plotly') # make sure python will look into the entire 'Dash-Plotly' folder as well

from settings.config import * # import global variables defined in 'config.py'

##### define components
### RANKING
def comp_filter_ranking():
    filter_ranking = dcc.Dropdown(['Top 100', 'Top 250', 'Top 1000', 'Alle bordspellen'], 'Top 1000', id='filter_ranking')
    return filter_ranking

### PLAYERS (amount)
def comp_filter_players():
    filter_players = dcc.Dropdown(['1', '2', '3','4', '5', '6', '7+'], id='filter_players')
    return filter_players

### PLAYTIME
def comp_filter_playtime():
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
    return filter_playtime

### COMPLEXITY
def comp_filter_complexity():
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
    return filter_complexity


### DESIGNER(S)
def comp_filter_designer(bgg_df):
    # Create list containing all unique designers
    def get_designer_list(designer_string):
        global all_designers
        try:
            temp_list = designer_string.split(', ')
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
    return filter_designer