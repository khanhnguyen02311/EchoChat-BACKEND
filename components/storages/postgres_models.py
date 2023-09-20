# SQLAlchemy 2.0 Migrations:
# docs.sqlalchemy.org/en/20/changelog/whatsnew_20.html#step-three-apply-exact-python-types-as-needed-using-orm-mapped
import random, string
from datetime import datetime
from typing import Annotated, Optional, List
from sqlalchemy import ForeignKey, types, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

# declare datatypes
str16 = Annotated[str, None]
str64 = Annotated[str, None]
str128 = Annotated[str, None]
str256 = Annotated[str, None]
str_random = Annotated[str, mapped_column(default=''.join(random.choices(string.ascii_letters + string.digits, k=16)))]

smallint = Annotated[int, None]
int_identifier = Annotated[int, mapped_column(default=random.randint(1, 9999))]
int_PK = Annotated[int, mapped_column(primary_key=True)]

timestamp = Annotated[datetime, mapped_column(default=datetime.utcnow)]


class Base(DeclarativeBase):
    type_annotation_map = {
        str16: types.VARCHAR(16),
        str64: types.VARCHAR(64),
        str128: types.VARCHAR(128),
        str256: types.VARCHAR(256),
        str_random: types.VARCHAR(64),
        smallint: types.SMALLINT,
        int_identifier: types.SMALLINT,
        timestamp: types.TIMESTAMP,
    }


Friend = Table(
    "friend", Base.metadata,
    Column("accountinfo_id_user", ForeignKey("accountinfo.id"), primary_key=True),
    Column("accountinfo_id_friend", ForeignKey("accountinfo.id"), primary_key=True),
)


# ==============================================================================
class Account(Base):
    __tablename__ = 'account'
    id: Mapped[int_PK]
    username: Mapped[str128]  # Mapped without Optional[] is set to nullable = False
    password: Mapped[str128]
    email: Mapped[str128]
    time_created: Mapped[timestamp]

    accountinfo_id: Mapped[int] = mapped_column(ForeignKey("accountinfo.id"))
    accountinfo_rel: Mapped["Accountinfo"] = relationship(back_populates="account_rel",
                                                          cascade='save-update, merge, delete')


# ==============================================================================
class Accountinfo(Base):
    __tablename__ = 'accountinfo'
    id: Mapped[int_PK]
    name: Mapped[str_random]
    identifier: Mapped[int_identifier]
    description: Mapped[Optional[str128]]

    accountattachment_id: Mapped[Optional[int]] = mapped_column(ForeignKey('accountattachment.id'))
    accountattachment_rel: Mapped[Optional['Accountattachment']] = relationship(back_populates="accountinfo_rel",
                                                                                cascade='save-update, merge, delete')

    # Account reference
    account_rel: Mapped["Account"] = relationship(back_populates='accountinfo_rel')

    # friend_rel: Mapped[List["Accountinfo"]] = relationship("Accountinfo", secondary=Friend,
    #                                                        primaryjoin=id == Friend.c.accountinfo_id_user,
    #                                                        secondaryjoin=id == Friend.c.accountinfo_id_friend)


# ==============================================================================
class Accountattachment(Base):
    __tablename__ = 'accountattachment'
    id: Mapped[int_PK]
    filename: Mapped[str128]

    accountinfo_rel: Mapped[Optional["Accountinfo"]] = relationship(back_populates="accountattachment_rel")

# ==============================================================================
