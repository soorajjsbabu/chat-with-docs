# Use official Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (Docker caches this layer)
# So if requirements don't change, it won't reinstall every time
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project code
COPY src/ ./src/
COPY api/ ./api/

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run when container starts
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]