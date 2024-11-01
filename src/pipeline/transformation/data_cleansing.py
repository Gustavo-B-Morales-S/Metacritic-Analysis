# Native Libraries
from typing import Literal

# Thirdy-Party Libraries
import pandas as pd
from awswrangler import s3
from pandas import DataFrame, Index

# Local Modules
from src.core.tools.s3 import s3_client


def cleanse_data(section: Literal['game', 'movie']) -> None:
    '''
    Reads JSON data from an S3 bucket, performs data cleansing, and writes the
    cleansed data as a Parquet file back to S3.

    Args:
        section (Literal['game', 'movie']): The content type for which data
            cleansing is to be performed. Can be either 'game' or 'movie'.

    Returns:
        None
    '''
    # Getting JSON file path & reading JSON data into a Pandas Dataframe
    s3_json_file_path: str = s3_client.get_file_path(
        layer='raw', file_name=f'metacritic_{section}', file_extension='json'
    )
    df: DataFrame = s3.read_json(path=s3_json_file_path)

    # Removing descriptions from numeric attributes
    numeric_columns: Index[str] = df.iloc[:, -8:].columns
    df.replace(
        dict.fromkeys(numeric_columns, r'[^0-9.]'), '', regex=True, inplace=True
    )

    # Assigns the appropriate type to numeric, date, and timestamp columns
    if section == 'movie':
        df['duration'] = pd.to_timedelta(df['duration'])
        df['duration'] = df['duration'].dt.components.apply(
            lambda x: f'{int(x.hours):02}:{int(x.minutes):02}:{int(x.seconds):02}', axis=1,
        )

    df['released_on'] = pd.to_datetime(df['released_on'], format='%b %d, %Y')

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], downcast='integer', errors='coerce')

    # Getting file output path & writing Dataframe data as a Parquet file into S3
    file_path: str = s3_client.get_file_path(
        layer='cleansed', file_name=f'metacritic_{section}', file_extension='parquet'
    )
    s3_client.upload_parquet(df=df, file_path=file_path, index=False)
