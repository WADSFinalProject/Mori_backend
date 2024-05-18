import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the database URL from environment variables
SQLALCHEMY_DATABASE_URL = "postgres://default:3HiADe0lNWPZ@ep-spring-forest-a1pra2zp.ap-southeast-1.aws.neon.tech:5432/verceldb?sslmode=require"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
