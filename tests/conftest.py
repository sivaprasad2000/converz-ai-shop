import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """Create the Flask app wired to an in-memory SQLite DB for the entire test session."""
    _app = create_app("testing")

    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()


@pytest.fixture(scope="session")
def db(app):
    """Expose the SQLAlchemy db instance (tables already created by the app fixture)."""
    return _db


@pytest.fixture()
def db_session(db):
    """
    Each test gets a clean transaction that is rolled back on teardown,
    so tests stay isolated without re-creating tables.
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    # Bind the session to this connection so changes stay inside the transaction
    db.session.bind = connection

    yield db.session

    db.session.remove()
    transaction.rollback()
    connection.close()
