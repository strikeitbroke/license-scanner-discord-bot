FROM python:3.13-slim AS build

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.8.21 /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN uv sync --locked

RUN chmod +x ./entrypoint.sh

CMD ["./entrypoint.sh"]
