from datetime import datetime
from sqlalchemy.orm import Session
import app.models as m
import app.schema as s
import sqlalchemy as sa
from fastapi import HTTPException, status
from app.logger import log


def get_movie_data(movie: m.Movie, db: Session, lang: s.Language, current_user: m.User | None = None) -> s.MovieOut:
    """Get detailed movie data including visual profile, ratings, and related information."""

    movie_id = movie.id
    movie_key = movie.key

    user_rating = None
    owner = None

    if current_user and current_user.role == s.UserRole.OWNER.value:
        owner = current_user
    else:
        owner = db.scalar(sa.select(m.User).where(m.User.role == s.UserRole.OWNER.value))

    if not owner:
        log(log.ERROR, "Owner not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    owner_rating = next((r for r in movie.ratings if r.user_id == owner.id), None)
    if not owner_rating:
        log(log.ERROR, "Owner rating for movie [%s] not found", movie_key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner rating not found")

    visual_profile = movie.get_visual_profile(owner.id)
    if not visual_profile:
        log(log.ERROR, "Visual profile for movie [%s] not found", movie_key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visual profile not found")

    if current_user and current_user.role != s.UserRole.OWNER.value:
        user_rating = next((r for r in movie.ratings if current_user and r.user_id == current_user.id), None)

    # Only owner's for now
    visual_profile_out = s.VisualProfileData(
        key=visual_profile.category.key,
        name=visual_profile.category.get_name(lang),
        description=visual_profile.category.get_description(lang),
        criteria=[
            s.VisualProfileCriterionData(
                key=title_rating.criterion.key,
                name=title_rating.criterion.get_name(lang),
                description=title_rating.criterion.get_description(lang),
                rating=title_rating.rating,
            )
            for title_rating in sorted(visual_profile.ratings, key=lambda x: x.order)
        ],
    )

    # For anonymous users
    # The .get() method only returns the default value if the key does not exist in the dictionary. If the key exists but its value is None, .get() will return None instead of the default value.
    movie_avg_rating = movie.average_by_criteria
    overral_rating_criteria = s.BaseRatingCriteria(
        acting=movie_avg_rating.get("acting") or 0.01,
        plot_storyline=movie_avg_rating.get("plot_storyline") or 0.01,
        script_dialogue=movie_avg_rating.get("script_dialogue") or 0.01,
        music=movie_avg_rating.get("music") or 0.01,
        enjoyment=movie_avg_rating.get("enjoyment") or 0.01,
        production_design=movie_avg_rating.get("production_design") or 0.01,
        visual_effects=movie_avg_rating.get("visual_effects"),
        scare_factor=movie_avg_rating.get("scare_factor"),
        humor=movie_avg_rating.get("humor"),
        animation_cartoon=movie_avg_rating.get("animation_cartoon"),
    )

    # For authenticated users
    is_visual_effects = movie.rating_criterion == s.RatingCriterion.VISUAL_EFFECTS.value
    is_scary = movie.rating_criterion == s.RatingCriterion.SCARE_FACTOR.value
    is_humor = movie.rating_criterion == s.RatingCriterion.HUMOR.value
    is_animation_cartoon = movie.rating_criterion == s.RatingCriterion.ANIMATION_CARTOON.value
    user_rating_criteria = (
        s.BaseRatingCriteria(
            acting=user_rating.acting,
            plot_storyline=user_rating.plot_storyline,
            script_dialogue=user_rating.script_dialogue,
            music=user_rating.music,
            enjoyment=user_rating.enjoyment,
            production_design=user_rating.production_design,
            visual_effects=user_rating.visual_effects if is_visual_effects else None,
            scare_factor=user_rating.scare_factor if is_scary else None,
            humor=user_rating.humor if is_humor else None,
            animation_cartoon=user_rating.animation_cartoon if is_animation_cartoon else None,
        )
        if user_rating
        else None
    )

    genre_matches = {(mg.genre_id): mg.percentage_match for mg in db.query(m.movie_genres).filter_by(movie_id=movie_id)}
    subgenre_matches = {
        (mg.subgenre_id): mg.percentage_match for mg in db.query(m.movie_subgenres).filter_by(movie_id=movie_id)
    }
    specification_matches = {
        (mg.specification_id): mg.percentage_match
        for mg in db.query(m.movie_specifications).filter_by(movie_id=movie_id)
    }
    keyword_matches = {
        (mg.keyword_id): mg.percentage_match for mg in db.query(m.movie_keywords).filter_by(movie_id=movie_id)
    }
    action_time_matches = {
        (mg.action_time_id): mg.percentage_match for mg in db.query(m.movie_action_times).filter_by(movie_id=movie_id)
    }

    return s.MovieOut(
        key=movie_key,
        title=movie.get_title(lang),
        title_en=movie.get_title(s.Language.EN) if lang == s.Language.UK else None,
        description=movie.get_description(lang),
        location=movie.get_location(lang),
        poster=movie.poster,
        budget=movie.formatted_budget,
        duration=movie.formatted_duration(lang.value),
        domestic_gross=movie.formatted_domestic_gross,
        worldwide_gross=movie.formatted_worldwide_gross,
        release_date=movie.release_date if movie.release_date else datetime.now(),
        # Visual Profile
        visual_profile=visual_profile_out,
        # Rating
        ratings_count=movie.ratings_count,
        rating_criterion=s.RatingCriterion(movie.rating_criterion),
        # Owner rating
        owner_rating=owner_rating.rating,
        # Main AVERAGE rating
        overall_average_rating=movie.average_rating,
        overall_average_rating_criteria=overral_rating_criteria,
        # User rating
        user_rating=user_rating.rating if user_rating else None,
        user_rating_criteria=user_rating_criteria,
        actors=[
            s.MovieActorOut(
                key=char.actor.key,
                full_name=char.actor.full_name(lang),
                character_name=char.character.get_name(lang),
                avatar_url=char.actor.avatar,
                born_location=char.actor.get_born_location(lang),
                age=char.actor.age,
                born=char.actor.born,
                died=char.actor.died,
            )
            for char in sorted(movie.characters, key=lambda x: x.order)
        ],
        directors=[
            s.MoviePersonOut(
                key=director.key,
                full_name=director.full_name(lang),
                avatar_url=director.avatar if director.avatar else "no avatar",
                born_location=director.get_born_location(lang),
                age=director.age,
                born=director.born,
                died=director.died,
            )
            for director in movie.directors
        ],
        genres=[
            s.MovieFilterItem(
                key=genre.key,
                name=genre.get_name(lang),
                description=genre.get_description(lang),
                percentage_match=genre_matches.get(genre.id, 0.0),
            )
            for genre in movie.genres
        ],
        subgenres=[
            s.MovieFilterItem(
                key=subgenre.key,
                subgenre_parent_key=subgenre.genre.key,
                name=subgenre.get_name(lang),
                description=subgenre.get_description(lang),
                percentage_match=subgenre_matches.get(subgenre.id, 0.0),
            )
            for subgenre in movie.subgenres
        ],
        specifications=[
            s.MovieFilterItem(
                key=specification.key,
                name=specification.get_name(lang),
                description=specification.get_description(lang),
                percentage_match=specification_matches.get(specification.id, 0.0),
            )
            for specification in movie.specifications
        ],
        keywords=[
            s.MovieFilterItem(
                key=keyword.key,
                name=keyword.get_name(lang),
                description=keyword.get_description(lang),
                percentage_match=keyword_matches.get(keyword.id, 0.0),
            )
            for keyword in movie.keywords
        ],
        action_times=[
            s.MovieFilterItem(
                key=action_time.key,
                name=action_time.get_name(lang),
                description=action_time.get_description(lang),
                percentage_match=action_time_matches.get(action_time.id, 0.0),
            )
            for action_time in movie.action_times
        ],
        related_movies=[
            s.RelatedMovieOut(
                key=related_movie.key,
                poster=related_movie.poster,
                title=related_movie.get_title(lang),
                relation_type=s.RelatedMovie(related_movie.relation_type),
            )
            for related_movie in movie.related_movies_collection
        ]
        if movie.relation_type
        else None,
        shared_universe_order=movie.shared_universe_order,
        shared_universe=s.SharedUniverseOut(
            key=movie.shared_universe.key,
            name=movie.shared_universe.get_name(lang),
            description=movie.shared_universe.get_description(lang),
            movies=[
                s.SharedUniverseMovies(
                    key=shared_movie.key,
                    title=shared_movie.get_title(lang),
                    poster=shared_movie.poster,
                    order=shared_movie.shared_universe_order,
                )
                for shared_movie in movie.shared_universe.get_sorted_movies()
            ],
        )
        if movie.shared_universe
        else None,
    )


def get_main_genres_for_movies(db: Session, movie_ids: list[int], lang: s.Language):
    # Fetch all genre matches for these movies
    genre_rows = db.execute(
        sa.select(
            m.movie_genres.c.movie_id,
            m.movie_genres.c.genre_id,
            m.movie_genres.c.percentage_match,
        ).where(m.movie_genres.c.movie_id.in_(movie_ids))
    ).all()
    # Fetch all genres needed
    genre_ids = {row.genre_id for row in genre_rows}
    genres = db.query(m.Genre).filter(m.Genre.id.in_(genre_ids)).all()
    genre_map = {genre.id: genre for genre in genres}

    # Build a dict: movie_id -> (genre, percentage_match)
    main_genre_map = {}
    from collections import defaultdict

    movie_genre_matches = defaultdict(list)
    for row in genre_rows:
        movie_genre_matches[row.movie_id].append(row)
    for movie_id, rows in movie_genre_matches.items():
        # Pick the genre with the highest percentage_match
        best_row = max(rows, key=lambda r: r.percentage_match)
        genre = genre_map.get(best_row.genre_id)
        if genre:
            genre_name = genre.get_name(lang)
            main_genre_map[movie_id] = f"{genre_name} ({best_row.percentage_match}%)"
        else:
            main_genre_map[movie_id] = "No main genre"
    return main_genre_map


def get_user_order(sort_by: s.SortBy, is_reverse: bool):
    """Get the order for authenticated user"""

    if sort_by == s.SortBy.RATED_AT:
        return m.Rating.updated_at.desc() if is_reverse else m.Rating.updated_at.asc()
    if sort_by == s.SortBy.RELEASE_DATE:
        return m.Movie.release_date.desc() if is_reverse else m.Movie.release_date.asc()
    if sort_by == s.SortBy.RATINGS_COUNT:
        return m.Movie.ratings_count.desc() if is_reverse else m.Movie.ratings_count.asc()
    if sort_by == s.SortBy.RANDOM:
        return sa.func.random()

    return m.Rating.rating.desc() if is_reverse else m.Rating.rating.asc()


def get_order(sort_by: s.SortBy, is_reverse: bool):
    if sort_by == s.SortBy.RELEASE_DATE:
        return m.Movie.release_date.desc() if is_reverse else m.Movie.release_date.asc()
    if sort_by == s.SortBy.RATING:
        return m.Movie.average_rating.desc() if is_reverse else m.Movie.average_rating.asc()
    if sort_by == s.SortBy.RATINGS_COUNT:
        return m.Movie.ratings_count.desc() if is_reverse else m.Movie.ratings_count.asc()
    if sort_by == s.SortBy.RANDOM:
        return sa.func.random()

    return m.Movie.id.desc() if is_reverse else m.Movie.id.asc()


def build_movie_query(sort_by: s.SortBy, is_reverse: bool, current_user: m.User | None):
    """Build a query for movies based on the sort criteria and user context."""

    if current_user:
        user_order = get_user_order(sort_by, is_reverse)
        return (
            sa.select(m.Movie)
            .join(m.Rating, m.Rating.movie_id == m.Movie.id)
            .where(m.Rating.user_id == current_user.id)
            .order_by(user_order)
        )
    # fdfd
    else:
        order = get_order(sort_by, is_reverse)
        return sa.select(m.Movie).where(m.Movie.is_deleted.is_(False)).order_by(order)
