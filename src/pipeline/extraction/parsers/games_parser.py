# Native Libraries
from typing import Iterable

# Third-Party Libraries
from selectolax.parser import HTMLParser, Node
from loguru import logger

# Local Modules
from src.core.tools.mongodb import HTTPResponse


SELECTORS: dict[str, str] = {
    'publisher': '.c-gameDetails_Distributor .g-outer-spacing-left-medium-fluid',
    'critic_ratings': '.c-reviewsSection_header-critic .c-reviewsStats span',
    'user_ratings': '.c-reviewsSection_header-user .c-reviewsStats span',
    'reviews_and_ratings': '.c-productScoreInfo_reviewsTotal',
    'release_date': '.g-text-xsmall .u-text-uppercase',
    'developer': '.c-gameDetails_Developer li',
    'scores': '.c-siteReviewScore_background span',
    'genre': 'a.c-globalButton_container',
    'platform': '.c-gamePlatformLogo',
    'game': '.c-productHero_title',
    'must_play': '.c-productScoreInfo_must',
}


def parse_games_data(responses: Iterable[HTTPResponse]) -> list[dict[str, str | int]]:
    """
    Parses Metacritic game data from an iterable of HTTP response documents.

    Args:
        response_documents (Iterable[HTTPResponse]): A collection of HTTP response
            documents containing HTML content to be parsed.

    Returns:
        list[dict[str, str | int]]: A list of dictionaries where each dictionary
        represents a game and its attributes, such as name, platform, genre, scores,
        and ratings.
    """
    logger.info('Starting response processing')
    json_like: list[dict[str, str | int]] = []

    for response in responses:
        logger.info(f'Processing response from {response.url}.')
        tree: HTMLParser = response.content

        try:
            critic_ratings, user_ratings = tree.css(SELECTORS['reviews_and_ratings'])
            critic_score, user_score, *_ = tree.css(SELECTORS['scores'])

            critic_ratings_category: Node = tree.css(SELECTORS['critic_ratings'])
            user_rating_category: Node = tree.css(SELECTORS['user_ratings'])

            release_date: Node = tree.css_first(SELECTORS['release_date'])
            developer: Node = tree.css_first(SELECTORS['developer'])
            publisher: Node = tree.css_first(SELECTORS['publisher'])
            platform: Node = tree.css_first(SELECTORS['platform'])
            must_play: Node = tree.css(SELECTORS['must_play'])
            genre: Node = tree.css_first(SELECTORS['genre'])
            game: Node = tree.css_first(SELECTORS['game'])

            json_like.append({
                'name': game.text(),
                'platform': platform.text().strip(),
                'genre': genre.text().strip(),
                'must_play': 1 if bool(must_play) else 0,
                'developer': developer.text().strip(),
                'publisher': publisher.text(),
                'released_on': release_date.text(),
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
