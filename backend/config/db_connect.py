import logging
from mongoengine import connect, disconnect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self, db_name="ECIRAS", host='mongodb://localhost:27017', alias='default'):
        try:
            connect(db=db_name, host=host, alias=alias )
            logger.info(f"Connected to MongoDB database: {db_name}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise
            
    def disconnect(self):
        try:
            disconnect()
            logger.info("Disconnected from MongoDB")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from MongoDB: {e}")
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
        logger.error(f"Failed to connect to the database: {e}")
    finally:
        db.disconnect()
    


if __name__ == "__main__":
    main()
