-- config/schema.sql

-- Tabela de Dispositivos
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    protocol TEXT NOT NULL,
    token TEXT,
    config TEXT,
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

-- Tabela de Estado Atual dos Dispositivos
CREATE TABLE IF NOT EXISTS device_states (
    device_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    attributes TEXT,
    last_changed DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- Tabela de Roteamento de Mensagens
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(source_id, target_id),
    FOREIGN KEY(source_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY(target_id) REFERENCES devices(id) ON DELETE CASCADE
);