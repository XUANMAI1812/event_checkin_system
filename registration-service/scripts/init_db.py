from app.database import Base, engine
from app import models


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Da tao xong bang trong database.")


if __name__ == "__main__":
    main()
