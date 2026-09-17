"""
Composition root: o ÚNICO lugar do projeto que sabe quais implementações
concretas existem. Trocar yfinance por outro provedor é editar este arquivo.
"""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_session
from app.repositories.analysis_repository import SqlAlchemyAnalysisRepository
from app.repositories.base import AnalysisRepository, MarketDataRepository
from app.repositories.market_data_mock import MockMarketDataRepository
from app.repositories.market_data_yfinance import YFinanceMarketDataRepository
from app.services.portfolio_service import PortfolioAnalysisService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@lru_cache(maxsize=1)
def get_market_data_repository() -> MarketDataRepository:
    """
    Singleton: o repositório é stateless e pode carregar recursos caros
    (cliente HTTP, cache em memória). Recriar a cada request é desperdício.
    Com USE_MOCK_MARKET_DATA=true você desenvolve offline, sem rede nenhuma.
    """
    if settings.USE_MOCK_MARKET_DATA:
        return MockMarketDataRepository(seed=42)
    return YFinanceMarketDataRepository(timeout_seconds=settings.MARKET_DATA_TIMEOUT)


def get_analysis_repository(session: SessionDep) -> AnalysisRepository:
    """Este NÃO é singleton: carrega a sessão, que vive só durante o request."""
    return SqlAlchemyAnalysisRepository(session)


def get_portfolio_service(
    market_data: Annotated[MarketDataRepository, Depends(get_market_data_repository)],
    analysis_repo: Annotated[AnalysisRepository, Depends(get_analysis_repository)],
) -> PortfolioAnalysisService:
    return PortfolioAnalysisService(
        market_data=market_data,
        analysis_repo=analysis_repo,
    )
