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