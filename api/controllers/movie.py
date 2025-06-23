from sqlalchemy.orm import joinedload, Session
import app.models as m
import app.schema as s
import sqlalchemy as sa


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
    else:
        order = get_order(sort_by, is_reverse)
        return (
            sa.select(m.Movie)
            .where(m.Movie.is_deleted.is_(False))
            .order_by(order)
            .options(joinedload(m.Movie.translations))
        )
