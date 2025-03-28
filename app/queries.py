# Native Libraries
from typing import Literal

# Third-Party Libraries
import duckdb
from duckdb import DuckDBPyRelation
from pandas import DataFrame

# Local Modules
from src.core.settings import aws_credentials
from src.core.tools.s3 import s3_client


for credential in ('region', 'access_key_id', 'secret_access_key'):
    duckdb.sql(f"SET s3_{credential}='{getattr(aws_credentials, credential)}';")


sections: tuple[str] = ('game', 'movie')
section_paths: dict[str, str] = {}


for section in sections:
    section_paths[f'{section.title()}s'] = s3_client.get_file_path(
        date='2024-10-30',
        layer='cleansed',
        file_name=f'metacritic_{section}',
        file_extension='parquet',
    )


def get_section_data(section: str) -> tuple[DuckDBPyRelation, DataFrame]:
    duckdb.sql(
        f"""
        CREATE TEMPORARY TABLE IF NOT EXISTS {section} AS (
            SELECT * FROM read_parquet('{section_paths.get(section)}')
        )
        """
    )
    relation = duckdb.sql(f'SELECT * FROM {section}')

    return relation, relation.df()


def get_popularity(section: str) -> DataFrame:
    name = 'movie' if section == 'Movies' else 'name'

    popularity_df = duckdb.sql(
        f"""
        SELECT
            {name}  AS "Name",
            EXTRACT(YEAR FROM released_on) AS "Released On",
            (critic_ratings + user_ratings) AS "Ratings"

        FROM {section}
        ORDER BY 3 DESC;
        """
    ).df()

    return popularity_df


def get_aggregated(by: str, alias: str) -> DataFrame:
    aggregated_df = duckdb.sql(f"""
        SELECT {by} as "{by.title()}", COUNT(*) AS "{alias}"
        FROM games
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 50;
    """).df()
    return aggregated_df
