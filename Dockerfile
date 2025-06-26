FROM newrelic/infrastructure-bundle:latest

# Create a non-root user
RUN adduser -D -u 1000 nri-solace

# Install necessary tools
RUN apk add --no-cache curl python3 py3-pip ca-certificates \
    && update-ca-certificates

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Copy requirements file and install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# Copy configurations
COPY config/solace-flex-config.yml /etc/newrelic-infra/integrations.d/
COPY config/newrelic-infra.yml /etc/newrelic-infra.yml

# Copy and setup entrypoint
COPY src/entrypoint.py /usr/bin/
RUN chmod +x /usr/bin/entrypoint.py

# Set working directory
WORKDIR /var/db/newrelic-infra/newrelic-integrations

# Set the virtual environment as the default Python environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Switch to non-root user
USER nri-solace

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD newrelic-infra diagnose || exit 1

CMD ["newrelic-infra"]
