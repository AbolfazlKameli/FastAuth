ARG PYTHON_VERSION=3.13.5

FROM docker.arvancloud.ir/python:${PYTHON_VERSION}-alpine

LABEL maintainer="abolfazlkameli0@gmail.com"

ENV PYTHONBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /usr/src/fastauth/

COPY Pipfile Pipfile.lock /usr/src/fastauth/

RUN pip install --no-cache-dir pipenv && PIPENV_VENV_IN_PROJECT=0 pipenv install --deploy --system && \
    apk add curl

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    app

COPY . /usr/src/fastauth/
RUN mkdir -p /usr/src/fastauth/logs/app && \
    chown -R app:app /usr/src/fastauth && \
    chmod 755 /usr/src/fastauth/logs && \
    chmod +x /usr/src/fastauth/entrypoint.sh

USER app
ENTRYPOINT ["sh", "-c", "/usr/src/fastauth/entrypoint.sh"]
