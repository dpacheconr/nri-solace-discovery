#!/bin/bash

# Script to update New Relic Solace Integration with the optimized configuration
set -e

echo "Updating New Relic Solace Integration..."

# Detect if running on Linux with systemd
IS_SYSTEMD=false
if [ "$(uname)" == "Linux" ] && command -v systemctl &> /dev/null; then
    IS_SYSTEMD=true
fi

# Create required directories if they don't exist
echo "Creating directories..."
mkdir -p /etc/newrelic-infra/integrations.d

# Copy the entrypoint script to the default location
echo "Updating Solace entrypoint script..."
cp src/entrypoint.py /usr/bin/entrypoint.py
chmod +x /usr/bin/entrypoint.py

# Install Python dependencies if running on Linux with systemd
if [ "$IS_SYSTEMD" = true ]; then
    echo "Installing Python dependencies..."
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
    elif command -v pip &> /dev/null; then
        pip install -r requirements.txt
    else
        echo "Warning: pip not found. Please install Python dependencies manually:"
        echo "pip install -r requirements.txt"
    fi
fi

# Copy and merge configuration files
echo "Deploying configuration files..."

# Handle solace-env-config.yml
if [ -f "/usr/bin/solace-env-config.yml" ]; then
    echo "Found existing solace-env-config.yml, merging with new configuration..."
    # Create a backup of the current config
    cp /usr/bin/solace-env-config.yml /usr/bin/solace-env-config.yml.bak
    
    # Merge the new config with the existing one using Python
    # This preserves existing values and only adds new ones
    python3 - << 'EOF'
import yaml

def merge_yaml(current, new):
    # Recursively merge new values into current while preserving existing ones
    if isinstance(current, dict) and isinstance(new, dict):
        for key, value in new.items():
            if key not in current:
                current[key] = value
            else:
                current[key] = merge_yaml(current[key], value)
        return current
    return current

try:
    with open('/usr/bin/solace-env-config.yml', 'r') as f:
        current_config = yaml.safe_load(f)
    with open('config/solace-env-config.yml', 'r') as f:
        new_config = yaml.safe_load(f)
    
    merged_config = merge_yaml(current_config, new_config)
    
    with open('/usr/bin/solace-env-config.yml', 'w') as f:
        yaml.safe_dump(merged_config, f, default_flow_style=False)
    print("Configuration successfully merged!")
except Exception as e:
    print(f"Error merging configurations: {e}")
    print("Restoring backup...")
    import shutil
    shutil.copy('/usr/bin/solace-env-config.yml.bak', '/usr/bin/solace-env-config.yml')
EOF
    # Remove the backup if merge was successful
    rm -f /usr/bin/solace-env-config.yml.bak
else
    echo "Installing default solace-env-config.yml..."
    cp config/solace-env-config.yml /usr/bin/solace-env-config.yml
    chmod 644 /usr/bin/solace-env-config.yml
    echo "NOTE: Please update /usr/bin/solace-env-config.yml with your Solace credentials"
fi

# Always update the Flex config as it contains our integration improvements
cp config/solace-flex-config.yml /etc/newrelic-infra/integrations.d/solace-flex-config.yml
chmod 644 /etc/newrelic-infra/integrations.d/solace-flex-config.yml

# Verify configuration files
echo "Verifying configuration files..."
if [ ! -f "/usr/bin/solace-env-config.yml" ]; then
    echo "Error: solace-env-config.yml not found in /usr/bin/"
    exit 1
fi

if [ ! -f "/etc/newrelic-infra/integrations.d/solace-flex-config.yml" ]; then
    echo "Error: solace-flex-config.yml not found in /etc/newrelic-infra/integrations.d/"
    exit 1
fi

# Verify Python dependencies
echo "Verifying Python dependencies..."
python3 -c "
import sys
try:
    import requests
    import yaml
    print('Required Python packages are installed')
except ImportError as e:
    print(f'Error: Missing required package - {e}')
    sys.exit(1)
"

# Restart the New Relic infrastructure agent
echo "Restarting New Relic infrastructure agent..."
if command -v service &> /dev/null; then
    service newrelic-infra restart
elif command -v systemctl &> /dev/null; then
    systemctl restart newrelic-infra
else
    echo "Warning: Could not automatically restart the New Relic infrastructure agent."
    echo "Please restart it manually using your system's service management tool."
fi

echo "Update complete!"
echo "The integration should now be discovering and monitoring all VPNs, queues, and topic endpoints."
echo ""
echo "Integration files deployed to:"
echo "- Entrypoint script: /usr/bin/entrypoint.py"
echo "- Environment config: /usr/bin/solace-env-config.yml"
echo "- Flex config: /etc/newrelic-infra/integrations.d/solace-flex-config.yml"
echo ""
echo "To verify the installation, run:"
echo "python3 /usr/bin/entrypoint.py discover-vpns"
echo ""
echo "Next steps:"
if [ ! -f "/usr/bin/solace-env-config.yml.bak" ]; then
    echo "1. Configure your Solace credentials in /usr/bin/solace-env-config.yml"
else
    echo "1. Your existing Solace configuration has been preserved and merged with new defaults"
fi
echo "2. Update your account ID in dashboards/solace-dashboard.json before importing"
echo ""
echo "You can import the dashboard template from dashboards/solace-dashboard.json into your New Relic account."
