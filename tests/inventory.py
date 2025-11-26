#!/usr/bin/env python3
"""
Dynamic inventory script for Horizon cluster deployment.
Reads node configuration from mandatory_vars.yml and generates Ansible inventory.
"""
import yaml
import json
import sys
import os

def load_vars_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, '..', '..', 'defaults', 'main', 'mandatory_vars.yml'),
        os.path.join(script_dir, '..', 'defaults', 'main', 'mandatory_vars.yml'),
        os.path.join(script_dir, 'defaults', 'main', 'mandatory_vars.yml'),
    ]
    
    vars_file = None
    for path in possible_paths:
        normalized_path = os.path.normpath(path)
        if os.path.exists(normalized_path):
            vars_file = normalized_path
            break
    
    if vars_file is None:
        print(f"Warning: mandatory_vars.yml not found in any expected location", file=sys.stderr)
        print(f"Searched paths:", file=sys.stderr)
        for path in possible_paths:
            print(f"  - {os.path.normpath(path)}", file=sys.stderr)
        return None
    
    try:
        with open(vars_file, 'r') as f:
            vars_data = yaml.safe_load(f)
            
        if vars_data is None:
            print(f"Warning: {vars_file} is empty or invalid", file=sys.stderr)
            return None
            
        return vars_data
        
    except FileNotFoundError:
        print(f"Warning: {vars_file} not found", file=sys.stderr)
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error loading vars file: {e}", file=sys.stderr)
        return None

def build_inventory(vars_data):
    inventory = {
        'all': {
            'children': ['horizon_cluster']
        },
        'horizon_cluster': {
            'hosts': [],
            'vars': {
                'ansible_user': 'root',
                'ansible_python_interpreter': '/usr/bin/python3',
                'ansible_ssh_common_args': '-o StrictHostKeyChecking=no'
            }
        },
        '_meta': {
            'hostvars': {}
        }
    }
    
    if vars_data is None:
        return inventory
    
    horizon_nodes = vars_data.get('horizon_nodes', [])
    
    if not horizon_nodes:
        print("Warning: No horizon_nodes found in configuration", file=sys.stderr)
        return inventory
    
    if not isinstance(horizon_nodes, list):
        print(f"Warning: horizon_nodes should be a list, got {type(horizon_nodes)}", file=sys.stderr)
        return inventory
    
    for node in horizon_nodes:
        if not isinstance(node, dict):
            print(f"Warning: Invalid node configuration: {node}", file=sys.stderr)
            continue
            
        hostname = node.get('hostname')
        ip = node.get('ip')
        
        if not hostname:
            print(f"Warning: Node missing hostname: {node}", file=sys.stderr)
            continue
            
        if not ip:
            print(f"Warning: Node {hostname} missing IP address", file=sys.stderr)
            continue
        
        inventory['horizon_cluster']['hosts'].append(hostname)
        inventory['_meta']['hostvars'][hostname] = {
            'ansible_host': ip
        }
    
    return inventory

def main():
    vars_data = load_vars_file()    
    inventory = build_inventory(vars_data)
    print(json.dumps(inventory, indent=2))

if __name__ == '__main__':
    main()