from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.exceptions import InsufficientDataError, UnknownTickerError
from app.repositories.base import AnalysisRepository, MarketDataRepository
from app.schemas.portfolio import PortfolioRequest, RiskAnalysisResponse
from app.services import risk_engine


class PortfolioAnalysisService:
    """
    Orquestra o caso de uso. Depende de ABSTRAÇÕES (Protocols), não de yfinance.
    Nos testes eu injeto um repositório fake e rodo tudo offline em milissegundos.
    """

    def __init__(
        self,
        market_data: MarketDataRepository,
        analysis_repo: AnalysisRepository,
    ) -> None:
        self._market_data = market_data
        self._analysis_repo = analysis_repo

    async def analyze(self, request: PortfolioRequest) -> RiskAnalysisResponse:
        weights = {a.ticker: float(a.weight) for a in request.assets}
        end = datetime.now(timezone.utc).date()
        # +40% de folga no calendário: 252 pregões ≈ 365 dias corridos.
        start = end - timedelta(days=int(request.lookback_days * 1.4))

        # O repositório pode levantar MarketDataUnavailableError.
        # Deixamos subir: o handler no main.py traduz para 503.
        prices = await self._market_data.get_close_prices(
            tickers=list(weights.keys()), start=start, end=end
        )

        # Ticker que não existe volta como coluna 100% NaN, não como erro.
        missing = [
            t
            for t in weights
            if t not in prices.columns or bool(prices[t].isna().all())
        ]
        if missing:
            raise UnknownTickerError(tickers=missing)

        returns = risk_engine.compute_daily_returns(prices)

        try:
            metrics = risk_engine.analyze(
                returns=returns,
                weights=weights,
                risk_free_rate=settings.RISK_FREE_RATE,
            )
        except ValueError as exc:
            # Traduz erro técnico do engine em erro de domínio.
            raise InsufficientDataError(str(exc)) from exc

        response = RiskAnalysisResponse.from_metrics(metrics, weights=weights)
        await self._analysis_repo.save(response)  # histórico no SQLite
        return response
