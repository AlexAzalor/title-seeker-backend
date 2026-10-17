import base64
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session

import app.models as m
from api.controllers.movie import get_ranked_similar_movies
import app.schema as s

MOVIE_ENTITY = "movie"
MOVIE_DESCRIPTION_UPDATED = "movie.description.updated"
MOVIE_BOX_OFFICE_UPDATED = "movie.box_office.updated"
MOVIE_ACTORS_UPDATED = "movie.actors.updated"
MOVIE_DIRECTORS_UPDATED = "movie.directors.updated"
MOVIE_RATING_UPDATED = "movie.rating.updated"
MOVIE_RATING_CREATED = "movie.rating.created"
MOVIE_VISUAL_PROFILE_UPDATED = "movie.visual_profile.updated"
MOVIE_GENRES_UPDATED = "movie.genres.updated"
MOVIE_SPECIFICATIONS_UPDATED = "movie.specifications.updated"
MOVIE_KEYWORDS_UPDATED = "movie.keywords.updated"
MOVIE_ACTION_TIMES_UPDATED = "movie.action_times.updated"
MOVIE_SIMILAR_MOVIES_UPDATED = "movie.similar_movies.updated"
SIMILAR_MOVIES_AUDIT_LIMIT = 5

# entity_type -> model with a unique string `key` column. Register new entity types here.
KEYED_ENTITY_MODELS = {
    MOVIE_ENTITY: m.Movie,
}


def resolve_entity_id(db: Session, entity_type: str, entity_key: str) -> int | None:
    """Map a public entity key to its internal id. Raises KeyError for an unsupported entity type."""
    model = KEYED_ENTITY_MODELS[entity_type]
    return db.scalar(sa.select(model.id).where(model.key == entity_key))


def _diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {key: {"old": old.get(key), "new": value} for key, value in new.items() if old.get(key) != value}


def record_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    event_type: str,
    user: m.User,
    old: dict[str, Any],
    new: dict[str, Any],
    grouped: bool = False,
) -> m.AuditLog | None:
    """Single entry point for audit logging.

    `old` and `new` are flat dicts keyed by whatever identifies a value for the event
    (language code, field name, ...). Only keys from `new` that differ from `old` are stored
    as {key: {"old", "new"}}. Nothing is written when nothing changed.
    With `grouped=True`, `old` and `new` are {group: flat dict} and the diff is computed per group:
    {group: {key: {"old", "new"}}}. Groups without changes are omitted.
    The row is added to the session without committing, so it shares the caller's transaction.

    Example:
        record_audit(
            db,
            entity_type=MOVIE_ENTITY,
            entity_id=movie.id,
            event_type="movie.description.updated",
            user=current_user,
            old={"en": "Old description", "uk": "Старий опис"},
            new={"en": "Old description", "uk": "Оновлений опис"},
        )
        db.commit()  # saves the edit and the audit row atomically

        # stored changes (unchanged "en" is omitted):
        # {"uk": {"old": "Старий опис", "new": "Оновлений опис"}}
    """
    if grouped:
        changes = {group: _diff(old.get(group, {}), values) for group, values in new.items()}
        changes = {group: diff for group, diff in changes.items() if diff}
    else:
        changes = _diff(old, new)
    if not changes:
        return None

    entry = m.AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        user_id=user.id,
        changes=changes,
    )
    db.add(entry)
    return entry


def _en_name(translations, attr: str) -> str:
    return next((getattr(t, attr) for t in translations if t.language == s.Language.EN.value), "")


def snapshot_movie_actors(db: Session, movie_id: int) -> list[dict]:
    """English-only snapshot of a movie's cast, in billing order. Call before and after a change."""
    rows = db.scalars(
        sa.select(m.MovieActorCharacter)
        .where(m.MovieActorCharacter.movie_id == movie_id)
        .order_by(m.MovieActorCharacter.order, m.MovieActorCharacter.id)
    ).all()
    return [
        {
            "key": row.actor.key,
            "name": _en_name(row.actor.translations, "full_name"),
            "avatar": row.actor.avatar,
            "character_key": row.character.key,
            "character_name": _en_name(row.character.translations, "name"),
        }
        for row in rows
    ]


def snapshot_movie_directors(movie: m.Movie) -> list[dict]:
    """English-only snapshot of a movie's directors, sorted by key so order changes don't count as edits."""
    return [
        {"key": d.key, "name": _en_name(d.translations, "full_name"), "avatar": d.avatar}
        for d in sorted(movie.directors, key=lambda d: d.key)
    ]


def snapshot_visual_profile(db: Session, visual_profile: m.VisualProfile) -> dict:
    """English-only snapshot of a user's visual profile: category plus scored criteria in display order.

    Reads through queries (not relationships) so it is accurate after the category/ratings were swapped in the same session.
    """
    category = db.get(m.VisualProfileCategory, visual_profile.category_id)
    ratings = db.scalars(
        sa.select(m.VisualProfileRating)
        .where(m.VisualProfileRating.title_visual_profile_id == visual_profile.id)
        .order_by(m.VisualProfileRating.order, m.VisualProfileRating.id)
    ).all()
    return {
        "category": {"key": category.key, "name": _en_name(category.translations, "name")} if category else None,
        "criteria": [
            {
                "key": r.criterion.key,
                "name": _en_name(r.criterion.translations, "name"),
                "rating": r.rating,
                "order": r.order,
            }
            for r in ratings
        ],
    }


def _localized(translations, attr: str = "name") -> dict[str, str]:
    return {t.language: getattr(t, attr) for t in sorted(translations, key=lambda t: t.language)}


