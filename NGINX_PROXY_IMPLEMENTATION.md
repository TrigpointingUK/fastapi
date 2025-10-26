# Nginx Reverse Proxy Implementation Summary

## Overview

Successfully implemented an nginx-based reverse proxy as an ECS Fargate service to forward traffic from the ALB to the legacy EC2 server (`i-02ea789e9d1265a51`). This allows `trigpointing.uk` to be pointed at the ALB while maintaining backward compatibility with the legacy infrastructure.

## Architecture

```
Cloudflare (HTTPS:443) → ALB
  ├─ trigpointing.uk/health (priority 300) → FastAPI [TEST RULE]
  ├─ api.trigpointing.uk (priority 200) → FastAPI
  ├─ forum.trigpointing.uk (priority 120) → phpBB
  ├─ wiki.trigpointing.uk (priority 124) → MediaWiki
  ├─ cache.trigpointing.uk (priority 125) → phpMyAdmin
  └─ trigpointing.uk/* (priority 990) → Nginx Proxy → Legacy Server (52.19.163.216)
```

## Files Created

### Terraform Module
- `terraform/modules/nginx-proxy/main.tf` - ECS task definition, service, auto-scaling, IAM policies
- `terraform/modules/nginx-proxy/variables.tf` - Input variables
- `terraform/modules/nginx-proxy/outputs.tf` - Module outputs

### Infrastructure Configuration
- `terraform/common/nginx-proxy.tf` - Target group, listener rule, SSM parameter, module instantiation
- `terraform/common/nginx-proxy-config.tpl` - Nginx configuration template

## Files Modified

### Cloudflare DNS
- `terraform/common/cloudflare.tf`
  - Added `cloudflare_record.root_domain` - Root domain (@) CNAME to ALB
  - Added `cloudflare_record.www` - WWW subdomain CNAME to ALB
  - Both use `allow_overwrite = true` to replace existing A record

### Security Groups
- `terraform/common/security.tf`
  - Added `aws_security_group.nginx_proxy_ecs` - Dedicated security group for nginx proxy
  - Allows ingress from ALB on port 80
  - Allows all egress (to reach legacy server via HTTPS)

### Production Test Rule
- `terraform/production/main.tf`
  - Added `aws_lb_listener_rule.test_health` - Routes trigpointing.uk/health to FastAPI
  - Priority 300 (higher than catch-all nginx proxy rule)
  - Allows testing FastAPI under production domain before full cutover

## Key Configuration Details

### Legacy Server
- **Instance ID**: `i-02ea789e9d1265a51`
- **Public IP**: `52.19.163.216`
- **Private IP**: `10.0.13.141`
- **VPC**: `vpc-0de7815a4b339c38d` (legacy VPC)
- **Region**: `eu-west-1`
- **Note**: Not managed by Terraform (data source only)

### Nginx Proxy
- **Container Image**: `nginx:alpine`
- **Resources**: 128 CPU units, 256 MB memory
- **Desired Count**: 1 (can scale to 3)
- **Health Check**: `/nginx-health` endpoint
- **Config Source**: AWS Systems Manager Parameter Store
- **Proxy Target**: `https://52.19.163.216`
- **SSL Verification**: Disabled (`proxy_ssl_verify off`) for legacy server

### SSL Certificate
- **Status**: Already configured ✓
- **Certificate**: Cloudflare origin certificate
- **Domains Covered**: `*.trigpointing.uk`, `trigpointing.uk`
- **Location**: `terraform/production/cloudflare-cert.auto.tfvars`

## Deployment Steps

### 1. Pre-Deployment Verification

```bash
# Verify legacy server is accessible
curl -I https://52.19.163.216

# Check current DNS
dig trigpointing.uk +short
```

### 2. Deploy Common Infrastructure

```bash
cd terraform/common
terraform init
terraform plan  # Review changes carefully
terraform apply
```

Expected resources to be created:
- SSM parameter for nginx config
- Target group for nginx proxy
- ALB listener rule (priority 990)
- ECS service with 1 task
- Security group for nginx proxy
- 2 Cloudflare DNS records (root + www)

### 3. Deploy Production Test Rule

```bash
cd terraform/production
terraform init
terraform plan  # Review changes
terraform apply
```

Expected resources to be created:
- ALB listener rule for `/health` test (priority 300)

### 4. Verify Deployment

```bash
# Check ECS service is running
aws ecs describe-services \
  --cluster trigpointing-cluster \
  --services trigpointing-nginx-proxy \
  --region eu-west-1

# Check target group health
aws elbv2 describe-target-health \
  --target-group-arn <nginx-proxy-target-group-arn> \
  --region eu-west-1

# View logs
aws logs tail /aws/ecs/trigpointing-nginx-proxy --follow --region eu-west-1
```

## Testing Strategy

### Phase 1: Test FastAPI Health Endpoint

Before DNS cutover, test the FastAPI health endpoint under the production domain:

```bash
# This should return FastAPI health response
curl https://trigpointing.uk/health

# Expected response:
{"status":"healthy"}
```

### Phase 2: Test Nginx Proxy (Pre-DNS Cutover)

Use `/etc/hosts` or curl host header override:

