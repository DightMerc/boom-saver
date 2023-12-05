FROM python:3.9.10-slim-bullseye as libs

RUN apt-get -y update \
    && apt-get -y install --no-install-recommends git gcc libc6-dev \
    && update-ca-certificates

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.9.10-slim-bullseye

WORKDIR /app/saver

COPY --from=libs /usr/local /usr/local
COPY . .

CMD ["bash", "entrypoint.sh"]
