# New Relic Solace Integration

This integration collects metrics from Solace PubSub+ Event Brokers using New Relic's infrastructure agent and Flex integration framework.

## Features

- **Automatic Resource Discovery**: Automatically discovers VPNs, queues, topic endpoints, bridges, and clients
- **Comprehensive Metrics**: Collects detailed metrics for all Solace resources
- **Memory-Efficient**: Uses in-memory variables for resource discovery
- **Error Handling**: Robust error handling with detailed logging
- **Pre-built Dashboard**: Includes a ready-to-import dashboard for Solace monitoring
- **SSL Support**: Supports secure connections to Solace brokers
- **Docker Support**: Easy deployment using Docker and docker-compose
- **Consistent Metric Naming**: All metrics use consistent lowercase names and attributes
- **Automatic Type Detection**: Automatically detects and preserves numeric types for metrics

## Prerequisites

- A New Relic account. You can create a free account at [newrelic.com/signup](https://newrelic.com/signup)
- A Solace PubSub+ Event Broker (cloud or self-hosted)
- An environment with:
  - Python 3.6 or higher
  - Docker (for containerized deployment)

## Getting Started

### 1. Configure New Relic Infrastructure Agent

Copy the example New Relic Infrastructure configuration:

```bash
cp config/newrelic-infra.example.yml config/newrelic-infra.yml
```

Update `config/newrelic-infra.yml` with your New Relic license key:

```yaml
license_key: YOUR_LICENSE_KEY
```

### 2. Configure Solace Connection

Copy the example Solace environment configuration:

```bash
cp config/solace-env-config.example.yml config/solace-env-config.yml
```

Update `config/solace-env-config.yml` with your Solace PubSub+ connection details:

```yaml
SOLACE_BASE_URL: "https://your-solace-broker.example.com:943/SEMP/v2/monitor"
SOLACE_USERNAME: "admin"
SOLACE_PASSWORD: "password"
# Python path - default is python3 for Linux host, /opt/venv/bin/python3 for Docker
PYTHON_PATH: "python3"
# Logging configuration
SOLACE_LOG_DIRECTORY: "/var/log/newrelic-solace"  # Directory for log files
SOLACE_LOG_LEVEL: "INFO"  # Can be DEBUG, INFO, WARNING, ERROR, or CRITICAL
```

> Note: While you can specify a specific VPN and queue (`SOLACE_MSG_VPN` and `SOLACE_QUEUE_NAME`), the integration will automatically discover all VPNs, queues, and topic endpoints.

### 3. Deploy the Integration

#### Using Docker

Build and run the Docker container:

```bash
docker-compose up -d
```

#### Manual Installation

1. Copy the configuration files to the appropriate directories:

```bash
# Create required directories
sudo mkdir -p /etc/newrelic-infra/integrations.d

# Copy configuration files
sudo cp config/solace-flex-config.yml /etc/newrelic-infra/integrations.d/
sudo cp config/solace-env-config.yml /usr/bin/
sudo cp config/newrelic-infra.yml /etc/newrelic-infra/
sudo cp src/entrypoint.py /usr/bin/
sudo chmod +x /usr/bin/entrypoint.py
```

2. Restart the New Relic infrastructure agent:

```bash
sudo systemctl restart newrelic-infra
```

Alternatively, you can use the provided update script:

```bash
sudo ./update-integration.sh
```

## How It Works

The integration collects Solace metrics through the following steps:

1. **Discovery**: Automatically discovers all message VPNs on your Solace instance
2. **Resource Enumeration**: For each VPN, finds all queues and topic endpoints
3. **In-Memory Storage**: Stores discovered resources in memory using variables with TTL values
4. **Metrics Collection**: Collects detailed metrics for each resource:
   - Queue statistics
   - Topic endpoint statistics
   - VPN-level metrics
   - Bridge statistics
   - Client connection statistics

## Data Format and Naming Conventions

### Metric Naming

- All metric names and attributes are in lowercase for consistency
- VPN names are consistently referenced as `vpnname` across all metrics
- Numeric metrics (counts, rates, usage) are automatically preserved as numeric types
- Queue names are referenced as `queuename`
- Topic endpoint names are referenced as `topicendpointname`
- Bridge names are referenced as `bridgename`

### Available Event Types

- `SolaceVPNSummary`: VPN-level summary metrics
- `SolaceQueueSummary`: Queue discovery and basic info
- `SolaceQueueStats`: Detailed queue metrics
- `SolaceVPNDetailedMetrics`: Detailed VPN metrics
- `SolaceTopicEndpointMetrics`: Topic endpoint metrics
- `SolaceBridgeMetrics`: Bridge metrics
- `SolaceClientMetrics`: Client connection metrics

### Metric Types

The integration automatically preserves numeric types for metrics including:
- Message counts (e.g., `rxmsgcount`, `txmsgcount`)
- Byte counts (e.g., `datarxbytecount`, `datatxbytecount`)
- Usage metrics (e.g., `msgspoolusagebytecount`)
- Rates and limits
- Timestamps and durations

## Dashboard

Two dashboard templates are included:
- `dashboards/solace-dashboard.json`: The stable, production-ready dashboard
- `dashboards/solace-dashboard-wip.json`: Work-in-progress dashboard with latest improvements

Both dashboards provide comprehensive visualization of:
1. All discovered VPNs
2. Queue metrics and statistics
3. Topic endpoint metrics
4. Bridge and client connection information

To import the dashboard:
1. Go to New Relic One
2. Navigate to Dashboards
3. Click "Import dashboard"
4. Upload the `dashboards/solace-dashboard.json` file

## Dashboard Setup

### 1. Configure Account ID

Before importing the dashboard, you need to update the New Relic account ID in the dashboard template:

1. Find your New Relic account ID:
   - Log in to New Relic One
   - Click on the account dropdown in the top right
   - Your account ID will be displayed next to your account name

2. Replace the placeholder account ID in `dashboards/solace-dashboard.json`:
   ```bash
   # On macOS/Linux
   sed -i '' 's/3333333/YOUR_ACCOUNT_ID/g' dashboards/solace-dashboard.json
   
   # On Linux
   sed -i 's/3333333/YOUR_ACCOUNT_ID/g' dashboards/solace-dashboard.json
   ```
   Replace `YOUR_ACCOUNT_ID` with your actual New Relic account ID.

### 2. Import the Dashboard

There are three ways to import the dashboard:

#### Option 1: Using New Relic UI
1. Go to New Relic One (https://one.newrelic.com)
2. Click on "Dashboards" in the top navigation
3. Click "Import dashboard" button
4. Click "Select file" and choose `dashboards/solace-dashboard.json`
5. Click "Import dashboard"

#### Option 2: Using New Relic API
```bash
curl -X POST 'https://api.newrelic.com/graphql' \
  -H 'Content-Type: application/json' \
  -H 'API-Key: YOUR_USER_KEY' \
  --data-binary '{
    "query": "mutation { dashboardCreate(accountId: YOUR_ACCOUNT_ID, dashboard: \"DASHBOARD_JSON\") { errors { description } } }"
  }'
```
Replace:
- `YOUR_USER_KEY` with your [User API key](https://one.newrelic.com/api-keys)
- `YOUR_ACCOUNT_ID` with your account ID
- `DASHBOARD_JSON` with the contents of `dashboards/solace-dashboard.json` (escaped as a JSON string)

#### Option 3: Using New Relic CLI
```bash
# Install New Relic CLI if you haven't already
curl -Ls https://download.newrelic.com/install/newrelic-cli/scripts/install.sh | bash

# Import the dashboard
newrelic dashboards create --accountId YOUR_ACCOUNT_ID --file dashboards/solace-dashboard.json
```

### 3. Dashboard Customization

After importing, you can customize the dashboard:

1. Click "..." in the top right of the dashboard
2. Select "Edit dashboard"
3. You can:
   - Add/remove widgets
   - Modify queries
   - Adjust layouts
   - Update thresholds
   - Customize variables

### 4. Available Widgets

The dashboard includes:

1. **Overview Page**
   - VPN Count
   - Total Queues
   - Total Topic Endpoints
   - VPNs by Message Count
   - VPNs by Connection Count

2. **VPN Metrics Page**
   - VPN Message Rate
   - VPN Connections
   - VPN Disk Usage

3. **Queue Metrics Page**
   - Top 10 Queues by Message Count
   - Top 10 Queues by Spool Usage
   - Queue Message Rate Over Time

4. **Topic Endpoint Metrics Page**
   - Top 10 Topic Endpoints by Message Count
   - Topic Endpoints by Spool Usage
   - Topic Endpoint Message Rate

5. **Bridges & Connectivity Page**
   - Bridge Status
   - Client Connections
   - Bridge Message Rate

### 5. Using Dashboard Variables

The dashboard includes a `solace_vpn` variable that allows filtering by VPN. To use it:

1. Click the filter icon in the top right
2. Select one or more VPNs
3. The dashboard will update to show data only for the selected VPNs

### 6. Troubleshooting

If you don't see data in the dashboard:
1. Verify the integration is running: `docker-compose logs nri_solace`
2. Check New Relic for data: 
   ```sql
   SELECT count(*) FROM SolaceVPNSummary SINCE 1 hour ago
   ```
3. Verify your account ID is correct in the dashboard JSON
4. Ensure all required permissions are set in New Relic

## Available Metrics

You can query the collected metrics in New Relic:

```sql
-- For VPN summary
FROM SolaceVPNSummary SELECT * 

-- For queue metrics
FROM SolaceQueueMetrics SELECT * 

-- For topic endpoint metrics
FROM SolaceTopicEndpointMetrics SELECT *

-- For bridge metrics
FROM SolaceBridgeMetrics SELECT *

-- For client metrics
FROM SolaceClientMetrics SELECT *
```

## Troubleshooting

- **No data appearing in New Relic?** Check your Solace connection details in `solace-env-config.yml`
- **Integration not starting?** Check your New Relic license key in `newrelic-infra.yml`
- **Missing metrics?** Run the container with debug logging: `docker-compose up -d nri_solace command: ["newrelic-infra", "-debug"]`

## License

This integration is licensed under [Apache 2.0](LICENSE).

## Contributing

We welcome contributions to improve this integration. Please feel free to submit pull requests.
SELECT * FROM SolaceQueueSample

-- For dynamic discovery:
SELECT * FROM SolaceQueueMetrics
```

#### Key Metrics Available with Dynamic Discovery

The dynamic discovery configuration collects several important metrics:

- **Queue metrics:**
  - `spooledMsgCount`: Number of messages in the queue
  - `msgSpoolUsage`: Spool usage in MB
  - `maxMsgSpoolUsage`: Maximum spool usage
  - `averageRxMsgRate`: Average receive message rate
  - `averageTxMsgRate`: Average transmit message rate
  - `rxMsgRate`: Current receive message rate
  - `txMsgRate`: Current transmit message rate

- **Sample NRQL queries:**

```sql
-- Monitor message counts across all queues
SELECT average(spooledMsgCount) FROM SolaceQueueMetrics FACET queueName, vpn TIMESERIES

-- Find queues with high spool usage
SELECT max(msgSpoolUsage) FROM SolaceQueueMetrics FACET queueName, vpn WHERE msgSpoolUsage > 0
```

<img width="1785" alt="Image" src="https://github.com/user-attachments/assets/5f3335d0-8923-4211-a6e7-944b575db4ca" />

#### Testing the integration locally

If you want to test the integration locally without using Docker, you can do so by running the following commands:

1. Navigate to the root of the repository
2. Run the following commands:

```bash
pip install -r requirements.txt
```

to install the required Python packages.

3. Run the following command:

```bash
python3 src/entrypoint.py {endpoint key} --config config/solace-env-config.yml
```

to run the integration against one of the Solace PubSub+ Event Broker endpoints.

Replace `{endpoint key}` with one of the following:

**Static monitoring commands:**
- `queue` - Get information about a specific queue
- `vpn` - Get information about a specific VPN
- `topicEndpoints` - Get information about topic endpoints

**Dynamic discovery commands:**
- `discover-vpns` - Discover all VPNs in the broker
- `discover-queues` - Discover all queues in a specific VPN
- `discover-all` - Discover all VPNs and all queues
- `queue-stats` - Get detailed statistics for a specific queue, including spooledMsgCount

**Examples:**

```bash
# Discover all VPNs
python3 /usr/bin/entrypoint.py discover-vpns

# Discover all queues in a specific VPN
python3 /usr/bin/entrypoint.py discover-queues --vpn your-vpn-name

# Get detailed queue statistics
python3 /usr/bin/entrypoint.py queue-stats --vpn your-vpn-name --queue your-queue-name

# Get all VPN statistics
python3 /usr/bin/entrypoint.py vpn-stats --vpn your-vpn-name
```

:grey_exclamation: **Note:** Make sure you have provided all the required configurations in the `solace-env-config.yml` file.

## Testing Solace API Endpoints with curl

You can manually test each Solace API endpoint using `curl` to ensure connectivity and correct output. Replace the variables in angle brackets (`<>`) with your actual values or use the values from your `solace-env-config.yml`.

### 1. Discover all VPNs

```bash
curl -u "<SOLACE_USERNAME>:<SOLACE_PASSWORD>" \
  -k "https://<SOLACE_HOST>:943/SEMP/v2/monitor/msgVpns"
```

### 2. Discover all queues in a VPN

```bash
curl -u "<SOLACE_USERNAME>:<SOLACE_PASSWORD>" \
  -k "https://<SOLACE_HOST>:943/SEMP/v2/monitor/msgVpns/<VPN_NAME>/queues"
```

### 3. Discover all topic endpoints in a VPN

```bash
curl -u "<SOLACE_USERNAME>:<SOLACE_PASSWORD>" \
  -k "https://<SOLACE_HOST>:943/SEMP/v2/monitor/msgVpns/<VPN_NAME>/topicEndpoints"
```

### 4. Get detailed metrics for a specific queue

```bash
curl -u "<SOLACE_USERNAME>:<SOLACE_PASSWORD>" \
  -k "https://<SOLACE_HOST>:943/SEMP/v2/monitor/msgVpns/<VPN_NAME>/queues/<QUEUE_NAME>"
```

### 5. Get detailed metrics for a specific topic endpoint

```bash
curl -u "<SOLACE_USERNAME>:<SOLACE_PASSWORD>" \
  -k "https://<SOLACE_HOST>:943/SEMP/v2/monitor/msgVpns/<VPN_NAME>/topicEndpoints/<TOPIC_ENDPOINT_NAME>"
```

### 6. Get VPN-level statistics

```bash
curl -u "<SOLACE_USERNAME>:<SOLACE_PASSWORD>" \
  -k "https://<SOLACE_HOST>:943/SEMP/v2/monitor/msgVpns/<VPN_NAME>"
```

### 7. Get bridge statistics for a VPN

```bash
curl -u "<SOLACE_USERNAME>:<SOLACE_PASSWORD>" \
  -k "https://<SOLACE_HOST>:943/SEMP/v2/monitor/msgVpns/<VPN_NAME>/bridges"
```

### 8. Get client connection statistics for a VPN

```bash
curl -u "<SOLACE_USERNAME>:<SOLACE_PASSWORD>" \
  -k "https://<SOLACE_HOST>:943/SEMP/v2/monitor/msgVpns/<VPN_NAME>/clients"
```

> **Tip:** Add `| jq` at the end of each command if you have [jq](https://stedolan.github.io/jq/) installed for pretty-printing JSON.

## Production Deployment Best Practices

### Security Considerations

1. **Credentials Management**
   - Store credentials securely using environment variables or a secrets management system
   - Use read-only SEMP API credentials with minimal permissions
   - Regularly rotate credentials

2. **Network Security**
   - Use SSL/TLS for all connections
   - Configure firewalls to restrict access to Solace SEMP API ports
   - Use private networks where possible

### Performance Optimization

1. **Resource Usage**
   - Monitor the integration's memory usage and adjust as needed
   - Set appropriate polling intervals based on your needs (default: 60s)
   - Use debug logging only when troubleshooting

2. **Scaling**
   - For large Solace deployments, consider running multiple instances
   - Monitor the integration's performance metrics
   - Adjust resource limits in docker-compose.yml if needed

### Monitoring

1. **Integration Health**
   - Monitor the infrastructure agent logs
   - Set up alerts for integration failures
   - Track API response times and error rates

2. **Validation**
   - Regularly validate metrics accuracy
   - Monitor for missing or unexpected data
   - Cross-reference with Solace's native monitoring

### Maintenance

1. **Updates**
   - Regularly update the integration and dependencies
   - Test updates in a staging environment first
   - Maintain change logs and rollback procedures

2. **Backup**
   - Backup configuration files
   - Document custom configurations
   - Maintain deployment procedures

## Extensibility and SEMP API Documentation

This integration uses Solace's SEMP (Solace Element Management Protocol) v2 Monitoring API. The full API documentation is available at [Solace SEMP API Documentation](https://docs.solace.com/API-Developer-Online-Ref-Documentation/swagger-ui/software-broker/monitor/index.html#/).

### Currently Monitored Resources

The integration currently monitors:
- Message VPNs (`/msgVpns`)
- Queues (`/msgVpns/{msgVpnName}/queues`)
- Topic Endpoints (`/msgVpns/{msgVpnName}/topicEndpoints`)
- Bridges (`/msgVpns/{msgVpnName}/bridges`)
- Clients (`/msgVpns/{msgVpnName}/clients`)

### Extending the Integration

The integration can be easily extended to monitor additional SEMP API endpoints. Here's how to add new monitoring capabilities:

1. **Add New API Method**
   
   In `src/entrypoint.py`, add a new method to the `SolaceAPI` class:
   ```python
   def get_new_resource(self, vpn_name: str) -> List[Dict[str, Any]]:
       """Get statistics for the new resource
       
       See: https://docs.solace.com/API-Developer-Online-Ref-Documentation/swagger-ui/software-broker/monitor/index.html#/
       for full API documentation and available endpoints.
       """
       vpn_name = requests.utils.quote(vpn_name, safe='')
       return self.make_request(f'msgVpns/{vpn_name}/your-new-endpoint')
   ```

2. **Add Command Line Option**
   
   In the `main()` function, add your new command:
   ```python
   parser.add_argument('command', choices=[
       # ... existing choices ...
       'new-resource-stats'
   ], help='Command to execute. See SEMP API docs for available endpoints')
   ```

3. **Update Flex Configuration**
   
   In `config/solace-flex-config.yml`, add a new integration:
   ```yaml
   integrations:
     - name: nri-solace-new-resource
       commands:
         - run_as_agent: true  # Runs with agent privileges
           command: /src/entrypoint.py new-resource-stats --vpn ${vpn_name}
           prefix: solace.new_resource
           custom_attributes:
             metricType: solace
             resourceType: your-new-endpoint
   ```

### Available SEMP API Endpoints

The Solace SEMP API provides monitoring for many resources, including:

1. **Message VPN Resources**
   - ACL Profiles
   - Authorization Groups
   - Bridges
   - Client Profiles
   - Client Usernames
   - Queues
   - Replicated Topics
   - Topic Endpoints

2. **Messaging Statistics**
   - Message Rates
   - Byte Rates
   - Connection Counts
   - Subscription Statistics

3. **System-Level Monitoring**
   - Hardware Status
   - Memory Usage
   - CPU Usage
   - Disk Usage
   - Network Status

4. **Security Monitoring**
   - Certificate Authorities
   - Client Certificates
   - LDAP Authorization
   - OAuth Providers

5. **DMR (Dynamic Message Routing)**
   - Cluster Links
   - Remote Message VPNs
   - Remote Topic Subscriptions

Refer to the [SEMP API Documentation](https://docs.solace.com/API-Developer-Online-Ref-Documentation/swagger-ui/software-broker/monitor/index.html#/) for detailed information about each endpoint and their available metrics.

### Example: Adding DMR Cluster Monitoring

Here's an example of how to extend the integration to monitor DMR clusters:

```python
# In entrypoint.py
def get_dmr_cluster_stats(self) -> List[Dict[str, Any]]:
    """Get DMR cluster statistics"""
    return self.make_request('dmrClusters')

# Add to command line options
parser.add_argument('command', choices=[
    # ... existing choices ...
    'dmr-cluster-stats'
])

# Add to command execution
elif args.command == 'dmr-cluster-stats':
    result = api.get_dmr_cluster_stats()
```

Then in `solace-flex-config.yml`:
```yaml
integrations:
  - name: nri-solace-dmr
    commands:
      - command: /src/entrypoint.py dmr-cluster-stats
        prefix: solace.dmr
```

### Best Practices for Extensions

When extending the integration:

1. **Error Handling**
   - Always use the built-in error handling in `make_request()`
   - Add appropriate validation for new parameters
   - Return empty lists/dicts for missing data

2. **Performance**
   - Consider the polling interval for new metrics
   - Group related metrics to minimize API calls
   - Use appropriate caching strategies

3. **Documentation**
   - Document new metrics and their meanings
   - Update dashboard JSON with new widgets
   - Include example NRQL queries

4. **Testing**
   - Test with various Solace versions
   - Validate error conditions
   - Check rate limits and performance impact
