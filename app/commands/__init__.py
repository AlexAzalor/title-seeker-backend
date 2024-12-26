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
    def fill_db_with_users():
        """Fill users with subgenres data from google spreadsheets"""
        from .export_users import export_users_from_google_spreadsheets

        export_users_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_ratings():
        """Fill ratings with subgenres data from google spreadsheets"""
        from .export_rating import export_ratings_from_google_spreadsheets

        export_ratings_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_characters():
        """Fill characters with subgenres data from google spreadsheets"""
        from .export_characters import export_characters_from_google_spreadsheets

        export_characters_from_google_spreadsheets()

    @app.cli.command()
    def fill_db_with_specifications():
        """Fill specifications table with data from google spreadsheets"""
        from .export_specifications import export_specifications_from_google_spreadsheets

        export_specifications_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_keywords():
        """Fill keywords table with data from google spreadsheets"""
        from .export_keywords import export_keywords_from_google_spreadsheets

        export_keywords_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def fill_db_with_action_times():
        """Fill ActionTime table with data from google spreadsheets"""
        from .export_action_times import export_action_times_from_google_spreadsheets

        export_action_times_from_google_spreadsheets()
        print("done")

    @app.cli.command()
    def import_movies():
        """Append data to google spreadsheets"""
        from .imports_from_google_sheet.import_movies import append_data_to_google_spreadsheets

        append_data_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def import_actors():
        """Append data to google spreadsheets"""
        from .imports_from_google_sheet.import_actors import import_actors_to_google_spreadsheets

        import_actors_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def import_ratings():
        """Append data to google spreadsheets"""
        from .imports_from_google_sheet.import_ratings import import_ratings_to_google_spreadsheets

        import_ratings_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def import_directors():
        """Append data to google spreadsheets"""
        from .imports_from_google_sheet.import_directors import import_directors_to_google_spreadsheets

        import_directors_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def import_genres():
        """Append data to google spreadsheets"""
        from .imports_from_google_sheet.import_genres import import_genres_to_google_spreadsheets

        import_genres_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def import_subgenres():
        """Append data to google spreadsheets"""
        from .imports_from_google_sheet.import_subgenres import import_subgenres_to_google_spreadsheets

        import_subgenres_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def import_specifications():
        """Append data to google spreadsheets"""
        from .imports_from_google_sheet.import_specifications import import_specifications_to_google_spreadsheets

        import_specifications_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def import_keywords():
        """Append data to google spreadsheets"""
        from .imports_from_google_sheet.import_keywords import import_keywords_to_google_spreadsheets

        import_keywords_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def import_action_times():
        """Append data to google spreadsheets"""
        from .imports_from_google_sheet.import_action_times import import_action_times_to_google_spreadsheets

        import_action_times_to_google_spreadsheets()
        print("done")

    @app.cli.command()
    def execute_all():
        """Execute all commands that related to movies"""
        from .export_users import export_users_from_google_spreadsheets
        from .export_actors import export_actors_from_google_spreadsheets
        from .export_directors import export_directors_from_google_spreadsheets
        from .export_genres import export_genres_from_google_spreadsheets
        from .export_subgenres import export_subgenres_from_google_spreadsheets
        from .export_specifications import export_specifications_from_google_spreadsheets
        from .export_keywords import export_keywords_from_google_spreadsheets
        from .export_action_times import export_action_times_from_google_spreadsheets
        from .export_movies import export_movies_from_google_spreadsheets
        from .export_rating import export_ratings_from_google_spreadsheets
        from .export_characters import export_characters_from_google_spreadsheets

        export_users_from_google_spreadsheets()
        export_actors_from_google_spreadsheets()
        export_directors_from_google_spreadsheets()
        export_genres_from_google_spreadsheets()
        export_subgenres_from_google_spreadsheets()
        export_specifications_from_google_spreadsheets()
        export_keywords_from_google_spreadsheets()
        export_action_times_from_google_spreadsheets()
        export_movies_from_google_spreadsheets()
        export_ratings_from_google_spreadsheets()
        export_characters_from_google_spreadsheets()
        print("===============================================================")
        print("DATABASE SUCCESSFULLY FILLED WITH DATA FROM GOOGLE SPREADSHEETS")
        print("===============================================================")
