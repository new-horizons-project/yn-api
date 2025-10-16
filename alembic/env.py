from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.db import Base, ALEMBIC_DATABASE_URL

config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def start_migrations():
	with context.begin_transaction():
			context.run_migrations()


def migrate_offline():
	context.configure(
		url=ALEMBIC_DATABASE_URL,
		target_metadata=Base.metadata,
		literal_binds=True
	)

	start_migrations()


def migrate_running():
	connection = create_engine(
		url=ALEMBIC_DATABASE_URL,
		poolclass=pool.NullPool
	)

	with connection.connect() as active_conn:
		context.configure(
			connection=active_conn,
			target_metadata=Base.metadata	
		)

		start_migrations()


if context.is_offline_mode():
    migrate_offline()
else:
    migrate_running()