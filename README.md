Evertrust Horizon
=================

Requirements
------------
To use this role, provision **EL9** VMs (RHEL, Rocky Linux or AlmaLinux) meeting the requirements from the official Evertrust documentation: https://docs.evertrust.fr/horizon/install-guide/2.10/iaas/prerequisites.
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
| **7626** | Akka Management (cluster discovery) | HA only; restricted to cluster IPs/CIDRs |
| **17355** | Akka/Pekko Artery (cluster communication) | HA only; restricted to cluster IPs/CIDRs |

**Note:** Port 9000 (Horizon application) is bound to `127.0.0.1` only and is NOT exposed externally. Nginx acts as a reverse proxy on port 443 (HTTPS only).

**Note on Akka/Pekko:** Horizon internally uses Pekko (the successor to Akka), but configuration variables maintain the `AKKA_*` naming convention for backwards compatibility with older Horizon versions. The functionality and port numbers remain the same.

**For MongoDB:** If managing the MongoDB VM separately, ensure port 27017 is open only to Horizon node IPs for security.

## Role Variables

The following table regroups the data that you have to provide the Ansible role with for the deployment and configuration to work properly.

**IMPORTANT:** Mandatory secrets must be provided before deployment unless `horizon_generate_missing_secrets: true` is explicitly set for an initial deployment. Other variables have safe defaults and can be overridden in the inventory.

The recommended approach is to export them as environment variables before running the playbook:

```bash
# Copy the example file and fill in your values
cp horizon.env.example horizon.env

# Export the variables
export $(grep -v '^#' horizon.env | xargs)
```

> **Note:** `horizon.env` is git-ignored. Never commit real credentials.

| Key | Value Type |
|-----|------------|
| `horizon_play_http_secret_key` | Required unless generation is explicitly enabled. Recommended: 128 random hexadecimal characters. |
| `horizon_default_ssv_key` | Required only before Horizon 2.8, unless generation is explicitly enabled. Recommended: 128 random hexadecimal characters. |
| `horizon_event_seal_secret` | Required unless generation is explicitly enabled. Recommended: 128 random hexadecimal characters. |
| `horizon_generate_missing_secrets` | Generate missing application secrets once (default: `false`); persist them root-only and reuse them on later runs. |
| `horizon_version` | Horizon version (default: `2.10.2`, overridable via `HORIZON_VERSION`) |
| `horizon_pkg_uri` / `horizon_pkg_checksum` | Horizon RPM URL and SHA-256. Override the version, URI and checksum together. |
| `horizon_repository_username` | Username to authenticate to the Evertrust repository |
| `horizon_repository_password` | Password to authenticate to the Evertrust repository |
| `horizon_tinkey_version` | Tinkey version (default: pinned to `1.13.0`) |
| `horizon_tinkey_pkg_uri` / `horizon_tinkey_pkg_checksum` | Tinkey RPM URL and SHA-256. Override them together with its version. |
| `horizon_cli_install` | Install the `horizon-cli` companion tool on the nodes (default: `true`, x86_64 only) |
| `horizon_cli_version` | Horizon CLI version (default: pinned to `1.17.1`) |
| `horizon_cli_pkg_uri` / `horizon_cli_pkg_checksum` | Horizon CLI RPM URL and SHA-256 (x86_64 only). Override them together with its version. |
| `horizon_licence_src_path` | Path to your Horizon license on your control machine |
| `horizon_mongodb_username` | MongoDB user pre-created on your MongoDB instance |
| `horizon_mongodb_password` | Password of the MongoDB user |
| `horizon_mongodb_uri` | MongoDB connection string (auto-built from username/password/hostname) |
| `horizon_mongodb_shell_package_uri` | URL where you store the Mongosh RPM (check architecture: x86_64 or aarch64) |
| `horizon_mongodb_hostname` | Hostname of your MongoDB instance |
| `horizon_mongodb_ip` | IP address of your MongoDB instance |
| `horizon_nodes` | List of Horizon nodes with hostname and IP (see below) |
| `horizon_akka_discovery_port` | Port for Akka cluster discovery (default: 7626) |
| `horizon_akka_artery_port` | Port for Akka/Pekko cluster communication (default: 17355) |
| `horizon_configure_firewall` | Set to `false` to skip firewall configuration (default: `true`) |
| `horizon_firewall_cluster_sources` | Explicit HA node IPs/CIDRs; facts are used when empty. Required if facts cannot provide routable addresses. |
| `horizon_extra_allowed_hosts` | Additional hosts allowed in Play filter, e.g. load balancer hostname (default: `[]`) |
| `horizon_tenants` | List of tenants (`name` + `hostname`) for multi-tenant deployments (default: `[]`, see Multi-Tenancy section) |
| `horizon_tenant_header_passthrough` | Allow clients to send their own `X-Tenant` header on the default vhost (default: `false`) |
| `horizon_licence_check` | Fail early if tenants are requested but the licence lacks the `multitenant` entitlement (default: `true`) |
| `horizon_nginx_ssl_verify_client` | TLS client-certificate request (default: `optional_no_ca`, needed for X.509 auth; set to `off` to avoid the browser certificate picker when unused) |
| `horizon_create_tenants` | Create the declared tenants through the root-scope API after startup (default: `true`) |
| `horizon_admin_username` / `horizon_admin_password` | API credentials for tenant creation; empty password = use the bootstrap password generated on first start |
| `horizon_tenant_default_certificate_limit` / `horizon_tenant_default_certificate_module` | Defaults for created tenants (`100` / `clm`), overridable per tenant entry |

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

