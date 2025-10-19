from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.db import Base, ALEMBIC_DATABASE_URL

config = context.config
target_metadata = Base.metadata


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline():
    context.configure(
        url=ALEMBIC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        url=ALEMBIC_DATABASE_URL,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
