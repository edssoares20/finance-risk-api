from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import Base

# SQLite não cria a pasta sozinho — se ela não existir, a conexão falha.
# No Render, o filesystem começa vazio (a pasta data/ fica fora do Git
# de propósito), então precisamos garantir que ela exista antes de conectar.
if settings.DATABASE_URL.startswith("sqlite"):
    db_file = settings.DATABASE_URL.split("///")[-1]
    Path(db_file).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,          # sqlite+aiosqlite:///./data/finance.db
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # permite ler o objeto depois do commit
)


# PEGADINHA DO SQLITE: por padrão ele IGNORA foreign keys silenciosamente.
# O ondelete="CASCADE" do models.py só funciona com este PRAGMA ligado.
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")   # leituras concorrentes com escrita
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


async def init_db() -> None:
    """Cria as tabelas. OK para dev; em produção o dono disso é o Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Unit of Work por request: commit no sucesso, rollback em qualquer erro."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
