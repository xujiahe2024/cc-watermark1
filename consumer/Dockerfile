FROM python:3.9

RUN mkdir output
WORKDIR /app

RUN mkdir output

COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

COPY app/ app/
RUN mkdir app/output

CMD ["python", "app/main.py"]