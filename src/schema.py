import enum
from sqlalchemy import Column, ForeignKey
from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class NotePermission(enum.Enum):
    freely  = 'freely'
    editable = 'editable'
    limited = 'limited'
    locked  = 'locked'
    protected = 'protected'
    private = 'private'


class Note(Base):
    __tablename__ = 'Notes'

    id          = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    shortid     = Column(String(255), nullable=False, default='0000000000')
    alias       = Column(String(255))
    ownerId     = Column(UUID(as_uuid=True), ForeignKey('Users.id'))
    content     = Column(Text)
    title       = Column(Text)
    createdAt   = Column(DateTime(timezone=True))
    deletedAt   = Column(DateTime(timezone=True))
    savedAt     = Column(DateTime(timezone=True))
    updatedAt   = Column(DateTime(timezone=True))
    lastchangeAt = Column(DateTime(timezone=True))
    lastchangeuserId = Column(UUID(as_uuid=True))
    permission  = Column(Enum(NotePermission))
    viewcount   = Column(Integer, default=0)
    authorship  = Column(Text)

    owner = relationship('User', back_populates='note')
    author = relationship('Author', back_populates='note')
    revision = relationship('Revision', back_populates='note')


class User(Base):
    __tablename__ = 'Users'

    id          = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    profileid   = Column(String(255), unique=True)
    profile     = Column(Text)
    history     = Column(Text)
    createdAt   = Column(DateTime(timezone=True))
    updatedAt   = Column(DateTime(timezone=True))
    accessToken = Column(Text)
    refreshToken = Column(Text)
    email       = Column(Text)
    password    = Column(Text)
    deleteToken = Column(UUID(as_uuid=True))

    note = relationship('Note', back_populates='owner', cascade='all, delete')
    author = relationship('Author', back_populates='user', cascade='all, delete')


class Author(Base):
    __tablename__ = 'Authors'

    id      = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    color   = Column(String(255))
    noteId  = Column(UUID(as_uuid=True), ForeignKey('Notes.id'))
    userId  = Column(UUID(as_uuid=True), ForeignKey('Users.id'))
    createdAt = Column(DateTime(timezone=True))
    updatedAt = Column(DateTime(timezone=True))

    note = relationship('Note', back_populates='author')
    user = relationship('User', back_populates='author')


class Revision(Base):
    __tablename__ = 'Revisions'

    id      = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    noteId  = Column(UUID(as_uuid=True), ForeignKey('Notes.id'))
    patch   = Column(Text)
    lastContent = Column(Text)
    content = Column(Text)
    length  = Column(Integer)
    createdAt = Column(DateTime(timezone=True))
    updatedAt = Column(DateTime(timezone=True))
    authorship = Column(Text)

    note = relationship('Note', back_populates='revision')


# class SequelizeMeta(Base): pass
# class Session(Base): pass
# class Temp(Base): pass
