#!/bin/bash
yum update -y

# Install MySQL client
yum install -y mysql

# Install useful tools
yum install -y htop vim tmux

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
