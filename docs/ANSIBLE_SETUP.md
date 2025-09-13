# Ansible Infrastructure Management

This document provides comprehensive instructions for managing the FastAPI infrastructure using Ansible.

## Overview

The Ansible setup is configured to manage three instance groups:
- **fastapi**: Both bastion and webserver instances
- **bastions**: Bastion host only (public subnet)
- **webservers**: Webserver instance only (private subnet, accessed via bastion)

## Prerequisites

### On Your Laptop

1. **Install Ansible**:
   ```bash
   # On Ubuntu/Debian
   sudo apt update && sudo apt install ansible

   # On macOS
   brew install ansible

   # On CentOS/RHEL
   sudo yum install ansible
   ```

2. **Verify Installation**:
   ```bash
   ansible --version
   ```

3. **SSH Key Setup**:
   Ensure your SSH key is properly configured:
   ```bash
   chmod 600 ~/.ssh/fastapi-bastion.pem
   ```

## Directory Structure

```
Ansible/
├── ansible.cfg              # Ansible configuration
├── inventory.yml            # Host inventory
├── group_vars/              # Group-specific variables
│   ├── fastapi.yml
│   ├── bastions.yml
│   └── webservers.yml
├── host_vars/               # Host-specific variables (if needed)
└── playbooks/               # Ansible playbooks
    ├── main.yml
    └── update-db-script.yml
```

## Inventory Configuration

The inventory is configured with:
- **Bastion**: Direct SSH access via public IP
- **Webserver**: SSH access via bastion proxy
- **SSH Key**: Uses `~/.ssh/fastapi-bastion.pem` for all connections
- **User**: `ec2-user` for all instances

## Basic Ansible Commands

### Test Connectivity

```bash
# Test connection to all hosts
ansible all -m ping

# Test connection to specific groups
ansible fastapi -m ping
ansible bastions -m ping
ansible webservers -m ping
```

### Run Playbooks

```bash
# Run main playbook on all hosts
ansible-playbook playbooks/main.yml

# Run main playbook on specific groups
ansible-playbook playbooks/main.yml --limit fastapi
ansible-playbook playbooks/main.yml --limit bastions
ansible-playbook playbooks/main.yml --limit webservers

# Run specific playbook
ansible-playbook playbooks/update-db-script.yml
```

### Ad-hoc Commands

```bash
# Check system information
ansible all -m setup -a "filter=ansible_distribution*"

# Update packages on all hosts
ansible all -m yum -a "name=* state=latest" --become

# Check disk usage
ansible all -m shell -a "df -h"

# Check running services
ansible all -m shell -a "systemctl list-units --type=service --state=running"
```

## Specific Use Cases

### 1. Initial Setup

After creating new instances, run the main playbook to set up basic configuration:

```bash
cd Ansible
ansible-playbook playbooks/main.yml
```

This will:
- Update MOTD on all instances
- Install MySQL client on all FastAPI instances
- Install common tools (htop, vim, curl, jq, awscli, python3, pip)
- Install boto3 for AWS integration

### 2. Update Database Connection Script

To update the database connection script to use AWS Secrets Manager:

```bash
cd Ansible
ansible-playbook playbooks/update-db-script.yml
```

This will:
- Install AWS CLI and jq on the bastion
- Create an updated database connection script that retrieves credentials from AWS Secrets Manager
- Create helper scripts for AWS CLI configuration

### 3. Install Additional Software

To install additional packages on specific groups:

```bash
# Install packages on bastion only
ansible bastions -m yum -a "name=tree state=present" --become

# Install packages on webserver only
ansible webservers -m yum -a "name=nginx state=present" --become

# Install packages on all FastAPI instances
ansible fastapi -m yum -a "name=git state=present" --become
```

### 4. Database Management

After updating the database connection script, you can connect to the database:

```bash
# SSH to bastion
ssh -i ~/.ssh/fastapi-bastion.pem ec2-user@3.9.71.10

# Run the updated connection script
./connect_to_db.sh
```

The script will:
- Retrieve credentials from AWS Secrets Manager
- Display connection information
- Connect to the RDS database

### 5. File Management

```bash
# Copy files to instances
ansible all -m copy -a "src=/path/to/local/file dest=/path/to/remote/file"

# Create directories
ansible all -m file -a "path=/opt/myapp state=directory" --become

# Set file permissions
ansible all -m file -a "path=/opt/myapp owner=ec2-user group=ec2-user mode=0755"
```

### 6. Service Management

```bash
# Start a service
ansible all -m systemd -a "name=nginx state=started enabled=yes" --become

# Stop a service
ansible all -m systemd -a "name=nginx state=stopped" --become

# Restart a service
ansible all -m systemd -a "name=nginx state=restarted" --become
```

## Troubleshooting

### Connection Issues

1. **SSH Key Permissions**:
   ```bash
   chmod 600 ~/.ssh/fastapi-bastion.pem
   ```

2. **Test SSH Connection**:
   ```bash
   # Test bastion connection
   ssh -i ~/.ssh/fastapi-bastion.pem ec2-user@3.9.71.10

   # Test webserver connection via bastion
   ssh -i ~/.ssh/fastapi-bastion.pem ec2-user@10.0.10.132
   ```

3. **Check Ansible Configuration**:
   ```bash
   ansible-config dump
   ```

### Common Issues

1. **Python Interpreter**: Ensure Python 3 is available on target hosts
2. **Sudo Access**: Use `--become` flag for tasks requiring root privileges
3. **Network Connectivity**: Ensure bastion can reach webserver via private network

### Debugging

```bash
# Run with verbose output
ansible-playbook playbooks/main.yml -v

# Run with extra verbose output
ansible-playbook playbooks/main.yml -vvv

# Check what would be changed without making changes
ansible-playbook playbooks/main.yml --check

# Run specific tasks
ansible-playbook playbooks/main.yml --tags "mysql"
```

## Security Considerations

1. **SSH Keys**: Keep your private key secure and never commit it to version control
2. **AWS Credentials**: Configure AWS CLI on instances securely
3. **Secrets Management**: Use AWS Secrets Manager for sensitive data
4. **Access Control**: Limit Ansible access to authorized users only

## Best Practices

1. **Idempotency**: Write playbooks that can be run multiple times safely
2. **Testing**: Test playbooks in a development environment first
3. **Documentation**: Keep playbooks and roles well-documented
4. **Version Control**: Keep all Ansible code in version control
5. **Backup**: Always backup before making significant changes

## Next Steps

1. Run the initial setup playbook
2. Update the database connection script
3. Test connectivity to all instances
4. Customize playbooks for your specific needs
5. Create additional roles for specific applications

For more information, see the [Ansible Documentation](https://docs.ansible.com/).