```bash
# Override DNS for testing
curl -H "Host: trigpointing.uk" https://<ALB-DNS-NAME>/

# Or add to /etc/hosts temporarily
echo "<ALB-IP> trigpointing.uk www.trigpointing.uk" | sudo tee -a /etc/hosts
```

Test various paths:
- `/` - Home page
- `/api/` - Legacy API endpoints
- `/images/` - Static content
- `/user/login` - Authentication flows

### Phase 3: DNS Cutover

The Cloudflare DNS records are already configured in Terraform. The `apply` will automatically update DNS from A record to CNAME.

**Rollback plan**: If issues arise, manually change Cloudflare DNS back to A record pointing to `52.19.163.216`

### Phase 4: Monitoring

```bash
# Monitor ALB access logs
aws logs tail /aws/elasticloadbalancing/trigpointing-alb --follow

# Monitor nginx proxy logs
aws logs tail /aws/ecs/trigpointing-nginx-proxy --follow

# Monitor legacy server logs (SSH to bastion, then legacy server)
ssh -i ~/.ssh/bastion.pem ec2-user@bastion.trigpointing.uk
ssh legacy-server
tail -f /var/log/httpd/access_log
```

## ALB Listener Rule Priorities

Current priority allocation:
- **100-199**: Reserved for future use
- **120**: forum.trigpointing.uk → phpBB
- **124**: wiki.trigpointing.uk → MediaWiki  
- **125**: cache.trigpointing.uk → phpMyAdmin
- **200**: api.trigpointing.uk → FastAPI
- **300**: trigpointing.uk/health → FastAPI (test rule)
- **990**: trigpointing.uk/* → Nginx proxy (catch-all)

## Migration Path Forward

Once nginx proxy is stable and serving production traffic:

1. **Identify specific paths to migrate** (e.g., `/api/v1/trigs`, `/api/v1/users`)
2. **Add higher priority listener rules** (e.g., priority 400-899)
3. **Implement new endpoints in FastAPI**
4. **Deploy and test incrementally**
5. **Eventually remove nginx proxy** when all paths are migrated

Example future listener rule:

```hcl
resource "aws_lb_listener_rule" "api_trigs" {
  listener_arn = data.terraform_remote_state.common.outputs.https_listener_arn
  priority     = 500

  action {
    type             = "forward"
    target_group_arn = module.target_group.target_group_arn
  }

  condition {
    host_header {
      values = ["trigpointing.uk"]
    }
  }

  condition {
    path_pattern {
      values = ["/api/v1/trigs*"]
    }
  }
}
```

## Important Notes

### VPC Peering Not Possible
- Legacy VPC (`vpc-0de7815a4b339c38d`) uses CIDR `10.0.0.0/16`
- New VPC (`vpc-059c258a05f9c2385`) uses CIDR `10.0.0.0/16`
- **Overlapping CIDRs prevent VPC peering**
- This is why we're using the proxy approach

### Nginx Configuration Management
- Nginx config is stored in SSM Parameter Store: `/trigpointing/nginx-proxy/config`
- Container fetches config at startup using AWS CLI
- To update config: Update SSM parameter, then restart ECS service
- Future enhancement: Consider using config files in S3 or EFS

### Security Considerations
- Nginx proxy uses `proxy_ssl_verify off` for legacy server (self-signed cert or no valid cert)
- All traffic from Cloudflare to ALB is HTTPS
- ALB to nginx proxy is HTTP (internal VPC traffic)
- Nginx proxy to legacy server is HTTPS (over public internet)

### Cost Impact
- Nginx proxy: ~$10-15/month (1 Fargate task, 128 CPU / 256 MB)
- NAT Gateway data transfer: ~$0.045/GB for proxy → legacy traffic
- Negligible ALB target group costs

## Troubleshooting

### Nginx proxy tasks not starting
```bash
# Check task logs
aws ecs describe-tasks --cluster trigpointing-cluster --tasks <task-id> --region eu-west-1

# Check SSM parameter exists
aws ssm get-parameter --name /trigpointing/nginx-proxy/config --region eu-west-1
```

### Target group shows unhealthy targets
```bash
# Check nginx container health
aws ecs execute-command --cluster trigpointing-cluster \
  --task <task-id> \
  --container trigpointing-nginx-proxy \
  --command "/bin/sh" \
  --interactive

# Inside container, test health endpoint
wget -O- http://localhost/nginx-health
```

### Legacy server not receiving traffic
```bash
# Check security group allows HTTPS from anywhere
aws ec2 describe-security-groups --group-ids sg-0593b5a17ef8459b3 --region eu-west-1

# Test connectivity from ECS task to legacy server
# (requires ECS Exec enabled)
curl -I https://52.19.163.216
```

### DNS not resolving correctly
```bash
# Check Cloudflare DNS records
dig trigpointing.uk +short
dig www.trigpointing.uk +short

# Should return Cloudflare IPs (proxied)
# Not ALB DNS directly
```

## Success Criteria

- ✓ Nginx proxy module created
- ✓ Infrastructure configured in common/
- ✓ Security groups configured
- ✓ Cloudflare DNS records configured
- ✓ SSL certificate already covers required domains
- ✓ Test health rule added to production

**Next steps**: Deploy and test!

