from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TOLERANCE = Decimal("0.0001")


class AssetAllocation(BaseModel):
    ticker: str = Field(..., min_length=3, max_length=12, examples=["PETR4.SA"])
    weight: Decimal = Field(..., gt=0, le=1, examples=["0.35"])

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.strip().upper()


class PortfolioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assets: list[AssetAllocation] = Field(..., min_length=2, max_length=50)
    lookback_days: int = Field(default=504, ge=60, le=2520)

    @model_validator(mode="after")
    def validate_portfolio(self) -> "PortfolioRequest":
        tickers = [a.ticker for a in self.assets]

        if len(set(tickers)) != len(tickers):
            dups = {t for t in tickers if tickers.count(t) > 1}
            raise ValueError(f"Tickers duplicados: {', '.join(sorted(dups))}")

        total = sum(a.weight for a in self.assets)
        if abs(total - Decimal(1)) > TOLERANCE:
            raise ValueError(
                f"Os pesos devem somar 1.0 (100%). Soma recebida: {total}. "
                f"Diferença: {total - Decimal(1)}"
            )
        return self


class PositionRisk(BaseModel):
    ticker: str
    weight: float
    risk_contribution: float = Field(
        ..., description="Fração do risco total atribuída a este ativo (soma = 1.0)"
    )


class RiskAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    expected_return_annual: float
    volatility_annual: float
    sharpe_ratio: float
    observations: int
    positions: list[PositionRisk]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_freshness: Literal["live", "stale"] = "live"

    @classmethod
    def from_metrics(cls, metrics, weights: dict[str, float]) -> "RiskAnalysisResponse":
        return cls(
            expected_return_annual=metrics.expected_return_annual,
            volatility_annual=metrics.volatility_annual,
            sharpe_ratio=metrics.sharpe_ratio,
            observations=metrics.observations,
            positions=[
                PositionRisk(
                    ticker=t,
                    weight=w,
                    risk_contribution=metrics.risk_contribution.get(t, 0.0),
                )
                for t, w in weights.items()
            ],
        )
