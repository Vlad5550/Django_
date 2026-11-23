-- Rulează acest fișier din SQL Shell (psql), conectat la baza postgres
-- cu utilizatorul administrativ postgres. Nu îl rula din pgAdmin Query Tool,
-- deoarece comenzile \gexec și \connect sunt comenzi specifice psql.

-- Creează utilizatorul numai dacă nu există deja.
SELECT 'CREATE ROLE vlad WITH LOGIN PASSWORD ''vlad'''
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vlad') \gexec
ALTER ROLE vlad WITH LOGIN PASSWORD 'vlad';

-- CREATE DATABASE nu poate fi rulat într-o tranzacție, de aceea folosim \gexec.
SELECT 'CREATE DATABASE "2026" OWNER vlad'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '2026')
ALTER DATABASE "2026" OWNER TO vlad;

\connect "2026"

CREATE SCHEMA IF NOT EXISTS django AUTHORIZATION vlad;
ALTER SCHEMA django OWNER TO vlad;
GRANT ALL ON SCHEMA django TO vlad;
