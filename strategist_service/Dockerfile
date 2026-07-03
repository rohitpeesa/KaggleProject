FROM python:3.11-slim

WORKDIR /app

# Ensure we have the base requirements and FastAPI/Uvicorn
COPY ../requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
RUN pip install fastapi uvicorn python-dotenv

# Copy project root and strategist_service
COPY ../ /app/

# Set working directory to the service
WORKDIR /app/strategist_service

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
