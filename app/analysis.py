# Third-Party Libraries
import duckdb
import streamlit as st
import altair as alt

# Local Modules
from app.queries import get_aggregated, get_section_data, get_popularity


# Sidebar Settings & ETC.
with st.sidebar:
    role_label = st.radio(
        'Choose a role:',
        ('Administrator', 'User')
    )
    section_label: str = st.radio(
        'Choose a section: ',
        ('Games', 'Movies'),
    )

    with st.spinner('Loading data..'):
        section_relation, section_df = get_section_data(section=section_label)
        st.success('Done!')


def render_headers() -> None:
    st.title(f'{section_label} Data')

    games, genres, developers, publishers = st.columns(4)

    if section_label == 'Games':
        games.metric(label='Total Games', value=len(section_df))
        genres.metric(label='Genres', value=len(section_df['genre'].unique()))
        developers.metric(label='Developers', value=len(section_df['developer'].unique()))
        publishers.metric(label='Publishers', value=len(section_df['publisher'].unique()))


def render_date_slider(minimum_year: int, maximum_year: int) -> None:
    start_year, end_year = st.slider(
        label='Year',
        min_value=minimum_year,
        max_value=maximum_year,
        value=(minimum_year, maximum_year),
    )
    return start_year, end_year


def render_popularity_graph() -> None:
    popularity_df = get_popularity(section=section_label)

    minimum_year, maximum_year = popularity_df['Released On'].agg(['min', 'max'])
    start_year, end_year = render_date_slider(minimum_year, maximum_year)

    filtered_by_year = (
        popularity_df[popularity_df['Released On'].between(start_year, end_year)]
    )

    chart = (
        alt.Chart(filtered_by_year.head(50))
        .mark_bar()
        .encode(
            x='Ratings:Q',
            y=alt.Y('Name:N', sort='-x')
        )
        .properties(
            width=700,
            height=700,
            title='Top 50 Most Popular Games by Period'
        )
    )
    st.altair_chart(chart)

def render_aggregations():
    if section_label == 'Games':
        to_aggregate = (
            ('platform', 'Popularity'),
            ('genre', 'Popularity'),
            ('developer', 'Games Developed'),
            ('publisher', 'Games Published'),
        )
        for column, alias in to_aggregate:
            st.bar_chart(
                data=get_aggregated(by=column, alias=alias),
                x=column.title(),
                y=alias.title()
            )

if __name__ == '__main__':
    render_headers()
    render_popularity_graph()
    render_aggregations()


    if role_label == 'Administrator':
        st.subheader(f'Ad-Hoc Query')
        query = st.text_input('Query:', f'SELECT * FROM {section_label}')
        table = duckdb.sql(query)
        st.write(table.df())
