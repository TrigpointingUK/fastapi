# AWS X-Ray Tracing Setup

This document describes how to set up AWS X-Ray tracing for the FastAPI application.

## Overview

The application now includes comprehensive AWS X-Ray tracing support with:
- Automatic instrumentation for FastAPI, SQLAlchemy, Requests, and Boto3
- Custom middleware for detailed request/response tracing
- Database operation tracing
- Terraform-managed X-Ray sampling rules and IAM permissions

## Environment Variables

Add these to your `.env` file:

```bash
# X-Ray Configuration
XRAY_ENABLED=true
XRAY_SERVICE_NAME=trigpointing-api
XRAY_SAMPLING_RATE=0.1
XRAY_DAEMON_ADDRESS=127.0.0.1:2000  # Optional, for local development
XRAY_TRACE_HEADER=X-Amzn-Trace-Id
```

## Local Development

### Option 1: X-Ray Daemon (Recommended)

1. Install the X-Ray daemon:
   ```bash
   # On macOS
   brew install aws-xray-sdk

   # On Linux
   wget https://s3.us-east-2.amazonaws.com/aws-xray-assets.us-east-2/xray-daemon/aws-xray-daemon-linux-amd64.tar.xz
   tar -xzf aws-xray-daemon-linux-amd64.tar.xz
   ```

2. Start the daemon:
   ```bash
   ./xray -o -n eu-west-1
   ```

3. Set environment variables:
   ```bash
   export XRAY_ENABLED=true
   export XRAY_DAEMON_ADDRESS=127.0.0.1:2000
   ```

4. Run the FastAPI application:
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

### Option 2: Direct AWS Integration

1. Configure AWS credentials:
   ```bash
   aws configure
   ```

2. Set environment variables:
   ```bash
   export XRAY_ENABLED=true
   export AWS_REGION=eu-west-1
   ```

3. Run the application (traces will be sent directly to AWS X-Ray)

## Production Deployment

### Terraform Configuration

The monitoring Terraform module includes X-Ray resources:

```hcl
module "monitoring" {
  source = "./monitoring"

  # X-Ray configuration
  xray_sampling_rate = 0.1
  enable_xray_daemon_role = true
  enable_xray_daemon_logs = true
  log_retention_days = 14
}
```

### IAM Permissions

The application needs these IAM permissions for X-Ray:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
      ],
      "Resource": "*"
    }
  ]
}
```

## Monitoring and Observability

### X-Ray Console

1. Go to AWS X-Ray Console
2. Select "Service map" to see the service topology
3. Use "Traces" to view individual request traces
4. Check "Analytics" for performance insights

### Key Metrics

- **Latency**: Request duration and database query times
- **Error Rate**: HTTP error codes and exceptions
- **Throughput**: Requests per second
- **Dependencies**: Database and external service calls

### Sampling Rules

The Terraform configuration creates sampling rules:
- API endpoints: 10% sampling rate
- Web endpoints: 10% sampling rate
- Database operations: Traced automatically

## Troubleshooting

### Common Issues

1. **No traces appearing**: Check XRAY_ENABLED=true and AWS credentials
2. **High costs**: Reduce XRAY_SAMPLING_RATE
3. **Missing database traces**: Ensure SQLAlchemy instrumentation is enabled

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('aws_xray_sdk').setLevel(logging.DEBUG)
```

### Health Check

The `/health` endpoint shows tracing status:
```json
{
  "status": "healthy",
  "tracing": {
    "xray_enabled": true,
    "otel_enabled": true
  }
}
```

## Performance Impact

- **CPU**: ~2-5% overhead
- **Memory**: ~10-20MB additional usage
- **Network**: Minimal impact with batching
- **Storage**: Traces stored in X-Ray for 30 days (configurable)

## Cost Considerations

- **Sampling**: 10% default rate balances cost vs. visibility
- **Retention**: 30-day default retention
- **Pricing**: $5 per million traces recorded
- **Optimization**: Use sampling rules to reduce costs for high-traffic endpoints
