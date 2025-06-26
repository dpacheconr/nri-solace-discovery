#!/usr/bin/env python3
import os
import sys
import json
import yaml
import requests
import argparse
from typing import Dict, Any, List, Optional, Union
import urllib3
import logging

# Constants
CONFIG_PATH = "/usr/bin/solace-env-config.yml"

def format_json_for_log(obj: Any) -> str:
    """
    Format a JSON-serializable object for logging with pretty printing.
    Makes logs more human-readable in debug mode.
    """
    try:
        return json.dumps(obj, indent=2, sort_keys=True)
    except Exception as e:
        logging.warning(f"Could not pretty-print JSON for logs: {e}")
        return str(obj)

def initialize_logging():
    """
    Initialize logging to write to a file.
    Uses configuration from solace-env-config.yml if available.
    """
    # Default values
    log_directory = "/var/log/newrelic-solace"
    log_level = logging.INFO
    
    # Try to load config
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            
            # Get log directory from config if available
            config_log_dir = config.get('SOLACE_LOG_DIRECTORY')
            if config_log_dir:
                log_directory = config_log_dir
                
            # Get log level from config if available
            config_log_level = config.get('SOLACE_LOG_LEVEL', 'INFO').upper()
            log_level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            log_level = log_level_map.get(config_log_level, logging.INFO)
    except Exception as e:
        # If we can't read config, use defaults
        pass  # Don't log here as logging is not initialized yet

    log_file = os.path.join(log_directory, "entrypoint.log")
    
    # Ensure log directory exists
    try:
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
    except Exception:
        # If we can't create the directory, fall back to /tmp
        log_directory = "/tmp"
        log_file = os.path.join(log_directory, "newrelic-solace.log")
    
    # Set up file handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)  # Set log level from config
    
    # Remove existing handlers (to avoid duplicate logging)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our file handler
    root_logger.addHandler(file_handler)
    
    # Log initialization
    logging.info("Logging initialized to %s with level %s", log_file, 
                 logging.getLevelName(root_logger.getEffectiveLevel()))

def load_config():
    """
    Load configuration from solace-env-config.yml
    Returns the loaded config or empty dict if not found
    """
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return {}

# Initialize logging before anything else
initialize_logging()

# Disable SSL warnings
urllib3.disable_warnings()

def normalize_key(key: str) -> str:
    """Normalize a dictionary key to be lowercase and valid for New Relic"""
    # Convert to lowercase and replace problematic characters
    key = str(key).lower()
    # Special handling for specific keys to ensure consistency
    special_keys = {
        'msgvpnname': 'vpnname',
        'msgvpn': 'vpnname',
        'vpnname': 'vpnname',
        'queuename': 'queuename',
        'queue': 'queuename',
        'topicendpointname': 'topicendpointname',
        'resourcetype': 'resourcetype',
        'clientname': 'clientname',
        'msgvpn': 'vpnname',
        'bridgename': 'bridgename'
    }
    
    # Check if we have a direct special key
    normalized = special_keys.get(key.lower())
    if normalized:
        return normalized
        
    # Replace any sequences of non-alphanumeric chars with underscore
    import re
    key = re.sub(r'[^a-z0-9]+', '_', key)
    # Remove leading/trailing underscores
    key = key.strip('_')
    return key