The default configuration uses the architecture detected at runtime (`ansible_facts['architecture']`). The Horizon and Tinkey RPMs default to `noarch` and work on both architectures. The Horizon CLI RPM is only published for x86_64: on other architectures its installation is skipped with a notice.

## Overview

The previous table is not exhaustive but the excluded variables can be left as they are for a deployment with default values (valid in most cases). Note that the more variables you customize for your environment and needs, the less configuration will be necessary afterwards.

| Initial variables localisation |
|--------------------------------|
| `defaults/main/default_values.yml` : everything with a working default (versions, package URIs, ports, paths, tenancy...) — override only what you need |
| `defaults/main/mandatory_vars.yml` : what YOU must provide — secrets (via env vars, see `horizon.env.example`), cluster nodes, MongoDB location, licence path. Loaded after `default_values.yml`, so redefining any default here wins |

Environment variables are used by the supplied defaults for secrets and may also select the Horizon version. Any value can instead be supplied as an Ansible variable (inventory, Vault or extra-vars), which takes precedence. The role fails at the very start with the full list of missing secrets if any. Set `horizon_generate_missing_secrets: true` only for an initial deployment to generate missing application secrets. It writes 128-character hexadecimal values to `/etc/evertrust/horizon-generated-secrets.yml` (`root:root`, `0600`) on every Horizon node; save them immediately in the customer Vault and never commit that file.

**Tinkey & Java:** Tinkey is pinned to `1.13.0` by default. Its RPM declares no Java dependency. Horizon 2.10 no longer installs Java automatically, so the role installs `horizon_tinkey_java_package` (default: `java-17-openjdk-headless`) explicitly for Tinkey and the Horizon runtime.

**Horizon CLI:** Horizon CLI is pinned to `1.17.1` by default. Set `horizon_cli_install: false` to omit it, or override its version, RPM URI and checksum as a matching set.

This role is composed of the following steps played in order:

### 1. Package Installation

The download and install of the necessary packages to run Horizon, including:
- System dependencies (wget, nginx, postfix, firewalld, epel-release)
- Horizon RPM package
- Tinkey RPM package (required for Horizon >= 2.8, used for AES256 keyset encryption)
- Horizon CLI RPM package (companion automation tool, x86_64 only, disable with `horizon_cli_install: false`)
- MongoDB shell (mongosh)
- SELinux configuration if enforcing mode is detected

### 2. Certificate Generation

Nginx generates a self-signed certificate by default. To supply an existing certificate, set `horizon_generate_default_cert: false` and provide the **PEM content** of `horizon_key`, `horizon_pem`, and `horizon_chain_pem`; these are contents, not controller file paths. `horizon_csr` is optional and retained only as an operator reference.

By default (`horizon_generate_default_cert: true`), the role automatically generates self-signed SSL/TLS certificates for Nginx with the following specifications:

- **Key type**: RSA 4096-bit
- **Hashing algorithm**: SHA-256
- **Certificate location**: `/etc/nginx/ssl/`
- **Validity**: 365 days
- **Subject fields**: Configurable via variables in `default_values.yml` (country, organization, OU, CN)
- **SANs**: All node hostnames and all tenant FQDNs (`horizon_cert_san_hosts`)

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
- Generation of `/etc/default/horizon` with JVM, Play, MongoDB, and cluster settings
- Configuration of hosts.allowed whitelist (nodes, extra hosts, tenant FQDNs)
- Deployment of the role-managed nginx vhost configuration (default vhost + one vhost per tenant), replacing the symlink shipped by the RPM

### 5. Firewall Configuration

Automatic configuration of firewalld to open necessary ports:
- SSH (22) to prevent lockout
- HTTPS (443) for web access
- Akka/Pekko cluster ports (7626, 17355) for HA deployments only
- Can be disabled by setting `horizon_configure_firewall: false`

### 6. Service Management

The start of adequate services:
- Postfix service
- Horizon service
- Nginx service (with configuration test)

### Cluster Split-Brain Resolver (Pekko)

**IMPORTANT:** For High Availability deployments (2+ nodes), the role automatically configures the split-brain resolver using a MongoDB-based lease-majority strategy. Since Horizon 2.8, the application runs on **Pekko** (the successor of Akka), so the configuration namespace is `pekko.*`:

```hocon
pekko.cluster.split-brain-resolver {
    active-strategy = "lease-majority"
    lease-majority {
      lease-implementation = "lease.mongo"
    }
}
```

