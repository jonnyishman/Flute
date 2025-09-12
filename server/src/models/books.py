"""Book and Chapter models for storing book information."""
from __future__ import annotations

import datetime as dt
from enum import IntEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import AuditMixin, db
from src.models.language import Language


class Book(db.Model, AuditMixin):
    """Book model representing books in the application."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    language_id: Mapped[int] = mapped_column(Integer, ForeignKey(Language.id), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    cover_art_filepath: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_visited_chapter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_visited_word_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_read: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    chapters = relationship(
        "Chapter",
        back_populates="book",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    language = relationship(Language)


class Chapter(db.Model, AuditMixin):
    """Chapter model representing individual chapters within books."""

    __tablename__ = "chapters"
    __table_args__ = (
        Index("ix_chapter_book_id_chapter_number", "book_id", "chapter_number", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    book_id: Mapped[int] = mapped_column(Integer, ForeignKey(Book.id), nullable=False)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    book: Mapped[Book] = relationship("Book", back_populates="chapters", lazy="select")


class TokenKind(IntEnum):
    WORD = 1
    PHRASE = 2


class Token(db.Model):
    """One row per normalised token (word or phrase)"""
    __tablename__ = "tokens"
    __table_args__ = (
        CheckConstraint("kind IN (1, 2)", name="ck_token_kind_valid"),
        Index("ix_token_language_id_norm", "language_id", "norm", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    language_id: Mapped[int] = mapped_column(Integer, ForeignKey(Language.id), nullable=False)
    norm: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default=str(TokenKind.WORD.value)
    )

    # Relationships
    language = relationship(Language)


class BookVocab(db.Model):
    """
    Inverted index; which tokens appear in which book, with token counts.
    Primary key is (book_id, token_id) so we can optionally use WITHOUT ROWID.
    """
    __tablename__ = "book_vocab"
    __table_args__ = (
        # Covering index in the other direction
        Index("ix_book_vocab_token_book_count", "token_id", "book_id", "token_count"),
        {"sqlite_with_rowid": False},
    )

    # Composite primary key: (book_id, token_id)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey(Book.id), primary_key=True)
    token_id: Mapped[int] = mapped_column(Integer, ForeignKey(Token.id), primary_key=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)


class LearningStatus(IntEnum):
    LEARNING = 1
    KNOWN = 2
    IGNORE = 3


NUM_LEARNING_STAGES = 5


class TokenProgress(db.Model, AuditMixin):
    """Tracking user progress through unique tokens"""
    __tablename__ = "token_progress"
    __table_args__ = (
        CheckConstraint("status IN (1, 2, 3)", name="ck_token_progress_status_valid"),
        CheckConstraint(
            "(status != 1) OR (learning_stage BETWEEN 1 AND 5)",
            name="ck_token_progress_learning_stage_valid"
        ),
        # For fast lookup of all learning/known tokens
        Index("ix_token_progress_status_token", "status", "token_id"),
    )

    token_id: Mapped[int] = mapped_column(Integer, ForeignKey(Token.id), primary_key=True)
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    learning_stage: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    translation: Mapped[str | None] = mapped_column(String(500), nullable=True)


class BookTotals(db.Model):
    """Per-book totals that don't change unless the book test changes"""
    __tablename__ = "book_totals"

    book_id: Mapped[int] = mapped_column(Integer, ForeignKey(Book.id, ondelete="CASCADE"), primary_key=True)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    total_types: Mapped[int] = mapped_column(Integer, nullable=False)

    @classmethod
    def upsert_stmt(cls, book_id: int, total_tokens: int, total_types: int):
        """Return an upsert statement for the given book totals."""
        return insert(cls).values(
            book_id=book_id,
            total_tokens=total_tokens,
            total_types=total_types,
        ).on_conflict_do_update(
            index_elements=[cls.book_id],
            set_={
                "total_tokens": total_tokens,
                "total_types": total_types,
            }
        )
