#!/bin/bash

# Update system
yum update -y

# Install MySQL client
yum install -y mysql

# Install additional tools
yum install -y htop vim wget curl

# Install Docker (for potential containerized workloads)
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create a simple connection script to RDS
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

# Create a simple web server for testing
cat > /home/ec2-user/simple_web_server.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "webserver"}')
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Web Server Running</h1><p>This is the private web server instance.</p>')

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Server running at port {PORT}")
    httpd.serve_forever()
EOF

chmod +x /home/ec2-user/simple_web_server.py
chown ec2-user:ec2-user /home/ec2-user/simple_web_server.py

# Create a systemd service for the web server
cat > /etc/systemd/system/simple-webserver.service << 'EOF'
[Unit]
Description=Simple Web Server
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user
ExecStart=/usr/bin/python3 /home/ec2-user/simple_web_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the web server service
systemctl daemon-reload
systemctl enable simple-webserver
systemctl start simple-webserver

# Log the completion
echo "Web server setup completed at $(date)" >> /var/log/user-data.log
