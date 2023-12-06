FROM python:3.9.10-slim-bullseye as libs

RUN apt-get -y update \
    && apt-get -y install --no-install-recommends git gcc libc6-dev wget\
    && update-ca-certificates

RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.9.10-slim-bullseye

WORKDIR /app/saver

COPY --from=libs /usr/local /usr/local
COPY . .

CMD ["bash", "entrypoint.sh"]
