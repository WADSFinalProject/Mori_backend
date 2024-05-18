import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Correct database URL with 'postgresql' dialect
SQLALCHEMY_DATABASE_URL = "postgresql://default:3HiADe0lNWPZ@ep-spring-forest-a1pra2zp.ap-southeast-1.aws.neon.tech:5432/verceldb?sslmode=require"

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models
Base = declarative_base()
