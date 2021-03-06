from unittest import result
import psycopg2
import sys
import click
from flask import current_app, g
from flask.cli import with_appcontext            

""" SETUP FUNCTIONS """

# Set functions for app context
def init_app(app):
    app.teardown_appcontext(close_db)           # close on teardown
    app.cli.add_command(init_db)                # add init_db to click

# Initialize the database on click
@click.command('init-db')
@with_appcontext
def init_db():
    global db
    if not db:
        db = get_db()

    with current_app.open_resource('schema.sql') as f:
        with db.cursor() as cursor:
            try:
                cursor.execute(f.read().decode('utf8'))
                db.commit()
                cursor.close()
                click.echo('Initialized the database.')
            except Exception as err:
                print_exception(err)
                db.rollback()
                cursor.close()

# Add database to global variable
def get_db():
    # global db
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(current_app.config['DATABASE_URL'])
        except psycopg2.DatabaseError as e:
            print(e, file=sys.stderr)
            raise e
    return g.db

# Close database connection
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

""" ERROR HANDLER """

# Print psycopg2 errors
def print_exception(err):
    '''
    err_type, err_obj, traceback = sys.exc_info()
    line_num = traceback.tbl_lineno
    print(f"\npsycopg2.DatabaseError: {err} on line {line_num}")
    print(f"psycopg2.Traceback: {traceback} -- type: {err_type}")
    print(f"psycopg2.Diagnostics: {err.diag}")
    print(f"psycopg2.pgerror: {err.pgerror}")
    print(f"psycopg2.pgcode: {err.pgcode}\n")
    '''
    print(f"psycopg2.DatabaseError")

""" SESSION FUNCTIONS """

# Add session
def add_session(user_id, session_key) -> bool:
    db = get_db()
    query = "INSERT INTO session (user_id, session_key) VALUES (%s, %s)"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (user_id, session_key))
            db.commit()
            cursor.close()
            return True
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False

def get_session(user_id):
    db = get_db()
    query = "SELECT session_key FROM session WHERE user_id = %s LIMIT 1"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (user_id,))
            session_key = cursor.fetchone()
            cursor.close()
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False
    return session_key

def remove_session(user_id) -> bool:
    db = get_db()
    query = "DELETE FROM session WHERE user_id = %s"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (user_id,))
            db.commit()
            cursor.close()
            return True
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False

def get_user_from_session(session_key):
    db = get_db()
    query = "SELECT user_id FROM session WHERE session_key = %s LIMIT 1"
    with db.cursor() as cursor:
        try:
            # cursor.execute(query, (session_key))
            cursor.execute(query, (session_key,))
            user_id = cursor.fetchone()
            cursor.close()
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False
    return user_id

""" USERS FUNCTIONS """

# Add user
def add_user(user_id, username):
    db = get_db()
    query = "INSERT INTO users (id, username) VALUES (%s, %s)"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (user_id, username))
            db.commit()
            cursor.close()
            return True
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False

# Get user information
def get_user(user_id):
    db = get_db()
    # Get user information
    query = "SELECT id, username, \
        TO_CHAR(last_accessed, 'MM-DD-YYYY HH:MI AM') AS last_accessed \
            FROM users WHERE id = %s LIMIT 1"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            cursor.close()
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False
    # Update last_accessed timestamp
    query = "UPDATE users SET last_accessed = NOW() WHERE id = %s"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (user_id,))
            db.commit()
            cursor.close()
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False
    return user

# Get all users
def get_all_users():
    db = get_db()
    query = "SELECT * FROM users"
    with db.cursor() as cursor:
        try:
            cursor.execute(query)
            users = cursor.fetchall()
            cursor.close()
        except Exception as err:
            print_exception(err)
            cursor.close()
            return False
    return users

# Get count of users
def get_users_count():
    db = get_db()
    query = "SELECT COUNT(*) FROM users"
    with db.cursor() as cursor:
        try:
            cursor.execute(query)
            count = cursor.fetchone()
            cursor.close()
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False
    return count

# Get most recent users
def get_most_recent_users(limit = 10):
    db = get_db()
    query = "SELECT id, username, \
        TO_CHAR(last_accessed, 'MM-DD-YYYY HH:MI AM') AS last_accessed \
            FROM users ORDER BY last_accessed DESC LIMIT %s"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (limit,))
            users = cursor.fetchall()
            cursor.close()
        except Exception as err:
            print_exception(err)
            cursor.close()
            return False
    return users

