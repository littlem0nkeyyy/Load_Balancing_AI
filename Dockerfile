FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY AI/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy AI code and Model directory
COPY AI/ ./AI/
COPY Model/ ./Model/
COPY data.csv .

WORKDIR /app/AI

EXPOSE 5000

CMD ["python", "web_dashboard.py"]
