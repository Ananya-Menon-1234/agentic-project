FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY mcp_servers/ ./mcp_servers/
COPY data/ ./data/

EXPOSE 8000
EXPOSE 8001
EXPOSE 8002
EXPOSE 8080

CMD ["sh", "-c", "python -m mcp_servers.health_server & python -m mcp_servers.finance_server & python -m mcp_servers.productivity_server & python -m app.api.main"]