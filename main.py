from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import models, schemas
from database import engine, get_db, Base

# Cria as tabelas no banco se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DFImóveis API",
    description="API para cadastro e consulta de imóveis no Distrito Federal - Plano Piloto",
    version="1.0.0",
)


# ══════════════════════════════════════════════════════════════
#  TIPO OPERAÇÃO
# ══════════════════════════════════════════════════════════════

@app.post("/tipo-operacao", response_model=schemas.TipoOperacaoOut, tags=["Tipo Operação"])
def criar_tipo_operacao(payload: schemas.TipoOperacaoCreate, db: Session = Depends(get_db)):
    """Cadastra um tipo de operação (ALUGUEL ou VENDA)."""
    existente = db.query(models.TipoOperacao).filter(
        models.TipoOperacao.nome_operacao == payload.nome_operacao.upper()
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Tipo de operação já cadastrado.")
    obj = models.TipoOperacao(nome_operacao=payload.nome_operacao.upper())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/tipo-operacao", response_model=List[schemas.TipoOperacaoOut], tags=["Tipo Operação"])
def listar_tipo_operacao(db: Session = Depends(get_db)):
    return db.query(models.TipoOperacao).all()


# ══════════════════════════════════════════════════════════════
#  TIPO IMÓVEL
# ══════════════════════════════════════════════════════════════

@app.post("/tipo-imovel", response_model=schemas.TipoImovelOut, tags=["Tipo Imóvel"])
def criar_tipo_imovel(payload: schemas.TipoImovelCreate, db: Session = Depends(get_db)):
    """Cadastra um tipo de imóvel (APARTAMENTO ou CASA)."""
    existente = db.query(models.TipoImovel).filter(
        models.TipoImovel.nome_tipo_imovel == payload.nome_tipo_imovel.upper()
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Tipo de imóvel já cadastrado.")
    obj = models.TipoImovel(nome_tipo_imovel=payload.nome_tipo_imovel.upper())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/tipo-imovel", response_model=List[schemas.TipoImovelOut], tags=["Tipo Imóvel"])
def listar_tipo_imovel(db: Session = Depends(get_db)):
    return db.query(models.TipoImovel).all()


# ══════════════════════════════════════════════════════════════
#  IMOBILIÁRIA
# ══════════════════════════════════════════════════════════════

@app.post("/imobiliaria", response_model=schemas.ImobiliariaOut, tags=["Imobiliária"])
def criar_imobiliaria(payload: schemas.ImobiliariaCreate, db: Session = Depends(get_db)):
    """Cadastra uma imobiliária."""
    obj = models.Imobiliaria(
        nome_imobiliaria=payload.nome_imobiliaria,
        creci=payload.creci,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/imobiliaria", response_model=List[schemas.ImobiliariaOut], tags=["Imobiliária"])
def listar_imobiliarias(db: Session = Depends(get_db)):
    return db.query(models.Imobiliaria).all()


# ══════════════════════════════════════════════════════════════
#  IMÓVEIS  (endpoint principal — inserção via Postman)
# ══════════════════════════════════════════════════════════════

@app.post("/imoveis", response_model=schemas.ImovelOut, tags=["Imóveis"])
def cadastrar_imovel(payload: schemas.ImovelCreate, db: Session = Depends(get_db)):
    """
    Cadastra um imóvel no banco de dados.
    Use este endpoint no Postman para inserir imóveis manualmente.

    Campos obrigatórios: endereco, preco, tipo_operacao_id, tipo_imovel_id
    """
    # Valida FK tipo_operacao
    op = db.query(models.TipoOperacao).filter(models.TipoOperacao.id == payload.tipo_operacao_id).first()
    if not op:
        raise HTTPException(status_code=404, detail=f"tipo_operacao_id {payload.tipo_operacao_id} não encontrado.")

    # Valida FK tipo_imovel
    ti = db.query(models.TipoImovel).filter(models.TipoImovel.id == payload.tipo_imovel_id).first()
    if not ti:
        raise HTTPException(status_code=404, detail=f"tipo_imovel_id {payload.tipo_imovel_id} não encontrado.")

    # Valida FK imobiliaria (opcional)
    if payload.imobiliaria_id:
        imob = db.query(models.Imobiliaria).filter(models.Imobiliaria.id == payload.imobiliaria_id).first()
        if not imob:
            raise HTTPException(status_code=404, detail=f"imobiliaria_id {payload.imobiliaria_id} não encontrado.")

    imovel = models.Imovel(**payload.model_dump())
    db.add(imovel)
    db.commit()
    db.refresh(imovel)
    return imovel


@app.get("/imoveis", response_model=List[schemas.ImovelOut], tags=["Imóveis"])
def listar_imoveis(
    tipo_operacao_id: int = None,
    tipo_imovel_id: int = None,
    db: Session = Depends(get_db),
):
    """Lista todos os imóveis, com filtros opcionais por tipo de operação e tipo de imóvel."""
    query = db.query(models.Imovel)
    if tipo_operacao_id:
        query = query.filter(models.Imovel.tipo_operacao_id == tipo_operacao_id)
    if tipo_imovel_id:
        query = query.filter(models.Imovel.tipo_imovel_id == tipo_imovel_id)
    return query.all()


@app.get("/imoveis-resumo", response_model=schemas.ImovelResumo, tags=["Imóveis"])
def resumo_imoveis(db: Session = Depends(get_db)):
    """
    Retorna um resumo estatístico dos imóveis cadastrados.
    Endpoint principal para alimentar o dashboard Streamlit.
    """
    total = db.query(func.count(models.Imovel.id)).scalar()

    # IDs dos tipos de operação
    aluguel = db.query(models.TipoOperacao).filter(models.TipoOperacao.nome_operacao == "ALUGUEL").first()
    venda = db.query(models.TipoOperacao).filter(models.TipoOperacao.nome_operacao == "VENDA").first()

    preco_aluguel = None
    if aluguel:
        preco_aluguel = db.query(func.avg(models.Imovel.preco)).filter(
            models.Imovel.tipo_operacao_id == aluguel.id
        ).scalar()

    preco_venda = None
    if venda:
        preco_venda = db.query(func.avg(models.Imovel.preco)).filter(
            models.Imovel.tipo_operacao_id == venda.id
        ).scalar()

    # IDs dos tipos de imóvel
    apto = db.query(models.TipoImovel).filter(models.TipoImovel.nome_tipo_imovel == "APARTAMENTO").first()
    casa = db.query(models.TipoImovel).filter(models.TipoImovel.nome_tipo_imovel == "CASA").first()

    total_apto = db.query(func.count(models.Imovel.id)).filter(
        models.Imovel.tipo_imovel_id == apto.id
    ).scalar() if apto else 0

    total_casa = db.query(func.count(models.Imovel.id)).filter(
        models.Imovel.tipo_imovel_id == casa.id
    ).scalar() if casa else 0

    return schemas.ImovelResumo(
        total_imoveis=total,
        preco_medio_aluguel=round(preco_aluguel, 2) if preco_aluguel else None,
        preco_medio_venda=round(preco_venda, 2) if preco_venda else None,
        total_apartamentos=total_apto,
        total_casas=total_casa,
    )


@app.delete("/imoveis/{imovel_id}", tags=["Imóveis"])
def deletar_imovel(imovel_id: int, db: Session = Depends(get_db)):
    """Remove um imóvel pelo ID."""
    imovel = db.query(models.Imovel).filter(models.Imovel.id == imovel_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado.")
    db.delete(imovel)
    db.commit()
    return {"detail": f"Imóvel {imovel_id} removido com sucesso."}
