# PROD 2 Stage

## Prerequisites

Ensure you have the following installed on your system:

- [Python](https://www.python.org/) (>=3.10,<3.12)
- [uv](https://docs.astral.sh/uv/)
- [Docker](https://www.docker.com/) (for containerized setup)

## Basic setup

### Installation

#### Clone the project

```bash
git clone https://github.com/Central-University-IT/test-2025-python-devitq
```

#### Go to the project directory

```bash
cd test-2025-python-devitq/solution
```

#### Customize environment

```bash
cp .env.template .env
```

And setup env vars according to your needs.

#### Install dependencies

##### For dev environment

```bash
uv sync --all-extras
```

##### For prod environment

```bash
uv sync --no-dev
```

#### Running

##### In dev mode

Apply migrations:

```bash
uv run python manage.py migrate
```

Start project:

```bash
uv run python manage.py runserver
```

##### In prod mode

Apply migrations:

```bash
uv run python manage.py migrate
```

Start project:

```bash
uv run gunicorn config.wsgi
```

## Containerized setup

### Clone the project

```bash
git clone https://github.com/Central-University-IT/test-2025-python-devitq
```

### Go to the project directory

```bash
cd test-2025-python-devitq/solution
```

### Build docker image

```bash
docker build -t prod-2-devitq .
```

### Customize environment

Customize environment with `docker run` command (or bind .env file to container), for all environment vars and default values see [.env.template](./.env.template).

### Run docker image

```bash
docker run -p 8080:8080 --name prod-2-devitq prod-2-devitq
```

Backend will be available on localhost:8080.
