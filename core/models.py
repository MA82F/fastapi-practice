from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    func,
    Integer,
    Float,
    DateTime,
    ForeignKey,
)
from core.database import Base
from sqlalchemy.orm import relationship


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(150), nullable=False)
    password = Column(String(150), nullable=False)

    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(
        DateTime, server_default=func.now(), server_onupdate=func.now()
    )

    costs = relationship("CostModel", back_populates="user")


class CostModel(Base):
    __tablename__ = "costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)

    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(
        DateTime, server_default=func.now(), server_onupdate=func.now()
    )

    user = relationship("UserModel", back_populates="costs", uselist=False)
