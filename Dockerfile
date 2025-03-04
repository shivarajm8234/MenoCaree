FROM python:3.9-slim

WORKDIR /app

# Install system dependencies, including wkhtmltopdf for PDF generation
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variable to indicate this is a production environment
ENV DEPLOYMENT_ENV=production

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
