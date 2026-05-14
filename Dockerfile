FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY pyproject.toml .
COPY README.md .
RUN pip install --no-cache-dir -e .

EXPOSE 3000

LABEL io.modelcontextprotocol.server.name="io.github.kcofoni/duplicati-mcp"

ENV MCP_TRANSPORT=streamable-http
ENV FASTMCP_HOST=0.0.0.0
ENV FASTMCP_PORT=3000
ENV DUPLICATI_URL=http://duplicati:8200
ENV DUPLICATI_READONLY=false
# DUPLICATI_DB_PATH is intentionally unset — SQLite access is opt-in.
# Set it to the path of Duplicati-server.sqlite inside the container, e.g.:
# ENV DUPLICATI_DB_PATH=/duplicati-config/Duplicati-server.sqlite

CMD ["duplicati-mcp"]