def flatten_dict(d: Union[Dict, List], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Recursively flatten a nested dictionary or list.
    Handles both dictionaries and lists, normalizing keys for New Relic compatibility.
    Preserves numeric types (int, float) for metric values.
    
    Args:
        d: The dictionary or list to flatten
        parent_key: The base key to prepend to flattened keys
        sep: The separator to use between nested key levels
    
    Returns:
        A flattened dictionary with normalized keys and preserved numeric types
    """
    items: List[tuple] = []
    
    # Function to convert string values to numbers if they represent numeric values
    def try_numeric(v):
        if not isinstance(v, str):
            return v
        try:
            if '.' in v:
                return float(v)
            return int(v)
        except (ValueError, TypeError):
            return v

    # Handle lists by treating each index as a key
    if isinstance(d, list):
        # If it's just a simple list of primitives, don't flatten
        if not any(isinstance(x, (dict, list)) for x in d):
            return {parent_key: [try_numeric(x) for x in d]} if parent_key else d
        # Otherwise flatten each item
        for i, item in enumerate(d):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            if isinstance(item, (dict, list)):
                items.extend(flatten_dict(item, new_key, sep).items())
            else:
                items.append((new_key, try_numeric(item)))
    # Handle dictionaries
    elif isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{normalize_key(k)}" if parent_key else normalize_key(k)
            # Check if this is a known metric field that should be numeric
            is_metric = any(x in k.lower() for x in ['count', 'rate', 'usage', 'size', 'byte', 'time', 'uptime', 'limit'])
            if isinstance(v, (dict, list)):
                items.extend(flatten_dict(v, new_key, sep).items())
            else:
                value = try_numeric(v) if is_metric else v
                items.append((new_key, value))
    else:
        return {parent_key: try_numeric(d)} if parent_key else d

    return dict(items)

def print_json_and_exit(data, exit_code=0):
    """Print data as JSON and exit with given code"""
    # Ensure we're handling empty results properly
    if data is None or (isinstance(data, dict) and not data) or (isinstance(data, list) and len(data) == 0):
        print(json.dumps({}))
        sys.exit(exit_code)
    
    # Format the output like Cohesity example:
    # Output everything as a single JSON array or object
    if isinstance(data, list):
        # Already a list, just output as JSON
        print(json.dumps(data))
    elif isinstance(data, dict):
        # Single dictionary
        print(json.dumps(data))
    else:
        # Any other value - wrap in a simple object
        print(json.dumps({"value": data}))
        
    sys.exit(exit_code)

class SolaceAPI:
    def __init__(self):
        # Load environment config
        config = load_config()
        self.base_url = config.get('SOLACE_BASE_URL')
        self.username = config.get('SOLACE_USERNAME')
        self.password = config.get('SOLACE_PASSWORD')
                
        if not all([self.base_url, self.username, self.password]):
            logging.error("Missing required configuration")
            print_json_and_exit([], 0)
            
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = False  # Skip SSL verification
        self.session.headers.update({'Content-Type': 'application/json'})

    def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Make a request to the Solace SEMP API and ensure flat list output"""
        base_url = self.base_url.rstrip('/SEMP/v2/monitor')
        url = f"{base_url}/SEMP/v2/monitor/{endpoint}"
        
        try:
            logging.debug(f"Making API request to {url}")
            if params:
                logging.debug(f"Request parameters: \n{format_json_for_log(params)}")
                
            response = self.session.get(url, params=params)
            logging.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            # Extract and flatten the 'data' key if present
            raw_data = data.get('data', [])
            
            # Process the raw data into flat dictionaries
            result = []
            if isinstance(raw_data, list):
                logging.debug(f"Processing {len(raw_data)} items from API response")
                for item in raw_data:
                    if isinstance(item, dict):
                        # Normalize keys before flattening
                        normalized_dict = {normalize_key(k): v for k, v in item.items()}
                        result.append(flatten_dict(normalized_dict))
            elif isinstance(raw_data, dict):
                # Normalize keys before flattening
                normalized_dict = {normalize_key(k): v for k, v in raw_data.items()}
                result.append(flatten_dict(normalized_dict))
                
            # Debug log outside of the actual data flow
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"Processed API data into {len(result)} result items")
                if result and len(result) > 0:
                    sample_item = result[0]
                    logging.debug(f"Sample result item: \n{format_json_for_log(sample_item)}")
            return result

        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            print_json_and_exit({"error": f"API request failed: {str(e)}"}, 0)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON response: {e}")
            print_json_and_exit({"error": f"Invalid JSON response: {str(e)}"}, 0)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            print_json_and_exit({"error": f"Unexpected error: {str(e)}"}, 0)

    def add_custom_attributes(self, items: List[Dict[str, Any]], event_type: str, resource_type: str = None) -> None:
        """
        Normalize all attribute keys in items - ensures consistent naming for dashboard queries.
        All custom attributes should come from the Flex config.
        """
        for item in items:
            # Create a new dict with normalized keys
            normalized_item = {}
            for key, value in item.items():
                normalized_key = normalize_key(key)  # Use our normalize_key function for consistency
                normalized_item[normalized_key] = value
            
            # Replace the original dict with the normalized version
            item.clear()
            item.update(normalized_item)

    def get_vpns(self) -> List[Dict[str, Any]]:
        """Get list of message VPNs"""
        data = self.make_request('msgVpns')
        logging.debug(f"Retrieved {len(data)} VPNs from API")
        
        # Log system VPNs being filtered out
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            system_vpns = [vpn.get('vpnname') for vpn in data if vpn.get('vpnname', '').startswith('#')]
            if system_vpns:
                logging.debug(f"Filtering out system VPNs: {', '.join(system_vpns)}")
        
        # Filter only active VPNs and exclude system VPNs (starting with #)
        active_vpns = [vpn for vpn in data if vpn.get('state') == 'up' and not vpn.get('vpnname', '').startswith('#')]
        
        # Add a simplified field for easy extraction
        for vpn in active_vpns:
            vpn['isActive'] = True
            
        logging.debug(f"Returning {len(active_vpns)} active, non-system VPNs")
        return active_vpns

    def get_queues(self, vpn_name: str) -> List[Dict[str, Any]]:
        """Get list of queues for a VPN"""
        if not vpn_name:
            logging.warning("No VPN name provided")
            return []
        # URL encode VPN name for special characters
        vpn_name = requests.utils.quote(vpn_name, safe='')
        data = self.make_request(f'msgVpns/{vpn_name}/queues')
        
        # Add vpnname to each queue for easier reference
        for queue in data:
            queue['vpnname'] = vpn_name
            
        return data

    def get_topic_endpoints(self, vpn_name: str) -> List[Dict[str, Any]]:
        """Get list of topic endpoints for a VPN"""
        if not vpn_name:
            logging.warning("No VPN name provided")
            return []
        vpn_name = requests.utils.quote(vpn_name, safe='')
        data = self.make_request(f'msgVpns/{vpn_name}/topicEndpoints')
        
        # Add vpnname to each endpoint for easier reference
        for endpoint in data:
            endpoint['vpnname'] = vpn_name
            
        return data

    def get_queue_stats(self, vpn_name: str, queue_name: str) -> Dict[str, Any]:
        """Get stats for a specific queue"""
        if not vpn_name or not queue_name:
            logging.warning("Missing VPN name or queue name")
            return {}
        vpn_name = requests.utils.quote(vpn_name, safe='')
        queue_name = requests.utils.quote(queue_name, safe='')
        data = self.make_request(f'msgVpns/{vpn_name}/queues/{queue_name}')
        return data if isinstance(data, dict) else data[0] if data else {}

    def get_topic_endpoint_stats(self, vpn_name: str, endpoint_name: str) -> Dict[str, Any]:
        """Get stats for a specific topic endpoint"""
        if not vpn_name or not endpoint_name:
            logging.warning("Missing VPN name or endpoint name")
            return {}
        vpn_name = requests.utils.quote(vpn_name, safe='')
        endpoint_name = requests.utils.quote(endpoint_name, safe='')
        data = self.make_request(f'msgVpns/{vpn_name}/topicEndpoints/{endpoint_name}')
        return data[0] if data else {}

    def get_vpn_stats(self, vpn_name: str) -> Dict[str, Any]:
        """Get stats for a specific VPN"""
        if not vpn_name:
            logging.warning("No VPN name provided")
            return {}
        vpn_name = requests.utils.quote(vpn_name, safe='')
        data = self.make_request(f'msgVpns/{vpn_name}')
        return data[0] if data else {}

    def get_bridge_stats(self, vpn_name: str) -> List[Dict[str, Any]]:
        """Get bridge stats for a VPN"""
        if not vpn_name:
            return []
        vpn_name = requests.utils.quote(vpn_name, safe='')
        return self.make_request(f'msgVpns/{vpn_name}/bridges')

    def get_client_stats(self, vpn_name: str) -> List[Dict[str, Any]]:
        """Get client stats for a VPN"""
        if not vpn_name:
            return []
        vpn_name = requests.utils.quote(vpn_name, safe='')
        return self.make_request(f'msgVpns/{vpn_name}/clients')

