# 📊 Finance & Risk API

> API REST para análise quantitativa de risco e retorno de carteiras de investimento, construída sobre princípios de Clean Architecture.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0_Async-D71F00?style=flat-square)](https://www.sqlalchemy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.2-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

[**🚀 Demo ao vivo**](https://finance-risk-api-ostg.onrender.com/docs)

> ⏱️ A demo roda no plano gratuito do Render e hiberna após 15 min de inatividade. A primeira requisição pode levar ~60s para acordar o serviço.

---

## 🎯 O Problema

Todo investidor sabe quanto sua carteira rendeu. Quase nenhum sabe **quanto risco assumiu para render aquilo** — e, principalmente, **de onde esse risco veio**.

Somar o risco de cada ativo individualmente é matematicamente errado: a covariância entre eles pode reduzir drasticamente o risco total. É o efeito da diversificação, e ele só aparece quando você trabalha com a matriz de covariância completa.

Esta API resolve isso. Você envia uma carteira e recebe:

| Métrica | O que responde |
|---|---|
| **Retorno Esperado Anualizado** | Quanto essa alocação renderia ao ano, com base na série histórica |
| **Volatilidade Anualizada** | O risco real da carteira, já considerando a correlação entre os ativos |
| **Índice de Sharpe** | Quanto retorno você ganha por unidade de risco assumida |
| **Contribuição Marginal de Risco** | 🎯 Quem está trazendo o risco — decomposição de Euler por ativo |

## 🏗️ Diferencial Técnico: Arquitetura Limpa

```
┌─────────────────────────────────────────────────────┐
│  API Layer          (FastAPI routers)               │  ← conhece HTTP
│  ↓ depende de                                       │
│  Service Layer      (orquestração + risk engine)    │  ← lógica pura
│  ↓ depende de ABSTRAÇÕES (Protocols), não de libs   │
│  Repository Layer   (yfinance · SQLAlchemy · mock)  │  ← I/O isolado
└─────────────────────────────────────────────────────┘
```

O serviço de análise **não sabe que o `yfinance` existe**. Ele depende de um `Protocol`:

```python
class MarketDataRepository(Protocol):
    async def get_close_prices(
        self, tickers: list[str], start: date, end: date
    ) -> pd.DataFrame: ...
```

| Quero trocar… | Mudo apenas… | Regra de negócio afetada |
|---|---|---|
| `yfinance` → outro provedor | uma classe em `repositories/` | **Zero** |
| SQLite → PostgreSQL | a variável `DATABASE_URL` | **Zero** |
| Rodar offline, sem internet | `USE_MOCK_MARKET_DATA=true` | **Zero** |

## 📐 A Matemática

Retornos simples diários:

$$r_{i,t} = \frac{P_{i,t}}{P_{i,t-1}} - 1$$

Retorno da carteira e anualização composta:

$$\mu_p = \mathbf{w}^\top \boldsymbol{\mu} \qquad R_{anual} = (1 + \mu_p)^{252} - 1$$

Volatilidade — forma quadrática de Markowitz:

$$\sigma_p = \sqrt{\mathbf{w}^\top \Sigma \mathbf{w}} \qquad \sigma_{anual} = \sigma_p \cdot \sqrt{252}$$

> ⚠️ Este projeto não é recomendação de investimento. É uma demonstração de engenharia de software e modelagem quantitativa.

## 🛠️ Stack

Python · FastAPI · Pydantic v2 · Pandas · NumPy · yfinance · SQLAlchemy 2.0 Async · SQLite/PostgreSQL · Tenacity

## 🚀 Rodando localmente

```bash
git clone https://github.com/edssoares20/finance-risk-api.git
cd finance-risk-api

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
echo "USE_MOCK_MARKET_DATA=true" > .env

uvicorn app.main:app --reload
```

Acesse **http://localhost:8000/docs**

## 📡 Exemplo de Uso

```bash
curl -X POST http://localhost:8000/api/v1/portfolio/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "assets": [
      {"ticker": "PETR4.SA", "weight": "0.30"},
      {"ticker": "VALE3.SA", "weight": "0.25"},
      {"ticker": "ITUB4.SA", "weight": "0.25"},
      {"ticker": "WEGE3.SA", "weight": "0.20"}
    ],
    "lookback_days": 504
  }'
```

```json
{
  "expected_return_annual": 0.2537,
  "volatility_annual": 0.1575,
  "sharpe_ratio": 0.9756,
  "observations": 477,
  "positions": [
    {"ticker": "PETR4.SA", "weight": 0.30, "risk_contribution": 0.2713},
    {"ticker": "VALE3.SA", "weight": 0.25, "risk_contribution": 0.2628},
    {"ticker": "ITUB4.SA", "weight": 0.25, "risk_contribution": 0.2380},
    {"ticker": "WEGE3.SA", "weight": 0.20, "risk_contribution": 0.2279}
  ]
}
```

## 🗺️ Roadmap

- [ ] Cache com TTL consciente de pregão
- [ ] VaR e CVaR por simulação de Monte Carlo
- [ ] Fronteira eficiente de Markowitz
- [ ] Testes automatizados com Hypothesis

## 📄 Licença

MIT

## 👤 Autor

Edson Soares — Estudante de Engenharia · UFBA

[GitHub](https://github.com/edssoares20)

---

<sub>⚠️ Projeto educacional. Não constitui recomendação de investimento.</sub>
