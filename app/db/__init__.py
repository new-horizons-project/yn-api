from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .schema import Base
from ..config import settings

engine = create_engine(
	settings.DATABASE_URL, 
	connect_args={ "check_same_thread" : False }
)

session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
	Base.metadata.create_all(bind=engine)


def get_db():
	db = session_local()
	try:
		yield db
	finally:
		db.close()