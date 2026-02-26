from sqlalchemy import Table, Column, ForeignKey
from .base import Base

author_book = Table("author_book",Base.metadata,
    Column("author_id", ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True))