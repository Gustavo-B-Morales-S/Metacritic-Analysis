# Native Libraries
from typing import Iterable

# Thirdy-Party Libraries
from loguru import logger
from selectolax.parser import HTMLParser, Node

# Local Modules
from src.core.contracts import HTTPResponse


SELECTORS: dict[str, str] = {
    'critic_ratings': '.c-reviewsSection_header-critic .c-reviewsStats span',
    'user_ratings': '.c-reviewsSection_header-user .c-reviewsStats span',
    'reviews_and_ratings': '.c-productScoreInfo_reviewsTotal',
    'scores': '.c-siteReviewScore_background span',
    'genre': '.c-genreList .c-globalButton_label',
    'movie': '.c-productHero_title',
    'awards': '.c-productionAwardSummary_awards .c-productionAwardSummary_award',
    'must_see': '.c-productScoreInfo_must',
    'details': '.c-movieDetails_sectionContainer',
}

def parse_movies_data(responses: Iterable[HTTPResponse]) -> list[dict[str, str | int]]:
    """Parses Metacritic data from an iterable of HTTP responses."""
    logger.info('Starting processing responses')
    json_like: list[dict[str, str | int]] = []

    for response in responses:
        logger.info(f'Processing response from {response.url}.')
        tree: HTMLParser = HTMLParser(response.content)

        try:
            for detail in tree.css(SELECTORS['details']):
                contents = detail.css('span')

                label: str = contents[0].text()
                content: str = contents[1].text()

                if label == 'Release Date':
                    release_date: str = content

                if label == 'Duration':
                    duration: str = content

            critic_ratings, user_ratings = tree.css(SELECTORS['reviews_and_ratings'])
            critic_score, user_score, *_ = tree.css(SELECTORS['scores'])

            critic_ratings_category: Node = tree.css(SELECTORS['critic_ratings'])
            user_rating_category: Node = tree.css(SELECTORS['user_ratings'])

            genre: Node = tree.css_first(SELECTORS['genre'])
            movie: Node = tree.css_first(SELECTORS['movie'])
            must_see: Node = tree.css(SELECTORS['must_see'])
            awards: Node = tree.css(SELECTORS['awards'])

            json_like.append({
                'movie': movie.text(),
                'genre': genre.text().strip(),
                'awards': len(awards),
                'must_see': 1 if bool(must_see) else 0,
                'released_on': release_date,
                'duration': duration,
                'user_score': user_score.text(),
                'critic_score': critic_score.text(),
                'user_ratings': user_ratings.text(),
                'critic_ratings': critic_ratings.text(),
                'user_positive_reviews': user_rating_category[1].text(),
                'user_mixed_reviews': user_rating_category[3].text(),
                'user_negative_reviews': user_rating_category[5].text(),
                'critic_positive_reviews': critic_ratings_category[1].text(),
                'critic_mixed_reviews': critic_ratings_category[3].text(),
                'critic_negative_reviews': critic_ratings_category[5].text(),
            })
        except:
            continue

    return json_like
