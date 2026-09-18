-- ============================================================
-- Aurora Fibra: base de aula. Todos os dados são fictícios.
-- ============================================================

CREATE TABLE clientes (
    id              SERIAL PRIMARY KEY,
    cpf             VARCHAR(11) UNIQUE NOT NULL,
    nome            VARCHAR(120) NOT NULL,
    email           VARCHAR(120),
    telefone        VARCHAR(20),
    cidade          VARCHAR(80),
    uf              CHAR(2),
    cep             VARCHAR(9),
    cliente_desde   DATE NOT NULL
);

CREATE TABLE contratos (
    id              SERIAL PRIMARY KEY,
    cliente_id      INT NOT NULL REFERENCES clientes(id),
    plano           VARCHAR(60) NOT NULL,
    velocidade_mbps INT NOT NULL,
    mensalidade     NUMERIC(10,2) NOT NULL,
    tecnologia      VARCHAR(20) NOT NULL,   -- 'fibra_legado' ou 'nova_fibra'
    status          VARCHAR(20) NOT NULL,   -- 'ativo', 'suspenso', 'cancelado'
    dia_vencimento  INT NOT NULL
);

CREATE TABLE faturas (
    id              SERIAL PRIMARY KEY,
    contrato_id     INT NOT NULL REFERENCES contratos(id),
    competencia     VARCHAR(7) NOT NULL,    -- 'AAAA-MM'
    valor           NUMERIC(10,2) NOT NULL,
    vencimento      DATE NOT NULL,
    pagamento       DATE,
    status          VARCHAR(20) NOT NULL    -- 'paga', 'aberta', 'vencida'
);

CREATE TABLE chamados (
    id              SERIAL PRIMARY KEY,
    cliente_id      INT NOT NULL REFERENCES clientes(id),
    abertura        TIMESTAMP NOT NULL,
    fechamento      TIMESTAMP,
    categoria       VARCHAR(40) NOT NULL,   -- 'lentidao', 'sem_conexao', 'cobranca', 'instalacao'
    descricao       TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL,   -- 'aberto', 'em_andamento', 'resolvido'
    tecnico         VARCHAR(80)
);

CREATE TABLE agenda_tecnica (
    id              SERIAL PRIMARY KEY,
    chamado_id      INT REFERENCES chamados(id),
    data_visita     DATE NOT NULL,
    turno           VARCHAR(10) NOT NULL,   -- 'manha' ou 'tarde'
    tecnico         VARCHAR(80) NOT NULL,
    status          VARCHAR(20) NOT NULL    -- 'agendada', 'realizada', 'cancelada'
);

CREATE INDEX idx_clientes_cpf ON clientes(cpf);
CREATE INDEX idx_contratos_cliente ON contratos(cliente_id);
CREATE INDEX idx_faturas_contrato ON faturas(contrato_id);
CREATE INDEX idx_chamados_cliente ON chamados(cliente_id);

-- ------------------------------------------------------------
-- Clientes
-- ------------------------------------------------------------
INSERT INTO clientes (cpf, nome, email, telefone, cidade, uf, cep, cliente_desde) VALUES
('11122233344', 'Marcela Tavares Pinto',  'marcela.tavares@exemplo.com.br', '11987650001', 'Osasco',        'SP', '06010-100', '2019-03-14'),
('22233344455', 'Rogério Santana Lima',   'rogerio.lima@exemplo.com.br',    '11987650002', 'Carapicuíba',   'SP', '06320-250', '2021-08-02'),
('33344455566', 'Ana Beatriz Nogueira',   'ana.nogueira@exemplo.com.br',    '11987650003', 'Barueri',       'SP', '06455-030', '2023-01-20'),
('44455566677', 'Wellington Farias Cruz', 'well.cruz@exemplo.com.br',       '11987650004', 'Osasco',        'SP', '06018-090', '2017-06-11'),
('55566677788', 'Cláudia Mendes Rocha',   'claudia.rocha@exemplo.com.br',   '11987650005', 'Santana de Parnaíba', 'SP', '06501-010', '2024-11-05'),
('66677788899', 'Itamar Gonçalves Reis',  'itamar.reis@exemplo.com.br',     '11987650006', 'Cotia',         'SP', '06700-000', '2020-02-28'),
('77788899900', 'Priscila Amaral Duarte', 'pri.duarte@exemplo.com.br',      '11987650007', 'Osasco',        'SP', '06110-045', '2022-09-17'),
('88899900011', 'Nelson Batista Freire',  'nelson.freire@exemplo.com.br',   '11987650008', 'Jandira',       'SP', '06600-100', '2018-12-01');

