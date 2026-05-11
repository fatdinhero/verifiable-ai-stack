FROM python:3.11-slim

WORKDIR /app

COPY wheels/ /wheels/
RUN pip install --no-cache-dir --no-index --find-links=/wheels \
    fastapi uvicorn[standard] pydantic numpy scipy cryptography \
    && rm -rf /wheels

COPY agentsprotocol_pkg ./agentsprotocol
COPY api.py .

EXPOSE 8080

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
