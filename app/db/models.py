"""
Modelos ORM (SQLAlchemy 2.0, estilo declarativo tipado com Mapped[]).

IMPORTANTE: estes modelos NÃO são os schemas Pydantic. Manter os dois
separados é o que permite mudar o banco sem quebrar o contrato da API
(e vice-versa). A conversão acontece no repositório.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa única — o Alembic usa este metadata para gerar migrations."""


class PortfolioAnalysis(Base):
    __tablename__ = "portfolio_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # server_default=func.now() deixa o carimbo com o banco, não com o app.
    # Em ambiente distribuído, relógio de aplicação diverge; o do banco não.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    expected_return_annual: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_annual: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    observations: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_free_rate: Mapped[float] = mapped_column(Float, nullable=False)
    lookback_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Hash determinístico da carteira (tickers + pesos ordenados).
    # Permite responder "já analisei essa carteira hoje?" com um índice,
    # em vez de varrer as posições. É a base da Tarefa 1 (cache).
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    positions: Mapped[list["AnalysisPosition"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        # lazy="selectin" evita o problema N+1 E o erro de lazy-load em
        # contexto async (o SQLAlchemy async não faz I/O implícito no acesso
        # ao atributo — sem isso, você toma MissingGreenlet em produção).
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_analysis_fingerprint_created", "fingerprint", "created_at"),
    )


class AnalysisPosition(Base):
    __tablename__ = "analysis_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticker: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    risk_contribution: Mapped[float] = mapped_column(Float, nullable=False)

    analysis: Mapped["PortfolioAnalysis"] = relationship(back_populates="positions")

    # Mesmo ticker duas vezes na mesma análise é dado corrompido.
    # O Pydantic já barra na entrada, mas a integridade no banco é a
    # última linha de defesa (scripts, imports, bugs futuros).
    __table_args__ = (UniqueConstraint("analysis_id", "ticker", name="uq_analysis_ticker"),)
