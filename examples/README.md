# Solace Integration Examples

This directory contains example output from the Solace integration commands, showing the data structure and metrics collected from a Solace PubSub+ broker.

## Files

- `vpn-discovery.json`: Output from the `discover-vpns` command showing all available VPNs on the broker
- `queue-discovery.json`: Output from the `discover-queues --vpn <vpn_name>` command showing all queues in a VPN
- `topic-endpoint-discovery.json`: Output from the `discover-topic-endpoints --vpn <vpn_name>` command showing topic endpoints
- `queue-stats.json`: Detailed statistics for a specific queue in a VPN
- `vpn-stats.json`: Detailed statistics for a specified VPN
- `bridge-stats.json`: Bridge statistics for a specified VPN
- `client-stats.json`: Client connection statistics for a specified VPN
- `sample-config.yml`: Example configuration file with comments on collected metrics
- `EXAMPLE-DATA.md`: Simplified and sanitized data samples showing the structure of metrics collected

**Note:** The JSON files contain raw output from a test environment. For cleaner, sanitized examples with simplified structure, please refer to the `EXAMPLE-DATA.md` file.

## Usage

These files can be used as reference for:

1. Understanding the data structure returned by the integration
2. Seeing which metrics are available for monitoring
3. Building custom dashboards and alerts based on the collected metrics

## Generating Your Own Examples

You can generate similar examples for your own Solace environment using:

```bash
# Set up the environment
cd /path/to/nri-solace
export PYTHONPATH=$(pwd)

# Generate examples
python3 src/entrypoint.py discover-vpns --config config/solace-env-config.yml > examples/vpn-discovery.json
python3 src/entrypoint.py discover-queues --vpn <vpn_name> --config config/solace-env-config.yml > examples/queue-discovery.json
python3 src/entrypoint.py vpn-stats --vpn <vpn_name> --config config/solace-env-config.yml > examples/vpn-stats.json
```

## Metric Categories

The integration collects the following categories of metrics:

1. **VPN Metrics**: Overall message rates and health of message VPNs
2. **Queue Metrics**: Message rates and spool usage for queues
3. **Topic Endpoint Metrics**: Message rates and spool usage for topic endpoints
4. **Bridge Metrics**: Bridge connection status and message flows
5. **Client Metrics**: Client connection status and message flows
