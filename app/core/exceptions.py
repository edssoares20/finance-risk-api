class DomainError(Exception):
    """Raiz de todos os erros de negócio. Nunca herde de HTTPException aqui."""


class MarketDataUnavailableError(DomainError):
    pass


class UnknownTickerError(DomainError):
    def __init__(self, tickers: list[str]) -> None:
        self.tickers = tickers
        super().__init__(f"Tickers não encontrados: {', '.join(tickers)}")


class InsufficientDataError(DomainError):
    pass
