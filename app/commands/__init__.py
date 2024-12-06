import click
import sqlalchemy as sa
from flask import Flask
from sqlalchemy import orm

from app import db, forms
from app import models as m
from app import schema as s


def init(app: Flask):
    # flask cli context setup
    @app.shell_context_processor
    def get_context():
        """Objects exposed here will be automatically available from the shell."""
        return dict(app=app, db=db, m=m, f=forms, s=s, sa=sa, orm=orm)

    if app.config["ENV"] != "production":

        @app.cli.command()
        @click.option("--count", default=100, type=int)
        def db_populate(count: int):
            """Fill DB by dummy data."""
            from test_flask.db import populate

            populate(count)
            print(f"DB populated by {count} instancies")

    @app.cli.command("create-admin")
    def create_admin():
        """Create super admin account"""
        query = m.Admin.select().where(m.Admin.email == app.config["ADMIN_EMAIL"])
        if db.session.execute(query).first():
            print(f"User with e-mail: [{app.config['ADMIN_EMAIL']}] already exists")
            return
        m.Admin(
            username=app.config["ADMIN_USERNAME"],
            email=app.config["ADMIN_EMAIL"],
            password=app.config["ADMIN_PASSWORD"],
        ).save()
        print("admin created")

    if app.config["ENV"] != "production":

        @app.cli.command("create-users")
        def create_users():
            """Create users"""
            from test_flask.utility import create_users

            create_users(db)
            print("users created")

    @app.cli.command()
    def delete_actors_from_db():
        """Fill movies with data from google spreadsheets"""
        from .delete_actors import delete_actors_from_db

        delete_actors_from_db()
        print("done")

    @app.cli.command()
    def fill_db_with_movies():
        """Fill movies with movies data from google spreadsheets"""
        from .export_movies import export_movies_from_google_spreadsheets

        export_movies_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_actors():
        """Fill movies with actors data from google spreadsheets"""
        from .export_actors import export_actors_from_google_spreadsheets

        export_actors_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_directors():
        """Fill movies with directors data from google spreadsheets"""
        from .export_directors import export_directors_from_google_spreadsheets

        export_directors_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_genres():
        """Fill movies with genres data from google spreadsheets"""
        from .export_genres import export_genres_from_google_spreadsheets

        export_genres_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_subgenres():
        """Fill movies with subgenres data from google spreadsheets"""
        from .export_subgenres import export_subgenres_from_google_spreadsheets

        export_subgenres_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def execute_all():
        """Execute all commands that related to movies"""
        from .export_actors import export_actors_from_google_spreadsheets
        from .export_directors import export_directors_from_google_spreadsheets
        from .export_genres import export_genres_from_google_spreadsheets
        from .export_subgenres import export_subgenres_from_google_spreadsheets
        from .export_movies import export_movies_from_google_spreadsheets

        export_actors_from_google_spreadsheets()
        export_directors_from_google_spreadsheets()
        export_genres_from_google_spreadsheets()
        export_subgenres_from_google_spreadsheets()
        export_movies_from_google_spreadsheets()
        print("done")
