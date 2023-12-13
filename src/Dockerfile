FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source=https://github.com/rjmarques/kube-kafka-consistency-checks
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /app

ARG TARGET

COPY requirements.txt .
COPY src/${TARGET}/ ${TARGET}

RUN pip install -r requirements.txt

ENV TARGET=$TARGET

CMD ["/bin/bash", "-c", "python -m $TARGET"]