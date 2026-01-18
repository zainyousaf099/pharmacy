# core/network_config.py
"""
Network Configuration for Clinic App
Handles server/client mode for database sharing across multiple PCs
"""

import os
import json
import socket
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent / 'network_config.json'

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_hostname():
    """Get the hostname of this machine"""
    return socket.gethostname()

def load_config():
    """Load network configuration from file"""
    default_config = {
        'mode': 'standalone',  # 'server', 'client', or 'standalone'
        'server_ip': '',
        'server_port': 8000,
        'is_pharmacy': False,
        'last_connected': None
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                return {**default_config, **config}
        except Exception:
            return default_config
    return default_config

def save_config(config):
    """Save network configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False

def set_server_mode():
    """Set this machine as the server (Pharmacy)"""
    config = load_config()
    config['mode'] = 'server'
    config['server_ip'] = get_local_ip()
    config['is_pharmacy'] = True
    return save_config(config)

def set_client_mode(server_ip, server_port=8000):
    """Set this machine as a client connecting to server"""
    config = load_config()
    config['mode'] = 'client'
    config['server_ip'] = server_ip
    config['server_port'] = server_port
    config['is_pharmacy'] = False
    return save_config(config)

def set_standalone_mode():
    """Set this machine to use local database"""
    config = load_config()
    config['mode'] = 'standalone'
    config['server_ip'] = ''
    config['is_pharmacy'] = False
    return save_config(config)

def is_server():
    """Check if this machine is running as server"""
    config = load_config()
    return config.get('mode') == 'server'

def is_client():
    """Check if this machine is running as client"""
    config = load_config()
    return config.get('mode') == 'client'

def get_server_url():
    """Get the server URL for API calls"""
    config = load_config()
    if config.get('mode') == 'client' and config.get('server_ip'):
        return f"http://{config['server_ip']}:{config.get('server_port', 8000)}"
    return None

def check_server_connection(server_ip, server_port=8000, timeout=3):
    """Check if a server is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((server_ip, server_port))
        sock.close()
        return result == 0
    except Exception:
        return False

def discover_servers(port=8000, timeout=1):
    """Discover servers on the local network"""
    local_ip = get_local_ip()
    base_ip = '.'.join(local_ip.split('.')[:-1])
    servers = []
    
    for i in range(1, 255):
        ip = f"{base_ip}.{i}"
        if ip != local_ip:
            if check_server_connection(ip, port, timeout):
                servers.append({'ip': ip, 'port': port})
    
    return servers

def get_network_status():
    """Get current network status for display"""
    config = load_config()
    local_ip = get_local_ip()
    hostname = get_hostname()
    
    status = {
        'local_ip': local_ip,
        'hostname': hostname,
        'mode': config.get('mode', 'standalone'),
        'server_ip': config.get('server_ip', ''),
        'server_port': config.get('server_port', 8000),
        'is_connected': False,
        'connection_status': 'Disconnected'
    }
    
    if config.get('mode') == 'server':
        status['is_connected'] = True
        status['connection_status'] = f"Server Mode - IP: {local_ip}:8000"
    elif config.get('mode') == 'client':
        server_ip = config.get('server_ip')
        if server_ip and check_server_connection(server_ip, config.get('server_port', 8000)):
            status['is_connected'] = True
            status['connection_status'] = f"Connected to {server_ip}"
        else:
            status['connection_status'] = f"Cannot reach server {server_ip}"
    else:
        status['connection_status'] = "Standalone Mode (Local Database)"
    
    return status
