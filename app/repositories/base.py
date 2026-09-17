"""
Interfaces do domínio. Uso `Protocol` (tipagem estrutural) em vez de ABC:
a implementação não precisa herdar de nada — basta ter os métodos com a
assinatura certa. Isso evita acoplamento de herança e deixa o mypy validar
o contrato em tempo de checagem, sem importar SQLAlchemy ou yfinance aqui.
"""
from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

import pandas as pd

from app.schemas.portfolio import RiskAnalysisResponse


@runtime_checkable
class MarketDataRepository(Protocol):
    """Fonte de preços. Pode ser yfinance, mock, CSV local ou cache."""

    async def get_close_prices(
        self, tickers: list[str], start: date, end: date
    ) -> pd.DataFrame:
        """
        Contrato explícito (isto é o que segura o projeto no longo prazo):
          - Retorna DataFrame indexado por data (ascendente).
          - Uma coluna por ticker, nomeada exatamente como o ticker recebido.
          - Preços de FECHAMENTO AJUSTADO (dividendos e splits já aplicados).
          - Ticker inexistente vira coluna toda NaN ou coluna ausente.
          - Levanta MarketDataUnavailableError se a fonte falhar.
        """
        ...


@runtime_checkable
class AnalysisRepository(Protocol):
    """Persistência do histórico de análises."""

    async def save(self, analysis: RiskAnalysisResponse) -> int: ...

    async def get_by_id(self, analysis_id: int) -> RiskAnalysisResponse | None: ...

    async def list_recent(self, limit: int = 20) -> list[RiskAnalysisResponse]: ...
