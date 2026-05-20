import os

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://order_user:order_pass@localhost:5432/order_db",
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    id_account = Column(String, nullable=False, index=True)
    date = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    total = Column(Float, nullable=False)

    items = relationship("OrderItemModel", back_populates="order", lazy="selectin")


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True)
    id_order = Column(String, ForeignKey("orders.id"), nullable=False)
    id_product = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)

    order = relationship("OrderModel", back_populates="items")


async def get_session() -> AsyncSession:  # type: ignore[override]
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
