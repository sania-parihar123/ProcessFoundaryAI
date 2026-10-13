
from collections.abc import Generator

from sqlalchemy.orm import Session

from processfoundry_ai.database.config import DatabaseConfig
from processfoundry_ai.database.session import get_session


def get_db() -> Generator[Session, None, None]:
    config = DatabaseConfig.from_env()
    db = get_session(config)

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
