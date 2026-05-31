FROM python:3.12-slim

WORKDIR /app

COPY Catalog_search_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Catalog_search_agent/ .

CMD ["python", "catalog_search_agent_mock.py"]