def main():
    """
    Main entry point for the Solace API client.
    Parses command line arguments and executes the appropriate command.
    """
    parser = argparse.ArgumentParser(
        description='Solace SEMP API Client for New Relic Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover all VPNs
  python3 entrypoint.py discover-vpns
  
  # Get all queue stats across all VPNs
  python3 entrypoint.py queue-stats-all
  
  # Get stats for all bridges across all VPNs
  python3 entrypoint.py bridge-stats-all
"""
    )
    
    commands_help = {
        'discover-vpns': 'Discover all message VPNs',
        'discover-queues-all': 'Discover all queues across all VPNs',
        'discover-topic-endpoints-all': 'Discover all topic endpoints across all VPNs',
        'queue-stats-all': 'Get statistics for all queues across all VPNs',
        'vpn-stats-all': 'Get statistics for all VPNs',
        'bridge-stats-all': 'Get bridge statistics for all VPNs',
        'client-stats-all': 'Get client statistics for all VPNs'
    }
    
    parser.add_argument('command', choices=list(commands_help.keys()), 
                       help='Command to execute', metavar='COMMAND',
                       type=str.lower)  # Case-insensitive command matching
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    try:
        args = parser.parse_args()
        
        # Set debug logging if requested via command line (overrides config)
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Debug logging enabled via command line")
            logging.debug(f"Python version: {sys.version}")
            logging.debug(f"Running from directory: {os.getcwd()}")
            logging.debug(f"Arguments: {vars(args)}")
        
        api = SolaceAPI()
        
        # No argument validation needed - all commands operate on all VPNs
        
        # Log the command being executed
        logging.debug(f"Executing command: {args.command} with args: {vars(args)}")
        logging.info(f"Processing command: {args.command}")
        
        # Execute the command
        if args.command == 'discover-vpns':
            logging.debug("Discovering VPNs...")
            result = api.get_vpns()
            # Get VPN list for output
            vpn_names = [vpn.get('vpnname') for vpn in result if vpn.get('vpnname')]
            logging.debug(f"Found {len(result)} VPNs, {len(vpn_names)} active non-system VPNs")
            if logging.getLogger().isEnabledFor(logging.DEBUG) and result:
                logging.debug(f"Active VPNs: \n{format_json_for_log(vpn_names)}")
            
        elif args.command == 'discover-queues-all':
            # Get all queues for all VPNs
            vpns = api.get_vpns()
            result = []
            for vpn in vpns:
                vpn_name = vpn.get('vpnname')
                if vpn_name:
                    queues = api.get_queues(vpn_name)
                    api.add_custom_attributes(queues, '', '')  # Just normalize the attribute names
                    result.extend(queues)
                    
        elif args.command == 'discover-topic-endpoints-all':
            # Get all topic endpoints for all VPNs
            vpns = api.get_vpns()
            result = []
            for vpn in vpns:
                vpn_name = vpn.get('vpnname')
                if vpn_name:
                    endpoints = api.get_topic_endpoints(vpn_name)
                    api.add_custom_attributes(endpoints, '', '')  # Just normalize the attribute names
                    result.extend(endpoints)
                    
        elif args.command == 'queue-stats-all':
            # Get stats for all queues in all VPNs
            vpns = api.get_vpns()
            result = []
            for vpn in vpns:
                vpn_name = vpn.get('vpnname')
                if not vpn_name:
                    continue
                
                # Get all queues for this VPN
                queues = api.get_queues(vpn_name)
                for queue in queues:
                    queue_name = queue.get('queuename')
                    if not queue_name:
                        continue
                    
                    # Get stats for this queue
                    stats = api.get_queue_stats(vpn_name, queue_name)
                    if stats:
                        api.add_custom_attributes([stats], '', '')  # Just normalize the attribute names
                        result.append(stats)
                        
        elif args.command == 'vpn-stats-all':
            # Get stats for all VPNs
            vpns = api.get_vpns()
            result = []
            for vpn in vpns:
                vpn_name = vpn.get('vpnname')
                if vpn_name:
                    stats = api.get_vpn_stats(vpn_name)
                    if stats:
                        api.add_custom_attributes([stats], '', '')  # Just normalize the attribute names
                        result.append(stats)
                        
        elif args.command == 'bridge-stats-all':
            # Get bridge stats for all VPNs
            vpns = api.get_vpns()
            result = []
            for vpn in vpns:
                vpn_name = vpn.get('vpnname')
                if vpn_name:
                    bridges = api.get_bridge_stats(vpn_name)
                    api.add_custom_attributes(bridges, '', '')  # Just normalize the attribute names
                    result.extend(bridges)
                    
        elif args.command == 'client-stats-all':
            # Get client stats for all VPNs
            vpns = api.get_vpns()
            result = []
            for vpn in vpns:
                vpn_name = vpn.get('vpnname')
                if vpn_name:
                    clients = api.get_client_stats(vpn_name)
                    api.add_custom_attributes(clients, '', '')  # Just normalize the attribute names
                    result.extend(clients)
        else:
            print_json_and_exit({"error": f"Unknown command: {args.command}"}, 0)
            
        # Ensure result is always a valid JSON array
        if result is None:
            result = []
        elif not isinstance(result, list):
            result = [result] if result else []
            
        logging.debug(f"Command {args.command} completed. Returning {len(result)} results.")
        if logging.getLogger().isEnabledFor(logging.DEBUG) and result:
            logging.debug(f"Result types: {[type(item).__name__ for item in result[:5]]}...")
            # Log a sample item from the result for debugging
            if result and len(result) > 0:
                sample_item = result[0]
                logging.debug(f"Sample result item: \n{format_json_for_log(sample_item)}")
        print_json_and_exit(result)
        
    except Exception as e:
        logging.error(f"Unexpected error in command {getattr(args, 'command', 'unknown')}: {str(e)}", exc_info=True)
        print_json_and_exit({"error": f"Unexpected error: {str(e)}"}, 0)

if __name__ == '__main__':
    main()
