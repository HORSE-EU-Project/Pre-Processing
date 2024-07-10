# http://flask.pocoo.org/docs/1.0/tutorial/database/
import sqlite3
import click
import os
from dotenv import load_dotenv
from flask import current_app, g, current_app
from flask.cli import with_appcontext

# Load environment variables from .env file
load_dotenv()

def get_db(path=None):
    if "db" not in g:
        if path is None:
            path = os.getenv('DB_PATH', './')
        g.db = sqlite3.connect(
            path, detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    
    return g.db

def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        
        db.executescript(f.read().decode("utf8"))

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    print("Initialized the database.")

def init_app(app):
    print("hello")
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    



def update_db_schema():
    """Update the database schema to match the schema.sql file."""
    db = get_db()
    current_schema = fetch_current_schema(db)
    desired_schema = parse_schema_file()

    # Implement schema changes
    apply_schema_changes(db, current_schema, desired_schema)

def fetch_current_schema(db):
    """Fetch the current database schema."""
    query = "SELECT name, sql FROM sqlite_master WHERE type='table';"
    result = db.execute(query).fetchall()
    return {row['name']: row['sql'] for row in result}

def parse_schema_file():
    """Parse the schema from the schema.sql file."""
    with current_app.open_resource('schema.sql') as f:
        schema_sql = f.read().decode('utf8')
    commands = schema_sql.split(';')
    schema = {}
    for command in commands:
        if 'CREATE TABLE' in command:
            tablename = command.split()[2]
            schema[tablename] = command + ';'
    return schema

def apply_schema_changes(db, current_schema, desired_schema):
    """Apply changes from the desired schema to the current database schema."""
    for tablename, sql in desired_schema.items():
        if tablename not in current_schema:
            db.execute(sql)  # Create missing table
        elif current_schema[tablename] != sql:
            db.execute('DROP TABLE IF EXISTS ' + tablename)  # Dangerous: data loss
            db.execute(sql)  # Recreate table with new schema

@click.command('update-db-schema')
@with_appcontext
def update_db_schema_command():
    """Update the database schema to match the schema.sql."""
    update_db_schema()
    print("Database schema updated.")

def init_app(app):
    """Add teardown and command registrations to the Flask app."""
    print("hello")
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(update_db_schema_command)
    
#drop teble based on name
def drop_table(table_name):
    db = get_db()
    db.execute('DROP TABLE IF EXISTS ' + table_name)
    print("Table dropped")
    