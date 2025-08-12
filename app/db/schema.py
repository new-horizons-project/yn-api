from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import (
	String, Text, Enum as SqlEnum, ForeignKey, Boolean, DateTime
)
from sqlalchemy.orm import (
	Mapped, mapped_column, relationship, DeclarativeBase
)

from .enums import *

class Base(DeclarativeBase):
	pass


class User(Base):
	__tablename__ = "users"

	id                       : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	username                 : Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
	password_hash            : Mapped[str] = mapped_column(String(255), nullable=False)
	registration_date        : Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
	role                     : Mapped[str] = mapped_column(SqlEnum(UserRoles, native_enum=False), default=UserRoles.user)
	is_disabled              : Mapped[bool] = mapped_column(Boolean, default=False)
	force_password_change    : Mapped[bool] = mapped_column(Boolean, default=False)

	topic: Mapped[list[Topic]] = relationship(back_populates="creator", cascade="all, delete-orphan")
	tokens: Mapped[list[JWT_Token]] = relationship(back_populates="user", cascade="all, delete-orphan")


class JWT_Token(Base):
	__tablename__ = "jwt_tokens"

	id               : Mapped[int] = mapped_column(primary_key=True)
	token            : Mapped[str] = mapped_column(Text, nullable=False)
	user_id          : Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
	created          : Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
	type             : Mapped[JWT_Type] = mapped_column(SqlEnum(JWT_Type, native_enum=False))
	last_used        : Mapped[datetime] = mapped_column(DateTime, nullable=False)
	device_name      : Mapped[str] = mapped_column(String(100), nullable=False)
	on_creation_ip   : Mapped[str] = mapped_column(String(45), nullable=False)
	expires_at       : Mapped[datetime] = mapped_column(DateTime, nullable=False)
	is_revoked       : Mapped[bool] = mapped_column(Boolean, default=False)

	user: Mapped[User] = relationship(back_populates="tokens")


class Translation(Base):
	__tablename__ = "translations"

	id                 : Mapped[int] = mapped_column(primary_key=True)
	translation_code   : Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
	full_name          : Mapped[str] = mapped_column(String(100), nullable=False)

	topic_translations: Mapped[list[TopicTranslation]] = relationship(back_populates="translation", cascade="all, delete-orphan")


class Topic(Base):
	__tablename__ = "topic"

	id                 : Mapped[int] = mapped_column(primary_key=True)
	name               : Mapped[str] = mapped_column(String(200), nullable=False)
	name_hash          : Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
	created_at         : Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
	edited_at          : Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
	creator_user_id    : Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

	creator: Mapped[User] = relationship(back_populates="topic")
	translations: Mapped[list[TopicTranslation]] = relationship(back_populates="topic", cascade="all, delete-orphan")

	categories: Mapped[list[Category]] = relationship(
		secondary="categories_in_topic",
		back_populates="topic"
	)

	tags: Mapped[list[Tag]] = relationship(
		secondary="tags_in_topic",
		back_populates="topic"
	)

	links: Mapped[list[TopicLink]] = relationship(back_populates="topic", cascade="all, delete-orphan")


class TopicTranslation(Base):
	__tablename__ = "topic_translations"

	id               : Mapped[int] = mapped_column(primary_key=True)
	translation_id   : Mapped[int] = mapped_column(ForeignKey("translations.id", ondelete="CASCADE"), nullable=False)
	topic_id         : Mapped[int] = mapped_column(ForeignKey("topic.id", ondelete="CASCADE"), nullable=False)
	parse_mode       : Mapped[ParseMode] = mapped_column(SqlEnum(ParseMode, native_enum=False), nullable=False)
	text             : Mapped[str] = mapped_column(Text, nullable=False)

	translation: Mapped[Translation] = relationship(back_populates="topic_translations")
	topic: Mapped[Topic] = relationship(back_populates="translations")


class Category(Base):
	__tablename__ = "categories"

	id             : Mapped[int] = mapped_column(primary_key=True)
	name           : Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
	description    : Mapped[str] = mapped_column(Text)
	display_mode   : Mapped[DisplayMode] = mapped_column(SqlEnum(DisplayMode, native_enum=False))

	topic: Mapped[list[Topic]] = relationship(
		secondary="categories_in_topic",
		back_populates="categories"
	)


class CategoryInTopic(Base):
	__tablename__ = "categories_in_topic"

	topic_id       : Mapped[int] = mapped_column(ForeignKey("topic.id", ondelete="CASCADE"), primary_key=True)
	category_id    : Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)


class Tag(Base):
	__tablename__ = "tags"

	id             : Mapped[int] = mapped_column(primary_key=True)
	name           : Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
	description    : Mapped[str] = mapped_column(Text)

	topic: Mapped[list[Topic]] = relationship(
		secondary="tags_in_topic",
		back_populates="tags"
	) 


class TagInTopic(Base):
	__tablename__ = "tags_in_topic"

	topic_id   : Mapped[int] = mapped_column(ForeignKey("topic.id", ondelete="CASCADE"), primary_key=True)
	tag_id     : Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class TopicLink(Base):
	__tablename__ = "topic_links"

	id         : Mapped[int] = mapped_column(primary_key=True)
	topic_id   : Mapped[int] = mapped_column(ForeignKey("topic.id", ondelete="CASCADE"), nullable=False)
	link_name  : Mapped[str] = mapped_column(String(200), nullable=False)
	link_url   : Mapped[str] = mapped_column(String(500), nullable=False)
	away       : Mapped[bool] = mapped_column(Boolean, default=False)

	topic: Mapped[Topic] = relationship(back_populates="links")
