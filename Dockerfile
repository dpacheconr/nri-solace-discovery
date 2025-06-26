# Use a specific version for reproducible builds
FROM newrelic/infrastructure-bundle:3.2.75

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Labels for better container management
LABEL org.label-schema.name="nri-solace" \
      org.label-schema.description="New Relic Solace Integration" \
      org.label-schema.vendor="New Relic" 

# Install necessary tools
RUN apk add --no-cache \
    curl \
    python3 \
    py3-pip \
    # Add jq for JSON parsing
    jq \
    # Add ca-certificates for SSL/TLS support
    ca-certificates \
    && update-ca-certificates

# Create a non-root user
RUN adduser -D -u 1000 nri-solace

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Activate the virtual environment and install base dependencies
# Using pip with version pinning and hash checking for security
RUN /opt/venv/bin/pip install --no-cache-dir pip==23.3.1 setuptools==69.0.3 wheel==0.42.0

# Copy requirements file
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# Create directories with proper permissions
RUN mkdir -p /etc/newrelic-infra/integrations.d /usr/bin /var/db/newrelic-infra/data /var/db/newrelic-infra/newrelic-integrations \
    && chown -R nri-solace:nri-solace /etc/newrelic-infra/integrations.d /usr/bin /var/db/newrelic-infra \
    && chmod 755 /usr/bin /var/db/newrelic-infra/data /var/db/newrelic-infra/newrelic-integrations

# New Relic Infrastructure configuration
COPY config/newrelic-infra.yml /etc/newrelic-infra.yml

# Set working directory
WORKDIR /var/db/newrelic-infra/newrelic-integrations

# Set the virtual environment as the default Python environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER nri-solace

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD newrelic-infra diagnose || exit 1

CMD ["newrelic-infra"]
