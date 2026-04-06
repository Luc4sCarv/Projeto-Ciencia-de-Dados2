from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class TipoOperacao(Base):
    __tablename__ = "tipo_operacao"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_operacao = Column(String(50), nullable=False, unique=True)  # ALUGUEL | VENDA

    imoveis = relationship("Imovel", back_populates="tipo_operacao")


class TipoImovel(Base):
    __tablename__ = "tipo_imovel"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_tipo_imovel = Column(String(50), nullable=False, unique=True)  # APARTAMENTO | CASA

    imoveis = relationship("Imovel", back_populates="tipo_imovel")


class Imobiliaria(Base):
    __tablename__ = "imobiliaria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creci = Column(String(50), nullable=True)
    nome_imobiliaria = Column(String(150), nullable=False)

    imoveis = relationship("Imovel", back_populates="imobiliaria")


class Imovel(Base):
    __tablename__ = "imoveis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endereco = Column(String(255), nullable=False)
    tamanho_m2 = Column(Float, nullable=True)
    preco = Column(Float, nullable=False)
    quartos = Column(Integer, nullable=True)
    vagas = Column(Integer, nullable=True)
    suites = Column(Integer, nullable=True)
    data_coleta = Column(DateTime, server_default=func.now())

    # Chaves estrangeiras
    imobiliaria_id = Column(Integer, ForeignKey("imobiliaria.id"), nullable=True)
    tipo_operacao_id = Column(Integer, ForeignKey("tipo_operacao.id"), nullable=False)
    tipo_imovel_id = Column(Integer, ForeignKey("tipo_imovel.id"), nullable=False)

    # Relacionamentos
    imobiliaria = relationship("Imobiliaria", back_populates="imoveis")
    tipo_operacao = relationship("TipoOperacao", back_populates="imoveis")
    tipo_imovel = relationship("TipoImovel", back_populates="imoveis")
