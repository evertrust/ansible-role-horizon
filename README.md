Evertrust Horizon
=================

Requirements
------------
To be able to use this role you have to previously provision VMs running on **CentOS/RHEL** and meeting the requirements from the official Evertrust documentation: https://docs.evertrust.fr/horizon/install-guide/2.8/iaas/prerequisites.
A root access to these VMs is mandatory, as per a normal RPM install of Horizon. You will have to configure your Ansible playbook to use these accounts while playing the role.

**IMPORTANT:** A running instance of MongoDB is also necessary. MongoDB should be accessible from all Horizon nodes.

### Ansible Prerequisites

It is necessary to:

1. **Install the ansible.posix collection:**
   ```bash
   ansible-galaxy collection install ansible.posix
   ```

2. **Configure SSH access:** Set up SSH key-based authentication from your control machine to all target nodes:
   ```bash
   # Generate SSH key if needed
   ssh-keygen -t rsa -b 4096

   # Copy to each target node
   ssh-copy-id root@horizon-node1-ip
   ssh-copy-id root@horizon-node2-ip
   ```

3. **Dynamic Inventory:** The role includes a dynamic inventory script at `tests/inventory.py` that automatically generates the Ansible inventory from your `mandatory_vars.yml` configuration. The script sets appropriate connection parameters and maps hostnames to IP addresses, eliminating manual inventory management.

4. **Licence File Setup**
Before deployment, you must provide a valid Horizon licence file. Create the required directories and place your licence file:
```bash
# For Molecule testing
mkdir -p molecule/default/files
cp /path/to/your/horizon.lic molecule/default/files/horizon.lic

# For VM deployment
mkdir -p tests/files
cp /path/to/your/horizon.lic tests/files/horizon.lic
```

Note: The files/ directories are not included in the repository and must be created before running the role.

### Firewall Configuration

**IMPORTANT:** This role automatically configures firewalld with the necessary ports. The following ports are opened:

| Port/Service | Purpose | When Opened |
|--------------|---------|-------------|
| **22 (SSH)** | Remote administration | Always |
| **443** | HTTPS web access | Always |
| **7626** | Akka Management (cluster discovery) | Only for HA (2+ nodes) |
| **17335** | Akka Artery (cluster communication) | Only for HA (2+ nodes) |

**Note:** Port 9000 (Horizon application) is bound to `127.0.0.1` only and is NOT exposed externally. Nginx acts as a reverse proxy on port 443 (HTTPS only).

**Note on Akka/Pekko:** Horizon internally uses Pekko (the successor to Akka), but configuration variables maintain the `AKKA_*` naming convention for backwards compatibility with older Horizon versions. The functionality and port numbers remain the same.

**For MongoDB:** If managing the MongoDB VM separately, ensure port 27017 is open only to Horizon node IPs for security.

## Role Variables

The following table regroups the data that you have to provide the Ansible role with for the deployment and configuration to work properly.

**IMPORTANT:** All these variables must be configured in `defaults/main/mandatory_vars.yml` with real values before deployment.

| Key | Value Type |
|-----|------------|
| `horizon_play_http_secret_key` | Random string, 128 characters, may include `@`, `!`, `#` |
| `horizon_default_ssv_key` | Random string, 128 characters, may include `@`, `!`, `#` |
| `horizon_event_seal_secret` | Random string, 128 characters, may include `@`, `!`, `#` |
| `horizon_version` | Horizon version (e.g., `2.8.1`) |
| `horizon_pkg_uri` | URL where you store the Horizon RPM (check architecture: x86_64 or aarch64) |
| `horizon_repository_username` | Username to authenticate to the Evertrust repository |
| `horizon_repository_password` | Password to authenticate to the Evertrust repository |
| `horizon_tinkey_version` | Tinkey version (required for Horizon >= 2.8, e.g., `1.12.0.1`) |
| `horizon_tinkey_pkg_uri` | URL where you store the Tinkey RPM (check architecture: x86_64 or aarch64) |
| `horizon_licence_src_path` | Path to your Horizon license on your control machine |
| `horizon_mongodb_username` | MongoDB user pre-created on your MongoDB instance |
| `horizon_mongodb_password` | Password of the MongoDB user |
| `horizon_mongodb_uri` | MongoDB connection string (auto-built from username/password/hostname) |
| `horizon_mongodb_shell_package_uri` | URL where you store the Mongosh RPM (check architecture: x86_64 or aarch64) |
| `horizon_mongodb_hostname` | Hostname of your MongoDB instance |
| `horizon_mongodb_ip` | IP address of your MongoDB instance |
| `horizon_nodes` | List of Horizon nodes with hostname and IP (see below) |
| `horizon_akka_discovery_port` | Port for Akka cluster discovery (default: 7626) |
| `horizon_akka_artery_port` | Port for Akka cluster communication (default: 17335) |
| `horizon_configure_firewall` | Set to `false` to skip firewall configuration (default: `true`) |
| `horizon_extra_allowed_hosts` | Additional hosts allowed in Play filter, e.g. load balancer hostname (default: `[]`) |

