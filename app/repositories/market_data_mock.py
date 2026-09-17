from datetime import date

import numpy as np
import pandas as pd


class MockMarketDataRepository:
    """
    Gera séries sintéticas por Movimento Browniano Geométrico.
    Com seed fixa é determinístico — perfeito para teste e dev offline.
    """

    def __init__(self, seed: int = 42, annual_drift: float = 0.12, annual_vol: float = 0.28):
        self._seed, self._drift, self._vol = seed, annual_drift, annual_vol

    async def get_close_prices(self, tickers: list[str], start: date, end: date) -> pd.DataFrame:
        rng = np.random.default_rng(self._seed)
        days = pd.bdate_range(start=start, end=end)          # só dias úteis
        n = len(days)
        mu_d, sigma_d = self._drift / 252, self._vol / np.sqrt(252)

        # Fator de mercado comum → gera correlação realista entre os ativos.
        market = rng.normal(0, 1, n)
        data = {}
        for i, ticker in enumerate(tickers):
            beta = 0.6 + 0.3 * ((i % 3) / 2)
            shocks = beta * market + np.sqrt(max(1 - beta**2, 0.05)) * rng.normal(0, 1, n)
            returns = mu_d + sigma_d * shocks
            data[ticker] = 50.0 * np.exp(np.cumsum(returns))

        return pd.DataFrame(data, index=days)
