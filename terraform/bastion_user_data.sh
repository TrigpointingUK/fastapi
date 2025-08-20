#!/bin/bash
dnf update -y

# Install MySQL client (available as mariadb-connector-c)
dnf install -y mariadb105

# Install useful tools
dnf install -y htop vim tmux jq wget curl

# Install MySQL utilities
dnf install -y mysql-common

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

# Create a schema export script
cat > /home/ec2-user/export-schema.sh << 'EOF'
#!/bin/bash
echo "Exporting database schema..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mysqldump -h ${db_endpoint} -u ${db_username} -p${db_password} \
  --no-data --routines --triggers --single-transaction \
  fastapi_staging > /home/ec2-user/schema_$TIMESTAMP.sql
echo "Schema exported to: schema_$TIMESTAMP.sql"
ls -la /home/ec2-user/schema_*.sql
EOF

chmod +x /home/ec2-user/export-schema.sh
chown ec2-user:ec2-user /home/ec2-user/export-schema.sh

# Create a sample data export script
cat > /home/ec2-user/export-sample.sh << 'EOF'
#!/bin/bash
echo "Exporting sample data (5 rows per table)..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mysqldump -h ${db_endpoint} -u ${db_username} -p${db_password} \
  --where="1 LIMIT 5" --single-transaction \
  fastapi_staging > /home/ec2-user/sample_$TIMESTAMP.sql
echo "Sample data exported to: sample_$TIMESTAMP.sql"
ls -la /home/ec2-user/sample_*.sql
EOF

chmod +x /home/ec2-user/export-sample.sh
chown ec2-user:ec2-user /home/ec2-user/export-sample.sh

# Create a database inspection script
cat > /home/ec2-user/inspect-db.sh << 'EOF'
#!/bin/bash
echo "=== DATABASE INSPECTION REPORT ==="
echo "Generated: $(date)"
echo ""

mysql -h ${db_endpoint} -u ${db_username} -p${db_password} fastapi_staging << 'SQL'
SELECT "=== TABLES ===" as '';
SHOW TABLES;

SELECT "=== TABLE STRUCTURES ===" as '';
SELECT table_name, table_rows, data_length, index_length 
FROM information_schema.tables 
WHERE table_schema = 'fastapi_staging' 
ORDER BY table_name;

SELECT "=== USERS TABLE STRUCTURE ===" as '';
DESCRIBE users;

SELECT "=== TLOG TABLE STRUCTURE ===" as '';
DESCRIBE tlog;

SELECT "=== INDEXES ===" as '';
SELECT table_name, index_name, column_name, seq_in_index
FROM information_schema.statistics 
WHERE table_schema = 'fastapi_staging'
ORDER BY table_name, index_name, seq_in_index;
SQL
EOF

chmod +x /home/ec2-user/inspect-db.sh
chown ec2-user:ec2-user /home/ec2-user/inspect-db.sh

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
