import base64
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from sqlalchemy.orm import Session

import app.models as m
from api.controllers.movie import get_ranked_similar_movies
from api.utils import normalize_query
import app.schema as s
from app.logger import log

MOVIE_ENTITY = "movie"
MOVIE_VISITED = "movie.visited"
MOVIE_VISIT_COOLDOWN = timedelta(hours=24)
MOVIE_CREATED = "movie.created"
MOVIE_DESCRIPTION_UPDATED = "movie.description.updated"
MOVIE_TITLE_UPDATED = "movie.title.updated"
MOVIE_DETAILS_UPDATED = "movie.details.updated"
MOVIE_BOX_OFFICE_UPDATED = "movie.box_office.updated"
MOVIE_POSTER_UPDATED = "movie.poster.updated"
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
MOVIE_COLLECTION_UPDATED = "movie.collection.updated"
SIMILAR_MOVIES_AUDIT_LIMIT = 5

# To add or change events, edit this registry: each category is a mutually exclusive filter.
EVENT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "content": (
        MOVIE_CREATED,
        MOVIE_RATING_CREATED,
        MOVIE_DESCRIPTION_UPDATED,
        MOVIE_RATING_UPDATED,
        MOVIE_TITLE_UPDATED,
        MOVIE_DETAILS_UPDATED,
        MOVIE_BOX_OFFICE_UPDATED,
        MOVIE_POSTER_UPDATED,
        MOVIE_ACTORS_UPDATED,
        MOVIE_DIRECTORS_UPDATED,
        MOVIE_VISUAL_PROFILE_UPDATED,
        MOVIE_GENRES_UPDATED,
        MOVIE_SPECIFICATIONS_UPDATED,
        MOVIE_KEYWORDS_UPDATED,
        MOVIE_ACTION_TIMES_UPDATED,
        MOVIE_COLLECTION_UPDATED,
        MOVIE_VISITED,
    ),
    "similar_movies": (MOVIE_SIMILAR_MOVIES_UPDATED,),
}

DEFAULT_EVENT_CATEGORY = "content"

# entity_type -> model with a unique string `key` column. Register new entity types here.
KEYED_ENTITY_MODELS: dict[str, type[m.Movie]] = {MOVIE_ENTITY: m.Movie}


def resolve_entity_id(db: Session, entity_type: str, entity_key: str) -> int | None:
    """Map a public entity key to its internal id. Raises KeyError for an unsupported entity type."""
    model = KEYED_ENTITY_MODELS[entity_type]
    return db.scalar(sa.select(model.id).where(model.key == entity_key))


def log_movie_visit(movie_id: int, user_id: int | None) -> None:
    """Background task: record a movie page visit, at most once per 24h per (movie, user).

    Uses its own session because the request-scoped one is closed once the response is sent.
    Never raises, so a logging failure cannot affect the response.
    """
    from app.database import db

    try:
        with db.Session() as session:
            now = datetime.now(UTC).replace(tzinfo=None)
            recent = session.scalar(
                sa.select(m.AuditLog.id)
                .where(
                    m.AuditLog.entity_type == MOVIE_ENTITY,
                    m.AuditLog.entity_id == movie_id,
                    m.AuditLog.event_type == MOVIE_VISITED,
                    m.AuditLog.user_id.is_(None) if user_id is None else m.AuditLog.user_id == user_id,
                    m.AuditLog.created_at >= now - MOVIE_VISIT_COOLDOWN,
                )
                .limit(1)
            )
            if recent:
                return

            session.add(
                m.AuditLog(
                    entity_type=MOVIE_ENTITY,
                    entity_id=movie_id,
                    event_type=MOVIE_VISITED,
                    user_id=user_id,
                    changes={"visited_at": now.isoformat()},
                )
            )
            session.commit()
    except Exception as e:
        log(log.ERROR, "Failed to log movie [%s] visit: %s", movie_id, e)


def _trim_list(old: Any, new: Any) -> tuple[Any, Any]:
    """For lists, drop items present unchanged on both sides so only added/removed/modified items remain.
    A pure reorder keeps the full lists, since the order itself is the change."""
    if not isinstance(old, list) or not isinstance(new, list):
        return old, new
    trimmed_old = [item for item in old if item not in new]
    trimmed_new = [item for item in new if item not in old]
    if not trimmed_old and not trimmed_new:
        return old, new
    return trimmed_old, trimmed_new


