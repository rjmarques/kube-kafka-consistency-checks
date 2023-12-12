FROM python:3.12-slim-bookworm

WORKDIR /app

ARG TARGET

COPY requirements.txt .
COPY src/${TARGET}/ ${TARGET}

RUN pip install -r requirements.txt

ENV TARGET=$TARGET

CMD ["/bin/bash", "-c", "python -m $TARGET"]