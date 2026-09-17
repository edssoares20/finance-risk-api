import hashlib

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import AnalysisPosition, PortfolioAnalysis
from app.schemas.portfolio import PositionRisk, RiskAnalysisResponse


def build_fingerprint(positions: list[PositionRisk]) -> str:
    payload = "|".join(f"{p.ticker}:{p.weight:.6f}" for p in sorted(positions, key=lambda x: x.ticker))
    return hashlib.sha256(payload.encode()).hexdigest()


class SqlAlchemyAnalysisRepository:
    """Implementa AnalysisRepository sem herdar dele — tipagem estrutural."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, analysis: RiskAnalysisResponse) -> int:
        row = PortfolioAnalysis(
            expected_return_annual=analysis.expected_return_annual,
            volatility_annual=analysis.volatility_annual,
            sharpe_ratio=analysis.sharpe_ratio,
            observations=analysis.observations,
            risk_free_rate=settings.RISK_FREE_RATE,
            lookback_days=0,
            fingerprint=build_fingerprint(analysis.positions),
            positions=[
                AnalysisPosition(
                    ticker=p.ticker,
                    weight=p.weight,
                    risk_contribution=p.risk_contribution,
                )
                for p in analysis.positions
            ],
        )
        self._session.add(row)
        # flush (não commit): materializa o ID sem encerrar a transação.
        # Quem decide o commit é o get_session — Unit of Work continua íntegro.
        await self._session.flush()
        analysis.id = row.id
        return row.id

    async def get_by_id(self, analysis_id: int) -> RiskAnalysisResponse | None:
        row = await self._session.get(PortfolioAnalysis, analysis_id)
        return self._to_schema(row) if row else None

    async def list_recent(self, limit: int = 20) -> list[RiskAnalysisResponse]:
        stmt = select(PortfolioAnalysis).order_by(desc(PortfolioAnalysis.created_at)).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._to_schema(r) for r in rows]

    @staticmethod
    def _to_schema(row: PortfolioAnalysis) -> RiskAnalysisResponse:
        return RiskAnalysisResponse(
            id=row.id,
            expected_return_annual=row.expected_return_annual,
            volatility_annual=row.volatility_annual,
            sharpe_ratio=row.sharpe_ratio,
            observations=row.observations,
            generated_at=row.created_at,
            positions=[
                PositionRisk(ticker=p.ticker, weight=p.weight, risk_contribution=p.risk_contribution)
                for p in row.positions
            ],
        )
