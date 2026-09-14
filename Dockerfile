FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 7860

CMD python -m mcp_servers.health_server & \
    python -m mcp_servers.finance_server & \
    python -m mcp_servers.productivity_server & \
    python -m app.api.main