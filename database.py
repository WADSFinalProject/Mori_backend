import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Correct database URL with 'postgresql' dialect
# SQLALCHEMY_DATABASE_URL = "g://default:3HiADe0lNWPZ@ep-spring-forest-a1pra2zp.ap-southeast-1.aws.neon.tech:5432/verceldb?sslmode=require"
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models
Base = declarative_base()