def snapshot_movie_genres(db: Session, movie_id: int) -> dict[str, list[dict]]:
    """Localized snapshot of a movie's genres and subgenres with their percentage_match.

    Genres and subgenres are separate lists; each subgenre also carries its parent genre.
    Both are sorted by key so only real changes show up in the diff.
    """
    genre_rows = db.execute(
        sa.select(m.Genre, m.movie_genres.c.percentage_match)
        .join(m.movie_genres, m.movie_genres.c.genre_id == m.Genre.id)
        .where(m.movie_genres.c.movie_id == movie_id)
        .order_by(m.Genre.key)
    ).all()
    subgenre_rows = db.execute(
        sa.select(m.Subgenre, m.movie_subgenres.c.percentage_match)
        .join(m.movie_subgenres, m.movie_subgenres.c.subgenre_id == m.Subgenre.id)
        .where(m.movie_subgenres.c.movie_id == movie_id)
        .order_by(m.Subgenre.key)
    ).all()

    return {
        "genres": [{"key": g.key, "name": _localized(g.translations), "percentage_match": pm} for g, pm in genre_rows],
        "subgenres": [
            {
                "key": sg.key,
                "name": _localized(sg.translations),
                "percentage_match": pm,
                "genre": {"key": sg.genre.key, "name": _localized(sg.genre.translations)},
            }
            for sg, pm in subgenre_rows
        ],
    }


def snapshot_movie_filter(db: Session, movie_id: int, model, link_table: sa.Table, link_fk: str) -> list[dict]:
    """Localized snapshot of a movie's filter items (specification, keyword, action time, ...).

    `link_fk` is the item-id column in the movie↔item table. Sorted by key to avoid order-only diffs.
    """
    rows = db.execute(
        sa.select(model, link_table.c.percentage_match)
        .join(link_table, link_table.c[link_fk] == model.id)
        .where(link_table.c.movie_id == movie_id)
        .order_by(model.key)
    ).all()
    return [{"key": item.key, "name": _localized(item.translations), "percentage_match": pm} for item, pm in rows]


def snapshot_movie_overall_rating(movie: m.Movie) -> dict[str, Any]:
    """Aggregate rating of a movie: average, votes count and the per-criterion averages that apply to it."""
    criteria = {key: value for key, value in (movie.average_by_criteria or {}).items() if value is not None}
    return {"rating": movie.average_rating, "ratings_count": movie.ratings_count, **criteria}


def snapshot_similar_movies(db: Session, movie_id: int, limit: int = SIMILAR_MOVIES_AUDIT_LIMIT) -> list[dict]:
    """Top `limit` similar movies (same ranking as the public endpoint), with rank, score and localized title."""
    return [
        {
            "rank": rank,
            "key": similar.key,
            "title": _localized(similar.translations, "title"),
            "poster": similar.poster,
            "similarity_score": round(score, 2),
        }
        for rank, (similar, score) in enumerate(get_ranked_similar_movies(db, movie_id, limit), start=1)
    ]


def record_similar_movies_change(db: Session, movie_id: int, user: m.User, old: list[dict]) -> m.AuditLog | None:
    """Log a new top-N similar list, only when the movies or their ranking changed (not on score drift)."""
    new = snapshot_similar_movies(db, movie_id)
    if [e["key"] for e in old] == [e["key"] for e in new]:
        return None
    return record_audit(
        db,
        entity_type=MOVIE_ENTITY,
        entity_id=movie_id,
        event_type=MOVIE_SIMILAR_MOVIES_UPDATED,
        user=user,
        old={"similar_movies": old},
        new={"similar_movies": new},
    )


def encode_cursor(created_at: datetime, log_id: int) -> str:
    return base64.urlsafe_b64encode(f"{created_at.isoformat()}|{log_id}".encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    """Raises ValueError for a malformed cursor."""
    try:
        created_at, log_id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        return datetime.fromisoformat(created_at), int(log_id)
    except Exception as e:
        raise ValueError("Invalid cursor") from e


def get_audit_history(
    db: Session,
    entity_type: str,
    entity_id: int,
    limit: int,
    cursor: str | None = None,
) -> s.AuditLogListOut:
    """Keyset pagination over (created_at DESC, id DESC).

    Newer records sort before the cursor, so inserts never shift or duplicate later pages.
    """
    query = (
        sa.select(m.AuditLog, m.User.first_name, m.User.last_name)
        .outerjoin(m.User, m.User.id == m.AuditLog.user_id)
        .where(m.AuditLog.entity_type == entity_type, m.AuditLog.entity_id == entity_id)
        .order_by(m.AuditLog.created_at.desc(), m.AuditLog.id.desc())
        .limit(limit + 1)
    )

    if cursor:
        cursor_created_at, cursor_id = decode_cursor(cursor)
        query = query.where(
            sa.tuple_(m.AuditLog.created_at, m.AuditLog.id)
            < sa.tuple_(sa.literal(cursor_created_at), sa.literal(cursor_id))
        )

    rows = db.execute(query).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = [
        s.AuditLogOut(
            id=entry.id,
            event_type=entry.event_type,
            user_id=entry.user_id,
            user_name=f"{first_name or ''} {last_name or ''}".strip() or None,
            changes=entry.changes,
            created_at=entry.created_at,
        )
        for entry, first_name, last_name in rows
    ]

    return s.AuditLogListOut(
        items=items,
        next_cursor=encode_cursor(rows[-1][0].created_at, rows[-1][0].id) if has_more else None,
    )
