# DMS (Database Migration Service) Setup

This document explains how to set up DMS to replicate data from your legacy EC2 MySQL instance to the new RDS database.

## Prerequisites

1. **Legacy MySQL Server Details:**
   - IP address or hostname
   - Port (usually 3306)
   - Username and password
   - Database name

2. **Network Access:**
   - DMS needs to connect to both legacy EC2 and new RDS
   - Legacy EC2 needs to allow inbound MySQL connections from DMS

## Security Group Configuration

### Current Setup
- ✅ **RDS Security Group**: Allows MySQL access from DMS
- ✅ **DMS Security Group**: Allows outbound MySQL to both RDS and legacy EC2
- ⚠️ **Legacy EC2**: Needs to allow inbound MySQL from DMS

### Legacy EC2 Security Group Update

You need to add an inbound rule to your legacy EC2's security group:

```bash
# Get the DMS security group ID
aws ec2 describe-security-groups \
  --group-names fastapi-dms-sg \
  --region eu-west-2 \
  --query 'SecurityGroups[0].GroupId' \
  --output text

# Add inbound rule to legacy EC2 security group
aws ec2 authorize-security-group-ingress \
  --group-id <LEGACY_EC2_SECURITY_GROUP_ID> \
  --protocol tcp \
  --port 3306 \
  --source-group <DMS_SECURITY_GROUP_ID> \
  --region <LEGACY_EC2_REGION>
```

## DMS Configuration

### 1. Set Variables

Create a `terraform.tfvars` file or set environment variables:

```bash
# Legacy MySQL details
export TF_VAR_legacy_mysql_host="your-legacy-ec2-ip-or-hostname"
export TF_VAR_legacy_mysql_username="your-mysql-username"
export TF_VAR_legacy_mysql_password="your-mysql-password"
export TF_VAR_legacy_mysql_database="your-database-name"
```

### 2. Deploy DMS Infrastructure

```bash
cd terraform/common
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### 3. Start Replication

```bash
# Start the replication task
aws dms start-replication-task \
  --replication-task-arn "arn:aws:dms:eu-west-2:ACCOUNT:task:fastapi-replication-task" \
  --start-replication-task-type start-replication \
  --region eu-west-2
```

## Monitoring

### Check Replication Status

```bash
# List replication tasks
aws dms describe-replication-tasks --region eu-west-2

# Check specific task status
aws dms describe-replication-tasks \
  --replication-task-arn "arn:aws:dms:eu-west-2:ACCOUNT:task:fastapi-replication-task" \
  --region eu-west-2
```

### CloudWatch Logs

DMS logs are available in CloudWatch:
- Log Group: `/aws/dms/task/fastapi-replication-task`
- Log Stream: `DMS-Task-Instance-<instance-id>`

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check security groups and network connectivity
2. **Authentication Failed**: Verify credentials and user permissions
3. **Replication Stopped**: Check CloudWatch logs for errors

### Testing Connectivity

```bash
# Test from bastion to legacy MySQL
mysql -h <legacy-ec2-ip> -u <username> -p<password> <database>

# Test from bastion to new RDS
mysql -h <rds-endpoint> -u admin -p<admin-password> fastapi_common
```

## Cost Considerations

- **DMS Instance**: ~$0.10/hour for t3.micro
- **Data Transfer**: Free within same region
- **Storage**: 20GB allocated (adjustable)

## Cleanup

After successful migration:

```bash
# Stop replication task
aws dms stop-replication-task \
  --replication-task-arn "arn:aws:dms:eu-west-2:ACCOUNT:task:fastapi-replication-task" \
  --region eu-west-2

# Destroy DMS infrastructure
terraform destroy -target=aws_dms_replication_task.main
terraform destroy -target=aws_dms_replication_instance.main
```
