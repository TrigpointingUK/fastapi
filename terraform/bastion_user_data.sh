#!/bin/bash
dnf update -y

# Install MySQL client (available as mariadb-connector-c)
dnf install -y mariadb105

# Install useful tools
dnf install -y htop vim tmux

# Install and start SSM agent (should be pre-installed in AL2023)
dnf install -y amazon-ssm-agent
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Create a script for easy database connection
cat > /home/ec2-user/connect-db.sh << 'EOF'
#!/bin/bash
echo "Connecting to RDS database..."
mysql -h ${db_endpoint} -u ${db_username} -p${db_password} fastapi_staging
EOF

chmod +x /home/ec2-user/connect-db.sh
chown ec2-user:ec2-user /home/ec2-user/connect-db.sh

# Create a .my.cnf file for easy access
cat > /home/ec2-user/.my.cnf << 'EOF'
[client]
host=${db_endpoint}
user=${db_username}
password=${db_password}
database=fastapi_staging
EOF

chmod 600 /home/ec2-user/.my.cnf
chown ec2-user:ec2-user /home/ec2-user/.my.cnf

echo "Bastion host setup complete!" > /var/log/user-data.log
