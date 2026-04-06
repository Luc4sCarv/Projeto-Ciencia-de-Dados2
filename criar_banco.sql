-- ============================================================
--  DB_DFImoveis — Script de criação e dados iniciais
--  Execute no MySQL Workbench antes de rodar a API
-- ============================================================

CREATE DATABASE IF NOT EXISTS DB_DFImoveis
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE DB_DFImoveis;

-- ── Tipo de Operação ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tipo_operacao (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    nome_operacao  VARCHAR(50) NOT NULL UNIQUE
);

-- ── Tipo de Imóvel ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tipo_imovel (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    nome_tipo_imovel VARCHAR(50) NOT NULL UNIQUE
);

-- ── Imobiliária ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS imobiliaria (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    creci            VARCHAR(50),
    nome_imobiliaria VARCHAR(150) NOT NULL
);

-- ── Imóveis ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS imoveis (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    endereco          VARCHAR(255) NOT NULL,
    tamanho_m2        FLOAT,
    preco             FLOAT        NOT NULL,
    quartos           INT,
    vagas             INT,
    suites            INT,
    data_coleta       DATETIME DEFAULT CURRENT_TIMESTAMP,
    imobiliaria_id    INT,
    tipo_operacao_id  INT NOT NULL,
    tipo_imovel_id    INT NOT NULL,
    FOREIGN KEY (imobiliaria_id)   REFERENCES imobiliaria(id),
    FOREIGN KEY (tipo_operacao_id) REFERENCES tipo_operacao(id),
    FOREIGN KEY (tipo_imovel_id)   REFERENCES tipo_imovel(id)
);

-- ── Dados iniciais ───────────────────────────────────────────
INSERT IGNORE INTO tipo_operacao (nome_operacao) VALUES ('ALUGUEL'), ('VENDA');
INSERT IGNORE INTO tipo_imovel (nome_tipo_imovel) VALUES ('APARTAMENTO'), ('CASA');
