"""Shared pytest fixtures for the Health Checker Pro test suite."""

import os
import tempfile

import pytest


@pytest.fixture(scope="session")
def app():
    """Create a Flask application configured for testing.

    Uses a temporary SQLite database that is cleaned up after the
    entire test session finishes.
    """
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(tmp_fd)

    os.environ["DATABASE_PATH"] = tmp_path
    os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key-do-not-use-in-prod")

    from app import create_app

    application = create_app()
    application.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,  # Disable rate limiting in tests
        }
    )

    yield application

    # Cleanup temp database
    try:
        os.unlink(tmp_path)
    except OSError:
        pass


@pytest.fixture()
def client(app):
    """A Flask test client — simulates HTTP requests without running the server."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """A Flask CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture()
def authenticated_client(client):
    """A test client that is already logged in with a test account.

    Creates the user if it doesn't exist, then logs in.
    """
    # Register a test user
    client.post(
        "/signup",
        data={
            "email": "test@example.com",
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
        },
        follow_redirects=True,
    )

    # Log in
    client.post(
        "/login",
        data={
            "email": "test@example.com",
            "password": "TestPass123!",
        },
        follow_redirects=True,
    )

    return client
