# rare-api

Django REST API backed by PostgreSQL.

## Prerequisites

- Python
- [pipenv](https://pipenv.pypa.io/en/latest/)
- Docker (for the database)

## Setup

1. Start the PostgreSQL database:
   ```bash
   docker-compose up -d
   ```

2. Install dependencies:
   ```bash
   pipenv install
   ```

3. Run migrations:
   ```bash
   pipenv run python manage.py migrate
   ```

4. Start the dev server:
   ```bash
   pipenv run python manage.py runserver
   ```

The API will be available at http://localhost:8000.
