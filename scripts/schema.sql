-- 🎟️ Boletera Serverless — Schema y datos de prueba
-- Corre esto en tu RDS PostgreSQL antes del taller

-- =====================
-- TABLAS
-- =====================

CREATE TABLE IF NOT EXISTS eventos (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(200) NOT NULL,
    fecha       TIMESTAMP NOT NULL,
    venue       VARCHAR(200) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS asientos (
    id          SERIAL PRIMARY KEY,
    evento_id   INTEGER REFERENCES eventos(id),
    zona        VARCHAR(50) NOT NULL,       -- 'VIP', 'General', 'Palco'
    fila        VARCHAR(10) NOT NULL,       -- 'A', 'B', 'C'...
    numero      INTEGER NOT NULL,
    precio      DECIMAL(10,2) NOT NULL,
    estado      VARCHAR(20) DEFAULT 'disponible',  -- 'disponible', 'vendido', 'reservado'
    UNIQUE(evento_id, zona, fila, numero)
);

CREATE TABLE IF NOT EXISTS tickets (
    id                  SERIAL PRIMARY KEY,
    folio               VARCHAR(20) UNIQUE NOT NULL,
    evento_id           INTEGER REFERENCES eventos(id),
    asiento_id          INTEGER REFERENCES asientos(id),
    nombre_comprador    VARCHAR(200) NOT NULL,
    email               VARCHAR(200) NOT NULL,
    total               DECIMAL(10,2) NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- =====================
-- DATOS DE PRUEBA
-- =====================

-- Evento demo
INSERT INTO eventos (nombre, fecha, venue) VALUES
    ('Bad Bunny World Tour 2026', '2026-08-15 21:00:00', 'Foro Sol, Ciudad de México'),
    ('Coldplay Music of the Spheres', '2026-09-20 20:00:00', 'Estadio Azteca, CDMX');

-- Asientos para evento 1 (Bad Bunny)
-- Zona VIP: filas A-B, asientos 1-10
INSERT INTO asientos (evento_id, zona, fila, numero, precio)
SELECT 1, 'VIP', fila, numero, 4500.00
FROM (VALUES ('A'), ('B')) AS filas(fila)
CROSS JOIN generate_series(1, 10) AS numero;

-- Zona General: filas C-G, asientos 1-20
INSERT INTO asientos (evento_id, zona, fila, numero, precio)
SELECT 1, 'General', fila, numero, 1200.00
FROM (VALUES ('C'), ('D'), ('E'), ('F'), ('G')) AS filas(fila)
CROSS JOIN generate_series(1, 20) AS numero;

-- Zona Palco: fila P, asientos 1-5
INSERT INTO asientos (evento_id, zona, fila, numero, precio)
SELECT 1, 'Palco', 'P', numero, 8000.00
FROM generate_series(1, 5) AS numero;

-- Simular algunos asientos ya vendidos (para que la demo se vea real)
UPDATE asientos SET estado = 'vendido'
WHERE evento_id = 1 AND zona = 'VIP' AND numero IN (1, 2, 3);

UPDATE asientos SET estado = 'vendido'
WHERE evento_id = 1 AND zona = 'General' AND fila = 'C' AND numero IN (1, 2, 3, 4, 5);

-- =====================
-- VERIFICAR
-- =====================
SELECT
    zona,
    COUNT(*) FILTER (WHERE estado = 'disponible') AS disponibles,
    COUNT(*) FILTER (WHERE estado = 'vendido') AS vendidos,
    MIN(precio) AS precio
FROM asientos
WHERE evento_id = 1
GROUP BY zona
ORDER BY zona;
