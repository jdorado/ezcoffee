FROM python:3.12-slim
WORKDIR /app
COPY coffee_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY coffee_api/src /app/coffee_api/src
WORKDIR /app/coffee_api
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
