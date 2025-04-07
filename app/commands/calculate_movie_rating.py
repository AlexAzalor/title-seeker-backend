from app.database import db
import sqlalchemy as sa
from app import models as m
from app import schema as s


def calculate_movie_rating():
    with db.begin() as session:
        movies = session.scalars(sa.select(m.Movie)).all()

        for movie in movies:
            movie_ratings = movie.ratings
            if not movie_ratings:
                continue
            average_rating = round(sum([rating.rating for rating in movie_ratings]) / len(movie_ratings), 2)

            average_acting = round(sum([rating.acting for rating in movie_ratings]) / len(movie_ratings), 2)
            average_plot_storyline = round(
                sum([rating.plot_storyline for rating in movie_ratings]) / len(movie_ratings), 2
            )
            average_script_dialogue = round(
                sum([rating.script_dialogue for rating in movie_ratings]) / len(movie_ratings), 2
            )
            average_music = round(sum([rating.music for rating in movie_ratings]) / len(movie_ratings), 2)
            average_enjoyment = round(sum([rating.enjoyment for rating in movie_ratings]) / len(movie_ratings), 2)
            average_production_design = round(
                sum([rating.production_design for rating in movie_ratings]) / len(movie_ratings), 2
            )
            if movie.rating_criterion == s.RatingCriterion.VISUAL_EFFECTS:
                # print('movie_ratings----------------', movie_ratings)
                average_visual_effects = round(
                    sum([rating.visual_effects for rating in movie_ratings]) / len(movie_ratings), 2
                )
            if movie.rating_criterion == s.RatingCriterion.SCARE_FACTOR:
                average_scare_factor = round(
                    sum([rating.scare_factor for rating in movie_ratings]) / len(movie_ratings), 2
                )
            if movie.rating_criterion == s.RatingCriterion.HUMOR:
                average_humor = round(sum([rating.humor for rating in movie_ratings]) / len(movie_ratings), 2)
            if movie.rating_criterion == s.RatingCriterion.ANIMATION_CARTOON:
                average_animation_cartoon = round(
                    sum([rating.animation_cartoon for rating in movie_ratings]) / len(movie_ratings), 2
                )

            movie.average_by_criteria = {
                "acting": average_acting,
                "plot_storyline": average_plot_storyline,
                "script_dialogue": average_script_dialogue,
                "music": average_music,
                "enjoyment": average_enjoyment,
                "production_design": average_production_design,
                "visual_effects": average_visual_effects
                if movie.rating_criterion == s.RatingCriterion.VISUAL_EFFECTS
                else None,
                "scare_factor": average_scare_factor
                if movie.rating_criterion == s.RatingCriterion.SCARE_FACTOR
                else None,
                "humor": average_humor if movie.rating_criterion == s.RatingCriterion.HUMOR else None,
                "animation_cartoon": average_animation_cartoon
                if movie.rating_criterion == s.RatingCriterion.ANIMATION_CARTOON
                else None,
            }

            movie.average_rating = average_rating
            movie.ratings_count = len(movie_ratings)

            session.flush()

        session.commit()
