#!/bin/bash

# Update system
yum update -y

# Install MySQL client
yum install -y mysql

# Install additional tools
yum install -y htop vim wget curl

# Create a simple connection script
cat > /home/ec2-user/connect_to_db.sh << 'EOF'
#!/bin/bash
echo "Connecting to RDS database..."
echo "Host: ${db_endpoint}"
echo "Username: ${db_username}"
echo "Password: ${db_password}"
echo ""
echo "Use: mysql -h ${db_endpoint} -u ${db_username} -p"
echo "Enter password when prompted: ${db_password}"
echo ""
mysql -h ${db_endpoint} -u ${db_username} -p${db_password}
EOF

chmod +x /home/ec2-user/connect_to_db.sh
chown ec2-user:ec2-user /home/ec2-user/connect_to_db.sh

# Create a script to connect to the webserver
cat > /home/ec2-user/connect_to_webserver.sh << 'EOF'
#!/bin/bash
echo "To connect to the webserver, use:"
echo "ssh -i your-key.pem ec2-user@<webserver-private-ip>"
echo ""
echo "The webserver is in the private subnet and accessible via this bastion host."
EOF

chmod +x /home/ec2-user/connect_to_webserver.sh
chown ec2-user:ec2-user /home/ec2-user/connect_to_webserver.sh

# Log the completion
echo "Bastion host setup completed at $(date)" >> /var/log/user-data.log
