FROM python:3.11-slim

WORKDIR /app

# Install all deps from bundled wheels — no PyPI access needed
COPY wheels/ /wheels/
RUN pip install --no-cache-dir --no-index --find-links=/wheels \
    fastapi "uvicorn[standard]" numpy onnxruntime tokenizers \
    && rm -rf /wheels

# Bake model into image — no runtime download needed
COPY model/ ./model/

COPY main.py .

ENV MODEL_DIR=/app/model

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