### Tinkey / KMS Variables (Horizon >= 2.8)

| Key | Value Type |
|-----|------------|
| `horizon_tink_master_key_uri` | KMS key URI (e.g. `gcp-kms://...` or `aws-kms://...`). Leave empty for soft mode (plaintext keyset). |
| `horizon_tink_credentials_src_path` | Path to the KMS credentials file on the Ansible controller. Leave empty for soft mode or HSM. |
| `horizon_tink_credentials_path` | Destination path of the KMS credentials file on the VM (default: `/opt/horizon/etc/tink-credentials.json`) |

**Horizon Nodes Configuration:**

For **standalone deployment** (single node):
```yaml
horizon_nodes:
  - hostname: horizon-node1-vm
    ip: 10.10.21.68
```

For **High Availability** (2-5 nodes):
```yaml
horizon_nodes:
  - hostname: horizon-node1-vm
    ip: 10.10.21.68
  - hostname: horizon-node2-vm
    ip: 10.10.21.69
  - hostname: horizon-node3-vm
    ip: 10.10.21.70
```

**IMPORTANT - Architecture Note:** Ensure the `horizon_mongodb_shell_package_uri` matches your system architecture:
- For **x86_64** (most common): Use the x86_64 RPM URL
- For **aarch64** (ARM): Use the aarch64 RPM URL

The default configuration uses the architecture detected at runtime (`ansible_facts['architecture']`). The Horizon and Tinkey RPMs default to `noarch` and work on both architectures.

## Overview

The previous table is not exhaustive but the excluded variables can be left as they are for a deployment with default values (valid in most cases). Note that the more variables you customize for your environment and needs, the less configuration will be necessary afterwards.

| Initial variables localisation |
|--------------------------------|
| `defaults/main/default_values.yml` : variables that can optionally be changed |
| `defaults/main/mandatory_vars.yml` : list of variables that must be set before using the role |

This role is composed of the following steps played in order:

### 1. Package Installation

The download and install of the necessary packages to run Horizon, including:
- System dependencies (wget, nginx, postfix, firewalld, epel-release)
- Horizon RPM package
- Tinkey RPM package (required for Horizon >= 2.8, used for AES256 keyset encryption)
- MongoDB shell (mongosh)
- SELinux configuration if enforcing mode is detected

### 2. Certificate Generation

The generation of certificates for Nginx if you didn't configure the variables `horizon_csr`, `horizon_pem`, `horizon_key`, and `horizon_chain_pem`. If you did, this step copies the content of these variables to provide your web server.

By default (`horizon_generate_default_cert: true`), the role automatically generates self-signed SSL/TLS certificates for Nginx with the following specifications:

- **Key type**: RSA 4096-bit
- **Hashing algorithm**: SHA-256
- **Certificate location**: `/etc/nginx/ssl/`
- **Validity**: 365 days
- **Subject fields**: Configurable via variables in `default_values.yml` (country, organization, OU, CN)

The generated files include:
- `horizon.key` - Private key
- `horizon.csr` - Certificate Signing Request
- `horizon.pem` - Self-signed certificate
- `horizon-chain.pem` - Certificate chain

All certificate files are automatically set with proper permissions (root:nginx, 0640).

**If you want to add your own certificate for Horizon after deployment:**

1. Copy your certificates to the Horizon nodes:
   - Certificate: `/etc/nginx/ssl/horizon.pem`
   - Private key: `/etc/nginx/ssl/horizon.key`
   - Certificate chain: `/etc/nginx/ssl/horizon-chain.pem`
   - CSR (optional): `/etc/nginx/ssl/horizon.csr`

2. Set proper permissions:
```bash
   sudo chown root:nginx /etc/nginx/ssl/horizon.*
   sudo chmod 640 /etc/nginx/ssl/horizon.*
```
3. Test and Reload Nginx:
```bash
   sudo nginx -t
   sudo systemctl reload nginx
```

### 3. Tinkey Keyset Generation (Horizon >= 2.8 only)

Generation and distribution of the AES256-GCM encryption keyset used by Horizon:
- On HA deployments: generated on node 1 and distributed to all other nodes
- On standalone deployments: generated directly on the single node
- Keyset stored at `/opt/horizon/etc/horizon.keyset` (permissions: `horizon:horizon 0640`)

