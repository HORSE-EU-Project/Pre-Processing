import sqlite3
import click
import os
import logging
from dotenv import load_dotenv
from flask import current_app, g
from flask.cli import with_appcontext

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_db(path=None):
    if "db" not in g:
        if path is None:
            path = os.getenv('DB_PATH', './')
        try:
            g.db = sqlite3.connect(
                path, detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
            logger.info(f"Connected to database at {path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    return g.db

def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()
        logger.info("Database connection closed")

def init_db():
    try:
        db = get_db()
        with current_app.open_resource("schema.sql") as f:
            db.executescript(f.read().decode("utf8"))
        logger.info("Database initialized with schema.sql")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize the database: {e}")
        raise

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    logger.info("Initialized the database with init-db command")

def update_db_schema():
    """Update the database schema to match the schema.sql file."""
    try:
        db = get_db()
        current_schema = fetch_current_schema(db)
        desired_schema = parse_schema_file()

        # Implement schema changes
        apply_schema_changes(db, current_schema, desired_schema)
        logger.info("Database schema updated")
    except sqlite3.Error as e:
        logger.error(f"Failed to update the database schema: {e}")
        raise

def fetch_current_schema(db):
    """Fetch the current database schema."""
    try:
        query = "SELECT name, sql FROM sqlite_master WHERE type='table';"
        result = db.execute(query).fetchall()
        logger.debug(f"Current schema fetched: {result}")
        return {row['name']: row['sql'] for row in result}
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch current schema: {e}")
        raise

def parse_schema_file():
    """Parse the schema from the schema.sql file."""
    try:
        with current_app.open_resource('schema.sql') as f:
            schema_sql = f.read().decode('utf8')
        commands = schema_sql.split(';')
        schema = {}
        for command in commands:
            if 'CREATE TABLE' in command:
                tablename = command.split()[2]
                schema[tablename] = command + ';'
        logger.debug(f"Desired schema parsed: {schema}")
        return schema
    except Exception as e:
        logger.error(f"Failed to parse schema file: {e}")
        raise

def apply_schema_changes(db, current_schema, desired_schema):
    """Apply changes from the desired schema to the current database schema."""
    try:
        for tablename, sql in desired_schema.items():
            if tablename not in current_schema:
                db.execute(sql)  # Create missing table
                logger.info(f"Table {tablename} created")
            elif current_schema[tablename] != sql:
                db.execute(f'DROP TABLE IF EXISTS {tablename}')  # Dangerous: data loss
                db.execute(sql)  # Recreate table with new schema
                logger.info(f"Table {tablename} updated")
    except sqlite3.Error as e:
        logger.error(f"Failed to apply schema changes: {e}")
        raise

@click.command('update-db-schema')
@with_appcontext
def update_db_schema_command():
    """Update the database schema to match the schema.sql."""
    update_db_schema()
    logger.info("Database schema updated with update-db-schema command")

def init_app(app):
    """Add teardown and command registrations to the Flask app."""
    logger.info("Initializing app with database commands")
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(update_db_schema_command)

# Drop table based on name
def drop_table(table_name):
    db = get_db()
   
