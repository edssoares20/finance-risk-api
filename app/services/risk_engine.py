"""
Motor de risco. Funções puras, sem I/O e sem async.
Toda a matemática do projeto mora aqui — e é aqui que os testes mordem.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252  # Padrão de mercado para séries diárias
MIN_OBSERVATIONS = 60        # Abaixo disso, a covariância é ruído puro


@dataclass(frozen=True)
class RiskMetrics:
    expected_return_annual: float
    volatility_annual: float
    sharpe_ratio: float
    observations: int
    risk_contribution: dict[str, float]  # Quanto cada ativo contribui do risco total


def compute_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Converte preços de fechamento ajustado em retornos SIMPLES diários.

    Por que simples e não logarítmico?
    O retorno de uma carteira é a média ponderada dos retornos simples
    dos ativos. Isso NÃO vale para log-retornos (log da soma != soma dos logs).
    Como o objetivo aqui é agregar ativos, simples é o correto.
    """
    # ffill limitado cobre feriados de bolsas diferentes (ex: BOVA11 vs SPY).
    # dropna(how="any") garante que todos os ativos tenham o mesmo eixo temporal:
    # calcular covariância com datas desalinhadas gera correlação fantasma.
    prices = prices.sort_index().ffill(limit=3)
    returns = prices.pct_change().dropna(how="any")
    return returns


def analyze(
    returns: pd.DataFrame,
    weights: dict[str, float],
    risk_free_rate: float,
) -> RiskMetrics:
    """
    Recebe a matriz de retornos diários (T x N) e os pesos da carteira.
    Devolve retorno esperado e volatilidade, ambos anualizados.
    """
    if len(returns) < MIN_OBSERVATIONS:
        raise ValueError(
            f"Amostra insuficiente: {len(returns)} observações "
            f"(mínimo {MIN_OBSERVATIONS})."
        )

    tickers = list(weights.keys())

    # Reordena colunas para casar EXATAMENTE com a ordem do vetor de pesos.
    # Bug clássico e silencioso: o pandas devolve colunas em ordem alfabética
    # e você multiplica o peso da PETR4 pelo retorno da VALE3.
    returns = returns[tickers]
    w = np.array([weights[t] for t in tickers], dtype=float)

    # --- Retorno esperado ---
    mu_daily_assets = returns.mean().to_numpy()      # vetor μ (N,)
    mu_daily_portfolio = float(w @ mu_daily_assets)  # produto interno wᵀμ

    # Anualização composta: assume reinvestimento diário.
    # A alternativa linear (μ * 252) superestima em carteiras voláteis.
    expected_return_annual = (1.0 + mu_daily_portfolio) ** TRADING_DAYS_PER_YEAR - 1.0

    # --- Volatilidade ---
    # ddof=1 = covariância AMOSTRAL (divide por T-1). Estamos estimando a
    # população a partir de uma amostra, então a correção de Bessel é obrigatória.
    cov_daily = returns.cov(ddof=1).to_numpy()       # matriz Σ (N x N)

    variance_daily = float(w @ cov_daily @ w)        # forma quadrática wᵀΣw
    variance_daily = max(variance_daily, 0.0)        # blinda erro de ponto flutuante
    vol_daily = np.sqrt(variance_daily)

    # Regra da raiz do tempo: variância escala linear no tempo,
    # desvio-padrão escala com √t. Vale sob i.i.d. (ver ressalvas na seção 3).
    volatility_annual = vol_daily * np.sqrt(TRADING_DAYS_PER_YEAR)

    # --- Sharpe ---
    sharpe = (
        (expected_return_annual - risk_free_rate) / volatility_annual
        if volatility_annual > 1e-12
        else 0.0
    )

    # --- Contribuição marginal de risco (decomposição de Euler) ---
    # Diferencial competitivo do projeto: não basta dizer "a carteira tem 22% de vol",
    # o usuário quer saber QUEM está trazendo esse risco.
    if vol_daily > 1e-12:
        marginal = (cov_daily @ w) / vol_daily          # ∂σ/∂w
        contribution = (w * marginal) / vol_daily       # soma = 1.0
    else:
        contribution = np.zeros_like(w)

    return RiskMetrics(
        expected_return_annual=round(expected_return_annual, 6),
        volatility_annual=round(volatility_annual, 6),
        sharpe_ratio=round(sharpe, 4),
        observations=len(returns),
        risk_contribution={
            t: round(float(c), 6) for t, c in zip(tickers, contribution)
        },
    )
