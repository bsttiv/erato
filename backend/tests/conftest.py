"""Real MongoDB, isolated by pytest session and emptied without dropping indexes."""
import os
from uuid import uuid4

import pytest
from pymongo import MongoClient

from app.database import create_indexes


@pytest.fixture(scope="session")
def mongo_database():
    original = os.environ["MONGODB_DB"]
    name = f"erato_test_{uuid4().hex}"
    os.environ["MONGODB_DB"] = name
    client = MongoClient(os.environ["MONGODB_URI"], tz_aware=True,
                         serverSelectionTimeoutMS=5000)
    database = client[name]
    create_indexes(database)
    yield database
    client.drop_database(name)
    client.close()
    os.environ["MONGODB_DB"] = original


@pytest.fixture(autouse=True)
def db(mongo_database):
    for name in mongo_database.list_collection_names():
        mongo_database[name].delete_many({})
    yield mongo_database
