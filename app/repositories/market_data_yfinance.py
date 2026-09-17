import asyncio
from datetime import date

import pandas as pd
import yfinance as yf
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import MarketDataUnavailableError


class YFinanceMarketDataRepository:
    def __init__(self, timeout_seconds: float = 12.0) -> None:
        self._timeout = timeout_seconds

    @retry(
        # Backoff exponencial: 1s, 2s, 4s. Sem isso, um retry agressivo
        # vira DDoS contra o provedor e você toma rate limit permanente.
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def get_close_prices(
        self, tickers: list[str], start: date, end: date
    ) -> pd.DataFrame:
        try:
            # yfinance é SÍNCRONO e bloqueante. Chamar direto numa rota async
            # congela o event loop inteiro e derruba o throughput da API.
            # to_thread joga para a thread pool; wait_for impõe teto de tempo.
            raw = await asyncio.wait_for(
                asyncio.to_thread(
                    yf.download,
                    tickers=tickers,
                    start=start,
                    end=end,
                    auto_adjust=True,   # ajusta por dividendos/splits
                    progress=False,
                    threads=True,
                ),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError as exc:
            raise MarketDataUnavailableError(
                f"Timeout de {self._timeout}s ao consultar o provedor."
            ) from exc
        except Exception as exc:
            # yfinance levanta exceções genéricas e inconsistentes.
            # Encapsulamos tudo numa exceção de domínio: nenhuma camada
            # acima precisa saber que existe uma lib chamada yfinance.
            raise MarketDataUnavailableError(str(exc)) from exc

        if raw is None or raw.empty:
            raise MarketDataUnavailableError("Provedor retornou payload vazio.")

        # Com múltiplos tickers o retorno é MultiIndex; normalizamos o formato
        # para que o resto do sistema sempre receba um DataFrame (datas x tickers).
        close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
        return close.rename(columns={"Close": tickers[0]}) if len(tickers) == 1 else close
