from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    InsufficientDataError,
    MarketDataUnavailableError,
    UnknownTickerError,
)
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Aqui entram recursos caros e de vida longa: pool de conexões,
    # cliente HTTP reutilizável, warm-up de cache.
    await init_db()  # cria as tabelas na subida
    yield
    # Shutdown gracioso: fechar conexões abertas.


def create_app() -> FastAPI:
    """App factory — permite instanciar apps isolados nos testes."""
    app = FastAPI(
        title="Finance & Risk API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(MarketDataUnavailableError)
    async def _market_data_down(request: Request, exc: MarketDataUnavailableError):
        return JSONResponse(
            status_code=503,
            content={"error": "market_data_unavailable", "detail": str(exc)},
            headers={"Retry-After": "30"},
        )

    @app.exception_handler(UnknownTickerError)
    async def _unknown_ticker(request: Request, exc: UnknownTickerError):
        return JSONResponse(
            status_code=422,
            content={"error": "unknown_ticker", "tickers": exc.tickers},
        )

    @app.exception_handler(InsufficientDataError)
    async def _insufficient_data(request: Request, exc: InsufficientDataError):
        return JSONResponse(
            status_code=422,
            content={"error": "insufficient_data", "detail": str(exc)},
        )

    return app


app = create_app()
