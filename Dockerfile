FROM python:3.9.10-slim-bullseye as libs

RUN apt-get -y update \
    && apt-get -y install --no-install-recommends git gcc libc6-dev \
    && update-ca-certificates

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.9.10-slim-bullseye

RUN useradd -d /app -u 1122 app \
    && mkdir -p /app/saver \
    && chown app: /app/saver \
    && mkdir -p /app/saver/temp \
    && chown app: /app/saver/temp

WORKDIR /app/saver

COPY --from=libs /usr/local /usr/local
COPY . .

USER app

CMD ["bash", "entrypoint.sh"]
