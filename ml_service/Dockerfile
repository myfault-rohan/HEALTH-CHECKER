FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY ml_service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy ML models from main folder
COPY model/ /app/model/

# Copy the FastAPI app code
COPY ml_service/main.py /app/main.py

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
