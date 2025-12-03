from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///scan_plates.db", echo=False)

# Create a base class for our models
Base = declarative_base()

# Create a session factory bound to our engine
SessionLocal = sessionmaker(bind=engine)