-- ------------------------------------------------------------
-- Contratos
-- ------------------------------------------------------------
INSERT INTO contratos (cliente_id, plano, velocidade_mbps, mensalidade, tecnologia, status, dia_vencimento) VALUES
(1, 'Aurora 600 Turbo',   600,  129.90, 'nova_fibra',   'ativo',    10),
(2, 'Aurora 300 Casa',    300,   89.90, 'fibra_legado', 'ativo',     5),
(3, 'Aurora 900 Gamer',   900,  179.90, 'nova_fibra',   'ativo',    20),
(4, 'Aurora 200 Básico',  200,   69.90, 'fibra_legado', 'suspenso', 15),
(5, 'Aurora 600 Turbo',   600,  129.90, 'nova_fibra',   'ativo',    25),
(6, 'Aurora 300 Casa',    300,   89.90, 'fibra_legado', 'ativo',    10),
(7, 'Aurora 900 Gamer',   900,  179.90, 'nova_fibra',   'ativo',     5),
(8, 'Aurora 200 Básico',  200,   69.90, 'fibra_legado', 'cancelado',15);

-- ------------------------------------------------------------
-- Faturas
-- ------------------------------------------------------------
INSERT INTO faturas (contrato_id, competencia, valor, vencimento, pagamento, status) VALUES
(1, '2026-06', 129.90, '2026-06-10', '2026-06-09', 'paga'),
(1, '2026-07', 129.90, '2026-07-10', '2026-07-10', 'paga'),
(1, '2026-08', 129.90, '2026-08-10', NULL,         'vencida'),
(2, '2026-07',  89.90, '2026-07-05', '2026-07-04', 'paga'),
(2, '2026-08',  89.90, '2026-08-05', '2026-08-05', 'paga'),
(2, '2026-09',  89.90, '2026-09-05', NULL,         'aberta'),
(3, '2026-08', 179.90, '2026-08-20', '2026-08-18', 'paga'),
(3, '2026-09', 179.90, '2026-09-20', NULL,         'aberta'),
(4, '2026-06',  69.90, '2026-06-15', NULL,         'vencida'),
(4, '2026-07',  69.90, '2026-07-15', NULL,         'vencida'),
(4, '2026-08',  69.90, '2026-08-15', NULL,         'vencida'),
(5, '2026-08', 129.90, '2026-08-25', '2026-08-25', 'paga'),
(6, '2026-08',  89.90, '2026-08-10', '2026-08-12', 'paga'),
(7, '2026-09', 179.90, '2026-09-05', NULL,         'aberta');

-- ------------------------------------------------------------
-- Chamados
-- ------------------------------------------------------------
INSERT INTO chamados (cliente_id, abertura, fechamento, categoria, descricao, status, tecnico) VALUES
(1, '2026-09-01 09:12:00', '2026-09-01 11:40:00', 'lentidao',    'Velocidade abaixo do contratado no período da noite.', 'resolvido', 'Equipe N2 Osasco'),
(1, '2026-09-12 20:05:00', NULL,                  'lentidao',    'Cliente relata oscilação em streaming após 20h.',       'aberto',    NULL),
(2, '2026-08-22 14:30:00', '2026-08-23 10:15:00', 'sem_conexao', 'Queda total após temporal na região.',                 'resolvido', 'Equipe N2 Carapicuíba'),
(3, '2026-09-10 19:44:00', NULL,                  'lentidao',    'Ping alto em jogos online, roteador piscando vermelho.','em_andamento','Equipe N2 Barueri'),
(4, '2026-07-19 08:00:00', '2026-07-19 09:30:00', 'cobranca',    'Contesta valor da fatura de junho.',                   'resolvido', NULL),
(7, '2026-09-13 07:55:00', NULL,                  'sem_conexao', 'Sem sinal desde a madrugada, luz LOS acesa.',          'aberto',    NULL);

-- ------------------------------------------------------------
-- Agenda técnica
-- ------------------------------------------------------------
INSERT INTO agenda_tecnica (chamado_id, data_visita, turno, tecnico, status) VALUES
(4, '2026-09-16', 'manha', 'Douglas Peixoto', 'agendada'),
(6, '2026-09-15', 'tarde', 'Sueli Aparecida Ramos', 'agendada'),
(3, '2026-08-23', 'manha', 'Douglas Peixoto', 'realizada');
