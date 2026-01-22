-- config/schema.sql

-- Tabela de Dispositivos
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    protocol TEXT NOT NULL,
    token TEXT,
    config TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Histórico
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    payload TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Tabela de Roteamento de Mensagens
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,   -- Quem está enviando
    target_id TEXT NOT NULL,   -- Quem deve receber
    enabled BOOLEAN DEFAULT 1, -- Para ligar/desligar a rota sem deletar
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Impede rotas duplicadas
    UNIQUE(source_id, target_id)
    FOREIGN KEY(source_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY(target_id) REFERENCES devices(id) ON DELETE CASCADE
);