# Get users by top total search history
def get_users_by_total_search_history(limit = 10):
    db = get_db()
    query = "SELECT users.username, COUNT(*) \
        FROM users LEFT JOIN search_history \
            ON users.id = search_history.user_id \
                GROUP BY users.id ORDER BY count(*) DESC LIMIT %s" 
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (limit,))
            users = cursor.fetchall()
            cursor.close()
        except Exception as err:
            print_exception(err)
            cursor.close()
            return False
    return users

""" PRIVILEGES FUNCTIONS """

# Set user privileges
def set_user_privileges(user_id, level):
    db = get_db()
    query = "UPDATE privileges (level) VALUES (%s) WHERE user_id = %s"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (level, user_id))
            db.commit()
            cursor.close()
            return True
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False

# Get user privileges
def get_user_privileges(user_id):
    db = get_db()
    query = "SELECT level FROM privileges WHERE user_id = %s LIMIT 1"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (user_id,))
            privileges = cursor.fetchone()
            cursor.close()
        except Exception as err:
            print_exception(err)
            cursor.close()
            return False
    return privileges

""" SEARCH_HISTORY FUNCTIONS """

# Get search history by user
def get_user_search_history(user_id):
    db = get_db()
    query = "select username, search, \
        TO_CHAR(timestamp, 'MM-DD-YYYY HH:MI AM') AS timestamp \
            FROM search_history LEFT JOIN users \
                ON search_history.user_id = users.id where user_id= %s"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (user_id,))
            search_history = cursor.fetchall()
            cursor.close()
        except Exception as err:
            print_exception(err)
            cursor.close()
            return False
    return search_history

# Add user search history
def add_user_search_history(user_id, search_term):
    db = get_db()
    query = "INSERT INTO search_history (user_id, search) VALUES (%s, %s)"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (user_id, search_term))
            db.commit()
            cursor.close()
            return True
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False

# Get all search history
def get_all_search_history():
    db = get_db()
    query = "SELECT username, search, \
        TO_CHAR(timestamp, 'MM-DD-YYYY HH:MI AM') AS timestamp \
            FROM search_history LEFT JOIN users \
                ON search_history.user_id = users.id"
    with db.cursor() as cursor:
        try:
            cursor.execute(query)
            search_history = cursor.fetchall()
            cursor.close()
        except Exception as err:
            print_exception(err)
            cursor.close()
            return False
    return search_history

# Get count of search history
def get_search_history_count():
    db = get_db()
    query = "SELECT COUNT(*) FROM search_history"
    with db.cursor() as cursor:
        try:
            cursor.execute(query)
            count = cursor.fetchone()
            cursor.close()
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False
    return count

# Get search history, sorted by most recent
def get_most_recent_search_history(limit = 10):
    db = get_db()
    query = "select username, search, \
        TO_CHAR(timestamp, 'MM-DD-YYYY HH:MI AM') AS timestamp \
            FROM search_history LEFT JOIN users \
                ON search_history.user_id = users.id LIMIT %s"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (limit,))
            search_history = cursor.fetchall()
            cursor.close()
        except Exception as err:
            print_exception(err)
            cursor.close()
            return False
    return search_history

""" INTERESTS FUNCTIONS """

# Get all unique interests
def get_all_interests():
    db = get_db()
    query = "SELECT DISTINCT interest, description FROM interests"
    with db.cursor() as cursor:
        try:
            cursor.execute(query)
            interests = cursor.fetchall()
            cursor.close()
        except Exception as err:
            print_exception(err)
            cursor.close()
            return False
    return interests

# Add interest
def add_interest(interest, description = None):
    db = get_db()
    if description is None:
        query = "INSERT INTO interests (interest) VALUES (%s)"
    else:
        query = "INSERT INTO interests (interest, description) VALUES (%s, %s)"
    with db.cursor() as cursor:
        try:
            cursor.execute(query, (interest, description))
            db.commit()
            cursor.close()
            return True
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False

# Add user interests
def add_user_interests(user_id, interests):
    db = get_db()
    interest_query = "SELECT id FROM interests WHERE interest = %s LIMIT 1"
    query = "INSERT INTO user_interests (user_id, interest) VALUES (%s, %s)"
    interests_ids = []
    with db.cursor() as cursor:
        try:
            for interest in interests:
                cursor.execute(interest_query, (interest,))
                interest_id = cursor.fetchall()
                cursor.execute(query, (user_id, interest_id))
            db.commit()
            cursor.close()
            return True
        except Exception as err:
            print_exception(err)
            db.rollback()
            cursor.close()
            return False