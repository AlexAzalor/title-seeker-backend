from datetime import datetime
import re
from typing import List
import filetype
from fastapi import UploadFile, HTTPException, status
from fastapi.routing import APIRoute
from app import schema as s
from app import models as m

from app.logger import log


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def get_file_extension(file: UploadFile):
    extension = filetype.guess_extension(file.file)

    if not extension:
        log(log.ERROR, "Extension not found for image [%s]", file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extension not found")

    return extension


def mark_as_deleted():
    current_timestamp = datetime.now().strftime("%y-%m-%d_%H:%M:%S:%f")

    return f"deleted-{current_timestamp}"


def get_error_message(lang: s.Language, text_uk: str, text_en: str) -> str:
    return text_uk if lang == s.Language.UK else text_en


def extract_values(input_string: List[str]) -> List[List[int]]:
    values_list: List[List[int]] = []

    for value in input_string:
        pattern = re.compile(r".*?\(([\d,]+)\)")
        match = pattern.match(value)

        if match:
            numbers_str = match.group(1)
            numbers_list = [int(num) for num in numbers_str.split(",")]
            values_list.append(numbers_list)
    return values_list


def extract_word(input_string: List[str]) -> List[str]:
    words_list: List[str] = []

    for word in input_string:
        pattern = re.compile(r"(.*?)\([\d,]+\)")
        match = pattern.match(word)

        if match:
            word = match.group(1).strip()
            words_list.append(word)
        else:
            words_list.append(word.strip())
    return words_list


def calculate_average_rating(ratings: list[m.Rating], attribute: str) -> float:
    """
    Calculate the average of a specific attribute from a list of ratings.

    :param ratings: List of Rating objects.
    :param attribute: The name of the attribute to calculate the average for.
    :return: The average value rounded to 2 decimal places.
    """
    if not ratings:
        return 0.0

    # Use getattr to dynamically access the attribute
    values = [getattr(rating, attribute, 0) for rating in ratings if getattr(rating, attribute, None) is not None]
    return round(sum(values) / len(values), 2) if values else 0.0


def process_movie_rating(movie: m.Movie):
    """
    Process the movie rating and calculate averages for various criteria.
    """
    movie_ratings = movie.ratings

    movie.average_rating = calculate_average_rating(movie_ratings, "rating")
    movie.ratings_count = len(movie_ratings)

    movie.average_by_criteria = {
        "acting": calculate_average_rating(movie_ratings, "acting"),
        "plot_storyline": calculate_average_rating(movie_ratings, "plot_storyline"),
        "script_dialogue": calculate_average_rating(movie_ratings, "script_dialogue"),
        "music": calculate_average_rating(movie_ratings, "music"),
        "enjoyment": calculate_average_rating(movie_ratings, "enjoyment"),
        "production_design": calculate_average_rating(movie_ratings, "production_design"),
        "visual_effects": calculate_average_rating(movie_ratings, "visual_effects")
        if movie.rating_criterion == s.RatingCriterion.VISUAL_EFFECTS
        else None,
        "scare_factor": calculate_average_rating(movie_ratings, "scare_factor")
        if movie.rating_criterion == s.RatingCriterion.SCARE_FACTOR
        else None,
        "humor": calculate_average_rating(movie_ratings, "humor")
        if movie.rating_criterion == s.RatingCriterion.HUMOR
        else None,
        "animation_cartoon": calculate_average_rating(movie_ratings, "animation_cartoon")
        if movie.rating_criterion == s.RatingCriterion.ANIMATION_CARTOON
        else None,
    }
