FROM python:3.12-slim
 
WORKDIR /app
 
RUN pip install flask --no-cache-dir

COPY weather.py .
 
CMD ["python", "weather.py"]
 