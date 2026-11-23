-- LAB 3, TASK 2: rulați în pgAdmin, conectat la baza de date postgres,
-- cu un cont administrator. CREATE DATABASE trebuie executat în afara unei tranzacții.
CREATE USER atelier_user WITH PASSWORD '2026';
CREATE DATABASE atelier_ciocolata OWNER vlad;
GRANT ALL PRIVILEGES ON DATABASE atelier_ciocolata TO vlad;
