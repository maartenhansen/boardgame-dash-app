import dash
from dash import html, dcc, dash_table, callback, Output, Input
import plotly.graph_objs as go
import plotly.express as px
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

# loads the "sketchy" template and sets it as the default
load_figure_template("superhero")


# import custom handwritten functions
import sys
sys.path.append('C:/Users/maart/OneDrive/Bureaublad/Syntra/Eindwerk/Dash-Plotly') # make sure python will look into the entire 'Dash-Plotly' folder as well
from functions.sql_bg_dash import create_db_connection, get_game_amount_by_designer_top_x, get_game_name_by_designer_top_x

# Define page & path
dash.register_page(__name__, path='/stats/') # '/' = homepage

##### Incorporporate data into app
# define servername & database name
server = 'DESKTOP-4K7IERR\SYNTRA_MAARTEN'
database = 'BoardgameProject'

# create engine for connection with database
engine = create_db_connection(server, database)

### Create barchart with amount of times designers are in top 100
df_top_x_designers = get_game_amount_by_designer_top_x(engine, 100)
fig_top_x_designers =  px.bar(df_top_x_designers, x='Auteur', y='Aantal')

### Create datatable to show the exact games of the designers in the above barchart
df_top_x_designers_gamenames = get_game_name_by_designer_top_x(engine, 100)
df_top_x_designers_gamenames_cols_to_display = [{"name": "Bordspel", "id": "Bordspel"}]
top_x_designers_gamenames_table = dash_table.DataTable(
    data=df_top_x_designers_gamenames.to_dict('records'),
    columns=df_top_x_designers_gamenames_cols_to_display,
    page_size=10,
    id='top_x_designers_gamenames',
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
    style_as_list_view=True
)



layout = html.Div([
    html.Div([
        html.H1(children='Statistieken'),
        html.Div([
            html.H2(children='Bordspellen in de top 100'),
            dcc.Graph(
                id='designers_in_top_100', 
                figure=fig_top_x_designers,
                config={'displayModeBar': False}
                ),
            ], style={'width': '47.5%', 'display': 'inline-block', 'marginRight': '5%'}),
        html.Div([
            html.H2(children='Bordspellen in de top 100'),
            top_x_designers_gamenames_table
            ], style={'width': '47.5%', 'display': 'inline-block', 'vertical-align': 'top'}
            ),
    ], style={'padding': 40, 'flex': 1})
])

###### Add callbacks (allows components to interact)
@callback(
    Output(component_id='top_x_designers_gamenames', component_property='data'),
    Input(component_id='designers_in_top_100', component_property='hoverData')
)
def update_top_x_designers_gamenames(hoverdata):
    try:
        df_temp = df_top_x_designers_gamenames.query('DesignerName == "{}"'.format(hoverdata['points'][0]['x'])) # get author value from hoverdata, and use it in the query
        df_dict = df_temp.to_dict('records') # change dataframe to dictionary, as a df cannot be returned
        print(df_dict)
        return df_dict
    except Exception as err: # No games will be returned if no designer is selected
        print(err)

