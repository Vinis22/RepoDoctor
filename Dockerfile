FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY repodoctor ./repodoctor
RUN pip install --no-cache-dir .

WORKDIR /workspace

EXPOSE 8000

ENTRYPOINT ["repocheckup"]
CMD ["."]
