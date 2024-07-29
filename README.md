Role Name
=========


Requirements
------------
To be able to use this role you have to previously provision 3 VMs running on CentOS/RHEL and meeting the requirements from the official EVERTRUST documentation : https://docs.evertrust.fr/horizon/install-guide/2.5/iaas/prerequisites. 
A root access to these VM is mandatory, as per a normal RPM install of Horizon. You will have to configure your Ansible playbook to use these accounts while playing the role.

A running instance of MongoDB is also necessary.
Moreover, you have to open the necessary flux on your VMs prior to this deployment, based on the official EVERTRUST documentation.

Concerning Ansible, it is necessary to : 
1. [Install the ansible.posix package](https://galaxy.ansible.com/ui/repo/published/ansible/posix/)
2. Define, for each host, the "host_number" variable with the values defined in the following table:

   | Host                        | Host_number's value |
   |-----------------------------|---------------------|
   | `1`                         | 0                   |
   | `2`                         | 1                   |
   | `3`                         | 2                   |

Role Variables
--------------
The following table regroups the data that you have to provide the Ansible role with for the deployment and configuration to work properly.

| Key                         | Value Type                             |
|-----------------------------|----------------------------------------|
| `play_http_secret_key`      | 32 characters string, no special character |
| `horizon_default_ssv_key`   | 32 characters string, no special character |
| `horizon_event_seal_secret` | 32 characters string, no special character |
| `horizon_pkg_uri`           | URL or file path where you store the Horizon RPM |
| `sonatype_username`         | Username to authenticate to this URL   |
| `sonatype_pwd`              | Password to authenticate to this URL   |
| `horizon_licence_src_path`  | Path to your Horizon license on your local machine |
| `mongodb_uri`               | URL or file path where you store the Horizon RPM |
| `mongo_org_repo_uri`        | URL or file path where you store the Mongosh RPM |
| `mongodb_hostname`          | Hostname of your MongoDB instance      |
| `horizon_hostname_node1`    | Hostname of your first Horizon VM      |
| `horizon_hostname_node2`    | Hostname of your second Horizon VM     |
| `horizon_hostname_node3`    | Hostname of your third Horizon VM      |

Overview
--------------
The previous table is not exhaustive but the excluded variables can be left as they are for a deployment with default values (valid in most cases). Note that the more variables you customize for your environment and needs, the less configuration will be necessary afterwards.


| Initial variables localisation                                                                     |
|----------------------------------------------------------------------------------------------------|
| `Horizon/defaults/main/default_values.yml` : variables that can optionally be changed.             |
| `Horizon/vars/main/mandatory_vars.yml` : list of variables that must be set before using the role. |


This role is composed of 4 steps played in order :

1. The download and install of the necessary packages to run Horizon.

2. The generation of certificates for Nginx if you didn’t configure the variables `horizon_csr`, `horizon_pem`, `horizon_key`, and `horizon_chain_pem`. If you did, this step copies the content of these variables to provide your web server.

If you want to use some previously created certificates for your Web servers, change the variable `horizon_generate_default_cert` to false and set the variables :

`horizon_csr`, `horizon_pem`, `horizon_key`, and `horizon_chain_pem`. With respectively the values of : a certificate signing request, the associated signed certificate, 
the key used to key this certificate and a bundle of the trust chain that signed it. 

##
3. The provisionnement of your Horizon licence and the different configuration files needed for Horizon to run properly, based on their respective templates.

4. The start of adequate services.

##
Additionally, a touchy and key element of the Horizon configuration is the Play variable “hosts allowed” in the horizon-extra.conf file. It configures the whitelist allowed to access Horizon. By default, only localhost and the content of "Horizon Hostname" are whitelisted.
Hence, we recommand to add the hostnames of all your nodes and the one of your load balancer.


Example Playbook
----------------

Here is a basic way of using this role : 

    - name: testPlaybook
      hosts: all
      roles:
        - role: Horizon
          tags: always



Author Information
------------------

If you have difficulties to use this role or modifications recommendations, please contact EVERTRUST. 

Check the install
------------------

If your Ansible role didn’t fail during the play, your Horizon HA should be deployed.
To test it, run :


    /opt/horizon/sbin/horizon-doctor  