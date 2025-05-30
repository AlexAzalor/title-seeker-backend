import sqlalchemy as sa

from app.database import db

category_criteria = sa.Table(
    "category_criteria",
    db.Model.metadata,
    sa.Column("category_id", sa.ForeignKey("visual_profile_categories.id"), primary_key=True),
    sa.Column("criterion_id", sa.ForeignKey("visual_profile_category_criteria.id"), primary_key=True),
)
