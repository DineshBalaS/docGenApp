# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only requirements first (for better layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Expose port
EXPOSE 6900

# Set environment (optional)
ENV FLASK_ENV=production

# Run the Flask app
CMD ["python", "app.py"]
