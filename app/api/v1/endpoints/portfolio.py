from fastapi import APIRouter, Depends, status

from app.api.deps import get_portfolio_service
from app.schemas.portfolio import PortfolioRequest, RiskAnalysisResponse
from app.services.portfolio_service import PortfolioAnalysisService

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post(
    "/analyze",
    response_model=RiskAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Calcula retorno esperado e volatilidade anualizada de uma carteira",
)
async def analyze_portfolio(
    payload: PortfolioRequest,
    service: PortfolioAnalysisService = Depends(get_portfolio_service),
) -> RiskAnalysisResponse:
    """
    A rota faz exatamente três coisas e nada mais:
      1. Recebe o payload já validado pelo Pydantic;
      2. Delega para o serviço;
      3. Devolve o resultado.
    Zero regra de negócio aqui. Se amanhã virar um worker de fila
    ou um comando de CLI, o serviço é reaproveitado sem tocar em nada.
    """
    return await service.analyze(payload)
