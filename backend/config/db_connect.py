import logging
from mongoengine import connect, disconnect

logger = logging.getLogger(__name__)


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self, db_name="ECIRAS", host='mongodb://localhost:27017', alias='default'):
        try:
            connect(
                db=db_name,
                host=host,
                alias=alias,
                maxPoolSize=10,
                minPoolSize=2,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000
            )
            logger.info("Connected to MongoDB database: %s", db_name)
            return True
        except Exception:
            logger.exception("Error connecting to MongoDB")
            raise

    def disconnect(self):
        try:
            disconnect()
            logger.info("Disconnected from MongoDB")
            return True
        except Exception:
            logger.exception("Error disconnecting from MongoDB")
            raise


def main():
    from dotenv import load_dotenv
    import os
    load_dotenv()
    db = Database()
    db_name = os.getenv("MONGO_DB_NAME", "ECIRAS")
    host = os.getenv("MONGO_URI", "mongodb://localhost:27017")

    try:
        db.connect(db_name=db_name, host=host)
    except Exception as e:
        logger.exception("Failed to connect to the database")
    finally:
        db.disconnect()


if __name__ == "__main__":
    main()