For Horizon < 2.8 the role falls back to the legacy `akka.cluster.split-brain-resolver` namespace. This configuration ensures proper cluster behavior during network partitions and prevents data inconsistency. It is automatically included in the `hosts_allowed.j2` template.

### Hosts Allowed Configuration

Additionally, a touchy and key element of the Horizon configuration is the Play variable "hosts allowed" in the horizon-extra.conf file. It configures the whitelist allowed to access Horizon.

The role automatically configures this whitelist to include:
- localhost
- All Horizon cluster node hostnames
- Any additional hosts defined in `horizon_extra_allowed_hosts` (e.g. load balancer hostname, `127.0.0.1` for local testing)
- All tenant FQDNs defined in `horizon_tenants`

This prevents "Host not allowed" errors when accessing Horizon through different hostnames.

## Multi-Tenancy (Horizon >= 2.9)

Horizon supports multi-tenant deployments when the licence carries the **`multitenant` entitlement**. Tenant selection is done through the `X-Tenant` HTTP header, which this role configures nginx to set based on the requested hostname (one vhost per tenant).

To deploy a multi-tenant instance, define your tenants:

```yaml
horizon_tenants:
  - name: tenant1
    hostname: tenant1.horizon.example.com
  - name: tenant2
    hostname: tenant2.horizon.example.com
```

The role then:
- Deploys one nginx vhost per tenant, setting `proxy_set_header X-Tenant "<name>"` so all requests reaching that FQDN are scoped to the tenant
- Keeps a default vhost (catch-all) serving the instance scope (administration)
- Strips any client-supplied `X-Tenant` header on the default vhost, so tenant selection can only happen through the dedicated vhosts (set `horizon_tenant_header_passthrough: true` to allow API clients to pass the header directly). The strip is applied even when no tenant is configured: with a multitenant licence Horizon honours the header, so it must never come from the client
- Adds every tenant FQDN to the Play `hosts.allowed` whitelist
- Includes every tenant FQDN in the SANs of the generated self-signed certificate

**Tenant creation is automated** (`horizon_create_tenants: true`): after the service answers, the role creates every tenant of `horizon_tenants` missing on the instance through the root-scope API (`POST /api/v1/security/tenants`), authenticated with `horizon_admin_password` or, by default, the bootstrap administrator password generated by Horizon on first start. Optional per-tenant keys: `description`, `certificate_limit`, `certificate_module` (`clm`/`pki`), `admin_password`. When the initial tenant administrator password is generated by Horizon, the role stores it on the first node in `/opt/horizon/var/run/tenant-<name>-adminPassword` (the creation response is the only place it ever appears).

**Root tenant URL**: the default vhost is a catch-all — any FQDN resolving to the nodes that is not declared as a tenant hostname lands on the root tenant (administration). Add such names (load-balancer FQDN, etc.) to `horizon_extra_allowed_hosts` so the Play host filter accepts them.

**Choosing the deployment mode** comes from the licence entitlement: the role decodes the ASN.1 licence container on the controller and identifies `multitenant`, even when `horizon_tenants` is initially empty. `horizon_tenants` only declares child tenants to configure and create. A tenant list with a single-tenant licence fails early. This remains a preflight: Horizon validates licence signature and validity itself. Set `horizon_licence_check: false` only for an explicitly accepted bypass.

**Prerequisites:**
- A licence with the `multitenant` entitlement (single-tenant licences ignore the `X-Tenant` header)
- DNS records (or load balancer config) pointing each tenant FQDN to the Horizon nodes
- If you bring your own certificate (`horizon_generate_default_cert: false`), it must cover all tenant FQDNs (SANs or wildcard)
- The controller must have OpenSSL when `horizon_licence_check: true` (default)

**Note:** if you add tenants after the initial deployment, re-run the role. If the self-signed certificate lacks a new FQDN SAN, the role stops rather than silently rotating trust. Replace it through the PKI process, or explicitly set `horizon_regenerate_self_signed_certificate_on_san_change: true` for a controlled self-signed renewal.

A **single-tenant** deployment is simply `horizon_tenants: []` (the default): only the default vhost is rendered, identical to the configuration shipped with the Horizon package.

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
- [ ] Secret keys (`HORIZON_PLAY_HTTP_SECRET_KEY`, `HORIZON_DEFAULT_SSV_KEY`, `HORIZON_EVENT_SEAL_SECRET`) are exported as environment variables
- [ ] MongoDB shell package URI matches your architecture (x86_64 vs aarch64)
- [ ] Horizon license file path is correct
- [ ] Ansible and ansible.posix collection are installed
- [ ] For RHEL 9: System is registered with subscription manager

## Uninstall

To completely remove Horizon from all nodes:

```bash
ansible-playbook tests/uninstall.yml -i tests/inventory.py
```

This will stop all services (Horizon, Nginx, Postfix), remove the Horizon, Tinkey, Horizon CLI and Mongosh packages, clean up all configuration files and firewall rules.

## Author Information

If you have difficulties to use this role or modifications recommendations, please contact Evertrust.
