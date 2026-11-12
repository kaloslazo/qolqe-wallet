# imagen de qolqe para las pruebas de rendimiento
# se construye desde la raiz del repo:
#   docker build -f tests/performance/Dockerfile -t qolqe-perf .
FROM python:3.12-slim
WORKDIR /app
# hora de lima para cruzar el csv de recursos con los resultados de k6
ENV TZ=America/Lima
COPY requirements.txt .
# mismo pin de fastapi que el ci; psutil para medir cpu y memoria desde adentro
RUN pip install --no-cache-dir -r requirements.txt "fastapi<0.118" psutil
COPY qolqe ./qolqe
EXPOSE 8000
CMD ["uvicorn", "qolqe.main:app", "--host", "0.0.0.0", "--port", "8000"]
