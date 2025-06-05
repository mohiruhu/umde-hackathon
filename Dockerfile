# Use a slim Python base image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy only requirements first (for cache efficiency)
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the full backend directory
COPY backend ./backend

# Expose port (Render automatically uses PORT env)
ENV PORT=8000
EXPOSE $PORT

# Set PYTHONPATH so backend.app.* works
ENV PYTHONPATH=backend

# Start the app
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
