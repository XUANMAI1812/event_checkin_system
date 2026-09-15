"""Tao bang trong DB cau hinh o DATABASE_URL. Chay 1 lan:

    python -m scripts.init_db
"""

from app import models  # noqa: F401
from app.database import Base, engine


def main() -> None:
    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)
    print("Da tao xong bang trong database.")


if __name__ == "__main__":
    main()
