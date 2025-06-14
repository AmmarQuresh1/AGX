FROM python:3.11-slim

WORKDIR /app

# 1. Copy only the requirements file first and install dependencies.
# This makes builds much faster by using Docker's cache.
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip -r ./requirements.txt

# 2. Now, copy your application code.
COPY ./agx_backend ./agx_backend
COPY ./agx ./agx

EXPOSE 8080

# 3. Tell uvicorn the correct path to your FastAPI app object.
CMD ["uvicorn", "agx_backend.app:app", "--host", "0.0.0.0", "--port", "8080"]