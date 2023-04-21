from sqlalchemy import create_engine, text, Table, MetaData, Column, Integer, insert, select
from sqlalchemy.exc import IntegrityError
import pandas as pd


# create engine for connection with database
def create_db_connection(server, database):
    return create_engine("mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=" + server + ";DATABASE=" + database + ";Trusted_Connection=yes;")


def create_initial_df(engine):
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

    return bgg_df