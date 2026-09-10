import pytest
import app.models  # Ensures all ORM models are imported & registered
from app.database.base import Base
from app.database.session import engine
from seed_users import seed_default_users


@pytest.fixture(autouse=True, scope="function")
def setup_test_database():
    """
    Automatically ensure all SQL database tables exist and default users are seeded.
    """
    Base.metadata.create_all(bind=engine)
    seed_default_users()
    yield
