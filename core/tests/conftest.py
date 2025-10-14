"""
Pytest Configuration and Fixtures for FastAPI Testing
This file contains all test configurations, database setup, and reusable fixtures
"""
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, get_db
from main import app
from models import UserModel

# Test Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with StaticPool for in-memory database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Session Scope Fixtures
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-scoped fixture to create and drop database tables
    Runs once for the entire test session
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Module Scope Fixtures
@pytest.fixture(scope="module")
def db_session():
    """
    Module-scoped database session
    Shared across all tests in a module
    """
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def override_dependencies(db_session):
    """
    Override FastAPI dependencies with test database
    Automatically applied to all tests in a module
    """
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.pop(get_db, None)


# Function Scope Fixtures
@pytest.fixture(scope="function")
def client():
    """
    Function-scoped test client with automatic cookie handling
    Uses CookieTestClient which automatically saves and sends cookies
    This simulates real browser behavior
    """
    # Return client directly (not in context manager)
    # This allows the same client instance to maintain cookies
    test_client = TestClient(app, base_url="https://testserver")
    return test_client


@pytest.fixture(scope="function")
def test_user(db_session):
    """
    Create a test user in the database
    Useful for authentication tests
    Cleans up after each test to avoid conflicts
    """
    # Delete any existing test user
    db_session.query(UserModel).filter(
        UserModel.user_name == "testuser"
    ).delete()
    db_session.commit()
    
    # Create new test user
    user = UserModel(
        user_name="testuser",
        password="testpass123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    yield user
    
    # Cleanup after test
    db_session.query(UserModel).filter(
        UserModel.id == user.id
    ).delete()
    db_session.commit()


@pytest.fixture(scope="function")
def authenticated_client(client, test_user):
    """
    Authenticated test client with valid cookies
    Returns a client with authentication cookies automatically set
    
    The CookieTestClient automatically saves cookies from the login response
    and sends them in subsequent requests
    """
    # Login to get authentication cookies
    response = client.post(
        "/login",
        json={
            "user_name": test_user.user_name,
            "password": test_user.password
        }
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    
    # Verify cookies are set (they're automatically saved by CookieTestClient)
    assert "access_token" in response.cookies, "Access token not in cookies"
    assert "refresh_token" in response.cookies, "Refresh token not in cookies"
    
    # No need to manually set cookies - CookieTestClient does it automatically!
    # The cookies are now saved and will be sent in all subsequent requests
    
    return client


@pytest.fixture(scope="function")
def test_user_credentials():
    """
    Provides test user credentials
    Useful for signup/login tests
    """
    return {
        "user_name": "newuser",
        "password": "newpass123"
    }


@pytest.fixture(scope="function")
def sample_cost_data():
    """
    Sample cost data for testing
    """
    return {
        "description": "Test expense",
        "amount": 100.50
    }


# Helper Functions
def login_user(client, username: str, password: str):
    
    response = client.post(
        "/login",
        json={"user_name": username, "password": password}
    )


    return response