def _diff(
    old: dict[str, Any], new: dict[str, Any], allow_same: bool = False, trim_lists: bool = True
) -> dict[str, dict[str, Any]]:
    result = {}
    for key, value in new.items():
        old_value = old.get(key)
        if old_value == value and not allow_same:
            continue
        if trim_lists and old_value != value:
            old_value, value = _trim_list(old_value, value)
        result[key] = {"old": old_value, "new": value}
    return result


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
    context: dict[str, Any] | None = None,
    # If allow_same is True, an audit entry will be created even if there are no changes.
    allow_same: bool = False,
    # If trim_lists is False, list values are stored in full (e.g. radar chart data that needs every point).
    trim_lists: bool = True,
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
        changes = {
            group: _diff(old.get(group, {}), values, allow_same=allow_same, trim_lists=trim_lists)
            for group, values in new.items()
        }
        changes = {group: diff for group, diff in changes.items() if diff}
    else:
        changes = _diff(old, new, allow_same=allow_same, trim_lists=trim_lists)
    if not changes:
        return None
    # Context is stored as a plain value (no old/new) next to the real changes
    changes = {**changes, **(context or {})}

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
    """Localized snapshot of a user's visual profile: category plus scored criteria in display order.

    Reads through queries (not relationships) so it is accurate after the category/ratings were swapped in the same session.
    """
    category = db.get(m.VisualProfileCategory, visual_profile.category_id)
    ratings = db.scalars(
        sa.select(m.VisualProfileRating)
        .where(m.VisualProfileRating.title_visual_profile_id == visual_profile.id)
        .order_by(m.VisualProfileRating.order, m.VisualProfileRating.id)
    ).all()
    return {
        "category": {"key": category.key, "name": _localized(category.translations)} if category else None,
        "criteria": [
            {
                "key": r.criterion.key,
                "name": _localized(r.criterion.translations),
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


def snapshot_movie_collection(db: Session, base_movie_id: int) -> list[dict]:
    """Localized snapshot of a collection (base included) in collection order.

    Queries instead of relationships so it is accurate right after the collection was edited in the same session.
    A movie that is not (or no longer) a collection base yields an empty list.
    """
    movies = db.scalars(
        sa.select(m.Movie)
        .where(
            sa.or_(m.Movie.id == base_movie_id, m.Movie.collection_base_movie_id == base_movie_id),
            m.Movie.relation_type.is_not(None),
        )
        .order_by(sa.nulls_last(m.Movie.collection_order), m.Movie.id)
    ).all()
    return [
        {
            "key": movie.key,
            "title": _localized(movie.translations, "title"),
            "poster": movie.poster,
            "relation_type": movie.relation_type,
            "order": movie.collection_order,
        }
        for movie in movies
    ]


def encode_cursor(created_at: datetime, log_id: int) -> str:
    return base64.urlsafe_b64encode(f"{created_at.isoformat()}|{log_id}".encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    """Raises ValueError for a malformed cursor."""
    try:
        created_at, log_id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        return datetime.fromisoformat(created_at), int(log_id)
    except Exception as e:
        raise ValueError("Invalid cursor") from e


def _summary_query(lang: s.Language) -> tuple[Any, sa.Select]:
    movie = sa.orm.aliased(m.Movie)
    translation = sa.orm.aliased(m.MovieTranslation)
    query = (
        sa.select(
            m.AuditLog.id,
            m.AuditLog.event_type,
            m.AuditLog.entity_type,
            m.AuditLog.created_at,
            m.AuditLog.user_id,
            m.User.first_name,
            m.User.last_name,
            m.User.role,
            movie.key.label("entity_key"),
            movie.poster.label("entity_poster"),
            translation.title.label("entity_title"),
        )
        .outerjoin(m.User, m.User.id == m.AuditLog.user_id)
        .outerjoin(movie, sa.and_(m.AuditLog.entity_type == MOVIE_ENTITY, m.AuditLog.entity_id == movie.id))
        .outerjoin(translation, sa.and_(translation.movie_id == movie.id, translation.language == lang.value))
    )

    return movie, query


def _summary_item(row: Any) -> s.AuditLogSummaryOut:
    return s.AuditLogSummaryOut(
        id=row.id,
        event_type=row.event_type,
        entity_type=row.entity_type,
        entity_key=row.entity_key,
        entity_title=row.entity_title,
        entity_poster=row.entity_poster,
        user_id=row.user_id,
        user_name=f"{row.first_name or ''} {row.last_name or ''}".strip() or None,
        user_role=row.role,
        created_at=row.created_at,
    )


def get_latest_audit_event(db: Session, lang: s.Language) -> s.AuditLogSummaryOut | None:
    """Most recent non-similar-movies event, independent of all other filters."""
    _, query = _summary_query(lang)
    row = db.execute(
        query.where(m.AuditLog.event_type != MOVIE_SIMILAR_MOVIES_UPDATED)
        .order_by(m.AuditLog.created_at.desc(), m.AuditLog.id.desc())
        .limit(1)
    ).first()
    return _summary_item(row) if row else None


def get_general_audit_history(
    db: Session,
    limit: int,
    cursor: str | None = None,
    category: str = DEFAULT_EVENT_CATEGORY,
    *,
    event_types: list[str] | None = None,
    exclude_event_types: list[str] | None = None,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_key: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    tz: ZoneInfo | None = None,
    search: str | None = None,
    sort: str = "desc",
    lang: s.Language = s.Language.EN,
) -> s.AuditLogSummaryListOut:
    """Keyset-paginated history of all entities without change details.

    Items are grouped by day in `tz` (UTC by default); a day may continue on the next page.
    Exactly one event category is shown at a time (default "content"); the other filters
    (user, entity, date, search) are combined with it using AND.
    `event_types` narrows the category to a subset of its events (OR between them).
    `exclude_event_types` removes matching events from the selected category.
    Raises ValueError for a malformed cursor, KeyError for an unsupported entity type or category.
    """
    included = EVENT_CATEGORIES[category]
    if event_types:
        included = tuple(e for e in included if e in event_types)
    if exclude_event_types:
        included = tuple(e for e in included if e not in exclude_event_types)

    movie, query = _summary_query(lang)

    query = query.where(m.AuditLog.event_type.in_(included))
    if user_id is not None:
        query = query.where(m.AuditLog.user_id == user_id)
    if entity_type:
        if entity_type not in KEYED_ENTITY_MODELS:
            raise KeyError(entity_type)
        query = query.where(m.AuditLog.entity_type == entity_type)
    if entity_key:
        query = query.where(movie.key == entity_key)
    # created_at is stored as naive UTC; convert the client's local day bounds to UTC
    tz = tz or ZoneInfo("UTC")

    def _local_midnight_utc(day: date) -> datetime:
        return datetime.combine(day, time.min, tzinfo=tz).astimezone(UTC).replace(tzinfo=None)

    if date_from:
        query = query.where(m.AuditLog.created_at >= _local_midnight_utc(date_from))
    if date_to:
        query = query.where(m.AuditLog.created_at < _local_midnight_utc(date_to + timedelta(days=1)))
    if search:
        normalized_search = normalize_query(search)
        any_title = sa.exists().where(
            m.MovieTranslation.movie_id == movie.id,
            sa.func.regexp_replace(sa.func.lower(m.MovieTranslation.title), r"[^a-zA-Zа-яА-Я0-9 ]", "", "g").ilike(
                f"%{normalized_search}%"
            ),
        )
        query = query.where(any_title)

    ascending = sort == "asc"
    order = (
        (m.AuditLog.created_at.asc(), m.AuditLog.id.asc())
        if ascending
        else (m.AuditLog.created_at.desc(), m.AuditLog.id.desc())
    )
    query = query.order_by(*order).limit(limit + 1)

    if cursor:
        cursor_created_at, cursor_id = decode_cursor(cursor)
        position = sa.tuple_(m.AuditLog.created_at, m.AuditLog.id)
        cursor_position = sa.tuple_(sa.literal(cursor_created_at), sa.literal(cursor_id))
        query = query.where(position > cursor_position if ascending else position < cursor_position)

    rows = db.execute(query).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    groups: list[s.AuditLogDayGroupOut] = []
    for row in rows:
        item = _summary_item(row)
        day = row.created_at.replace(tzinfo=UTC).astimezone(tz).date()
        if not groups or groups[-1].date != day:
            groups.append(s.AuditLogDayGroupOut(date=day, items=[]))
        groups[-1].items.append(item)

    return s.AuditLogSummaryListOut(
        latest_event=get_latest_audit_event(db, lang),
        groups=groups,
        next_cursor=encode_cursor(rows[-1].created_at, rows[-1].id) if has_more else None,
    )


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
        sa.select(m.AuditLog, m.User.first_name, m.User.last_name, m.User.role)
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
            user_role=role,
            changes=entry.changes,
            created_at=entry.created_at,
        )
        for entry, first_name, last_name, role in rows
    ]

    return s.AuditLogListOut(
        items=items,
        next_cursor=encode_cursor(rows[-1][0].created_at, rows[-1][0].id) if has_more else None,
    )


def get_audit_users(db: Session) -> s.AuditLogUserListOut:
    """Users that authored at least one audit event, for the history user filter."""
    rows = db.execute(
        sa.select(m.User.id, m.User.first_name, m.User.last_name, m.User.role)
        .where(m.User.id.in_(sa.select(m.AuditLog.user_id).distinct()))
        .order_by(m.User.first_name, m.User.last_name, m.User.id)
    ).all()
    return s.AuditLogUserListOut(
        users=[
            s.AuditLogUserOut(
                id=row.id,
                full_name=f"{row.first_name or ''} {row.last_name or ''}".strip(),
                role=row.role,
            )
            for row in rows
        ]
    )
