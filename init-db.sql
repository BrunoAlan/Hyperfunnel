-- Habilitar extensión uuid-ossp para generar UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verificar que la extensión está habilitada
SELECT * FROM pg_extension WHERE extname = 'uuid-ossp';
