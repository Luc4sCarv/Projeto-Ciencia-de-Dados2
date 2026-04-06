from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── TipoOperacao ──────────────────────────────────────────────
class TipoOperacaoCreate(BaseModel):
    nome_operacao: str = Field(..., example="ALUGUEL")

class TipoOperacaoOut(TipoOperacaoCreate):
    id: int
    class Config:
        from_attributes = True


# ── TipoImovel ────────────────────────────────────────────────
class TipoImovelCreate(BaseModel):
    nome_tipo_imovel: str = Field(..., example="APARTAMENTO")

class TipoImovelOut(TipoImovelCreate):
    id: int
    class Config:
        from_attributes = True


# ── Imobiliaria ───────────────────────────────────────────────
class ImobiliariaCreate(BaseModel):
    nome_imobiliaria: str = Field(..., example="Imobiliária Central DF")
    creci: Optional[str] = Field(None, example="DF-12345")

class ImobiliariaOut(ImobiliariaCreate):
    id: int
    class Config:
        from_attributes = True


# ── Imovel ────────────────────────────────────────────────────
class ImovelCreate(BaseModel):
    endereco: str = Field(..., example="Asa Norte, Bloco A, Ap 101 - Plano Piloto, DF")
    tamanho_m2: Optional[float] = Field(None, example=75.0)
    preco: float = Field(..., example=2500.00)
    quartos: Optional[int] = Field(None, example=2)
    vagas: Optional[int] = Field(None, example=1)
    suites: Optional[int] = Field(None, example=1)
    imobiliaria_id: Optional[int] = Field(None, example=1)
    tipo_operacao_id: int = Field(..., example=1)
    tipo_imovel_id: int = Field(..., example=1)

class ImovelOut(BaseModel):
    id: int
    endereco: str
    tamanho_m2: Optional[float]
    preco: float
    quartos: Optional[int]
    vagas: Optional[int]
    suites: Optional[int]
    data_coleta: Optional[datetime]
    imobiliaria: Optional[ImobiliariaOut]
    tipo_operacao: TipoOperacaoOut
    tipo_imovel: TipoImovelOut
    class Config:
        from_attributes = True


# ── Resumo ────────────────────────────────────────────────────
class ImovelResumo(BaseModel):
    total_imoveis: int
    preco_medio_aluguel: Optional[float]
    preco_medio_venda: Optional[float]
    total_apartamentos: int
    total_casas: int
