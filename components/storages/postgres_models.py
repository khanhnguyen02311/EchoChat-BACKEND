# SQLAlchemy 2.0 Migrations:
# docs.sqlalchemy.org/en/20/changelog/whatsnew_20.html#step-three-apply-exact-python-types-as-needed-using-orm-mapped
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from typing_extensions import Annotated
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from components.storages import Engine

# declare special types
str16 = Annotated[str, None]
str128 = Annotated[str, None]
str256 = Annotated[str, None]
smallint = Annotated[int, None]
timestamp = Annotated[datetime, mapped_column(nullable=False, default=datetime.utcnow())]
int_PK = Annotated[int, mapped_column(primary_key=True)]


class Base(DeclarativeBase):
    type_annotation_map = {
        str16: types.VARCHAR(16),
        str128: types.VARCHAR(128),
        str256: types.VARCHAR(256),
        smallint: types.SMALLINT,
        timestamp: types.TIMESTAMP,
    }


# ==============================================================================
class TestingTable(Base):
    __tablename__ = 'TestingTable'
    id: Mapped[int_PK]
    item: Mapped[str128]
    optional_item: Mapped[Optional[str128]]
    number: Mapped[int]


# ==============================================================================
class Account(Base):
    __tablename__ = 'Account'
    id: Mapped[int_PK]
    username: Mapped[str128]  # Mapped without Optional[] is set to nullable = False
    password: Mapped[str128]
    email: Mapped[str128]
    time_created: Mapped[timestamp]

    id_AccountInfo: Mapped[int] = mapped_column(ForeignKey("AccountInfo.id"))
    rel_AccountInfo: Mapped["AccountInfo"] = relationship(back_populates="rel_Account",
                                                          cascade='save-update, merge, delete')

    # Address reference
    rel_Addresses: Mapped[List["Address"]] = relationship(cascade='save-update, merge, delete')


# ==============================================================================
class AccountInfo(Base):
    __tablename__ = 'AccountInfo'
    id: Mapped[int_PK]
    name: Mapped[str128]
    age: Mapped[Optional[smallint]]  # Mapped with Optional[] is set to nullable = True
    phone_number: Mapped[Optional[str16]]

    # Account reference
    rel_Account: Mapped["Account"] = relationship(back_populates='rel_AccountInfo', uselist=False)


# ==============================================================================
class Address(Base):
    __tablename__ = 'Address'
    id: Mapped[int_PK]
    detail_address: Mapped[str128]

    id_Account: Mapped[int] = mapped_column(ForeignKey("Account.id"))


# ==============================================================================
class ChatGroup(Base):
    __tablename__ = 'ChatGroup'
    id: Mapped[int_PK]
    name: Mapped[str128]

    rel_ChatParticipants: Mapped[List["ChatParticipant"]] = relationship(cascade='save-update, merge, delete')
    rel_ChatMessages: Mapped[List["ChatMessage"]] = relationship()


# ==============================================================================
class ChatParticipant(Base):
    __tablename__ = 'ChatParticipant'

    id: Mapped[int_PK]
    notify: Mapped[bool]

    id_Account: Mapped[int] = mapped_column(ForeignKey("Account.id"))
    id_ChatGroup: Mapped[int] = mapped_column(ForeignKey("ChatGroup.id"))


# ==============================================================================
class ChatMessage(Base):
    __tablename__ = 'ChatMessage'

    id: Mapped[int_PK]
    text: Mapped[str256]

    id_ChatParticipant: Mapped["ChatParticipant"] = mapped_column(ForeignKey("ChatParticipant.id"))
    id_ChatGroup: Mapped[int] = mapped_column(ForeignKey("ChatGroup.id"))


# ==============================================================================
Base.metadata.create_all(Engine)
