from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend_financiero import financial_agent
from backend_marketing import marketing_agent
from backend_mercado import market_agent
from typing import Optional  # Asegúrate de que este import esté presente
from pydantic import BaseModel
# Crear instancia de FastAPI
app = FastAPI(title="API de Agentes", version="1.0")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],        # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],        # Permitir todos los encabezados
)

# Modelos de datos para las solicitudes y respuestas
class FinancialRequest(BaseModel):
    user_input: str

class MarketingRequest(BaseModel):
    user_input: str
    producto: Optional[str] = None
    objetivo: Optional[str] = None
    presupuesto: Optional[float] = None

class MarketRequest(BaseModel):
    user_input: str
    categoria: Optional[str] = None
    ubicacion: Optional[str] = None

# Rutas de la API

@app.post("/agente_financiero/")
async def agente_financiero(request: FinancialRequest):
    try:
        response = financial_agent(request.user_input)
        return {"respuesta": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agente_marketing/")
async def agente_marketing(request: MarketingRequest):
    try:
        response = marketing_agent(
            user_input=request.user_input,
            producto=request.producto,
            objetivo=request.objetivo,
            presupuesto=request.presupuesto
        )
        return {"respuesta": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agente_mercado/")
async def agente_mercado(request: MarketRequest):
    try:
        response = market_agent(
            user_input=request.user_input,
            categoria=request.categoria,
            ubicacion=request.ubicacion
        )
        return {"respuesta": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