### 4. Configuration Provisioning

The provisioning of your Horizon licence and the different configuration files needed for Horizon to run properly, based on their respective templates:
- Deployment of license file to `/opt/horizon/etc/horizon.lic`
- Updates to `/etc/hosts` with cluster node entries
- Generation of `/etc/default/horizon` with JVM, Play, MongoDB, and Akka cluster settings
- Configuration of hosts.allowed whitelist
- Nginx symlink creation

### 5. Firewall Configuration

Automatic configuration of firewalld to open necessary ports:
- SSH (22) to prevent lockout
- HTTPS (443) for web access
- Akka cluster ports (7626, 17335) for HA deployments only
- Can be disabled by setting `horizon_configure_firewall: false`

### 6. Service Management

The start of adequate services:
- Postfix service
- Horizon service
- Nginx service (with configuration test)

### Akka Cluster Split-Brain Resolver

**IMPORTANT:** For High Availability deployments (2+ nodes), the role automatically configures Akka's split-brain resolver using a MongoDB-based lease-majority strategy:

```hocon
akka.cluster.split-brain-resolver {
    active-strategy = "lease-majority"
    lease-majority {
      lease-implementation = "lease.mongo"
    }
}
```

This configuration ensures proper cluster behavior during network partitions and prevents data inconsistency. It is automatically included in the `hosts_allowed.j2` template.

### Hosts Allowed Configuration

Additionally, a touchy and key element of the Horizon configuration is the Play variable "hosts allowed" in the horizon-extra.conf file. It configures the whitelist allowed to access Horizon.

The role automatically configures this whitelist to include:
- localhost
- All Horizon cluster node hostnames
- Any additional hosts defined in `horizon_extra_allowed_hosts` (e.g. load balancer hostname, `127.0.0.1` for local testing)

This prevents "Host not allowed" errors when accessing Horizon through different hostnames.

## Deployment Types

### Standalone Deployment

For a single Horizon instance (no High Availability), configure only one node in `horizon_nodes`. The role will:
- Only open HTTP, HTTPS, and SSH ports
- Not open Akka cluster ports
- Configure Horizon without cluster formation

### High Availability Deployment

For a clustered Horizon deployment (2-5 nodes), configure multiple nodes in `horizon_nodes`. The role will:
- Open all required ports including Akka cluster ports
- Configure nodes to automatically discover each other
- Enable split-brain resolver for cluster stability
- Provide redundancy and load distribution

## Example Playbook

Here is a basic way of using this role:

```yaml
- name: Deploy Horizon
  hosts: horizon_nodes
  become: true
  gather_facts: true
  roles:
    - role: horizon
```

### Using the Provided Test Playbook

```bash
# 1. Configure your variables in defaults/main/mandatory_vars.yml

# 2. Syntax check
ansible-playbook tests/deploy.yml -i tests/inventory.py --syntax-check

# 3. Test connectivity
ansible all -i tests/inventory.py -m ping

# 4. Dry run (check mode)
ansible-playbook tests/deploy.yml -i tests/inventory.py --check

# 5. Deploy
ansible-playbook tests/deploy.yml -i tests/inventory.py

# 6. With verbose output
ansible-playbook tests/deploy.yml -i tests/inventory.py -vv
```

## Check the Installation

If your Ansible role didn't fail during the play, your Horizon instance should be deployed.

To test it, run:

```bash
/opt/horizon/sbin/horizon-doctor
```

### Additional Verification Steps

```bash
# Check Horizon service status
sudo systemctl status horizon

# Verify firewall configuration
sudo firewall-cmd --list-all

# For HA: Check Akka cluster configuration
grep "AKKA_DISCOVERY_ENDPOINTS" /etc/default/horizon

# Check Horizon logs
sudo journalctl -u horizon -f
```

## Pre-Deployment Checklist

Before running the playbook, verify:

- [ ] All VMs are provisioned and accessible via SSH
- [ ] SSH keys are copied to all target nodes
- [ ] MongoDB is running and accessible
- [ ] MongoDB user is created with `dbOwner` role on the `horizon` database
- [ ] `mandatory_vars.yml` is configured with real values (no placeholders)
- [ ] MongoDB shell package URI matches your architecture (x86_64 vs aarch64)
- [ ] Horizon license file path is correct
- [ ] Ansible and ansible.posix collection are installed
- [ ] For RHEL 9: System is registered with subscription manager

## Author Information

If you have difficulties to use this role or modifications recommendations, please contact Evertrust.