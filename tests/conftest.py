import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db, ensure_database_schema
from main import app
from seed_data import seed_initial_data

TEST_DB_FILE = "./test_shopsphere.db"
test_engine = create_engine(
    f"sqlite:///{TEST_DB_FILE}",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

    ensure_database_schema(test_engine)
    session = TestingSessionLocal()
    try:
        seed_initial_data(session)
    finally:
        session.close()

    yield

    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@shopsphere.com",
        "password": "Admin@ShopSphere2026!"
    })
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def employee_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "employee@shopsphere.com",
        "password": "Employee@1234!"
    })
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def customer_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "customer@shopsphere.com",
        "password": "Customer@1234!"
    })
    assert res.status_code == 200, res.text
    return res.json()["access_token"]
