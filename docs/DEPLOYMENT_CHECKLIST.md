# Nginx Proxy Deployment Checklist

## Pre-Deployment Verification

- [ ] Review `NGINX_PROXY_IMPLEMENTATION.md` for full details
- [ ] Verify legacy server is responding: `curl -I https://52.19.163.216`
- [ ] Check current DNS: `dig trigpointing.uk +short` (should show 52.19.163.216)
- [ ] Ensure you have AWS credentials configured for eu-west-1
- [ ] Ensure you have Cloudflare API token configured

## Phase 1: Deploy Common Infrastructure

```bash
cd /home/ianh/dev/fastapi/terraform/common
```

- [ ] Run `terraform init` (if needed)
- [ ] Run `terraform plan` and review:
  - [ ] SSM parameter creation
  - [ ] Target group creation
  - [ ] ALB listener rule (priority 990)
  - [ ] Security group creation
  - [ ] ECS service creation
  - [ ] 2 Cloudflare DNS records (CNAME for @ and www)
- [ ] Run `terraform apply` and approve
- [ ] Wait for ECS service to stabilize (2-3 minutes)

### Verify Common Deployment

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster trigpointing-cluster \
  --services trigpointing-nginx-proxy \
  --region eu-west-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names trigpointing-nginx-proxy-tg \
    --region eu-west-1 \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text) \
  --region eu-west-1
```

- [ ] ECS service shows `runningCount == desiredCount`
- [ ] Target group shows healthy targets
- [ ] No errors in CloudWatch logs: `/aws/ecs/trigpointing-nginx-proxy`

## Phase 2: Deploy Production Test Rule

```bash
cd /home/ianh/dev/fastapi/terraform/production
```

- [ ] Run `terraform init` (if needed)
- [ ] Run `terraform plan` and review:
  - [ ] ALB listener rule for `/health` (priority 300)
- [ ] Run `terraform apply` and approve

### Test FastAPI Health Endpoint

- [ ] Test: `curl https://trigpointing.uk/health`
- [ ] Should return: `{"status":"healthy"}` or similar FastAPI response
- [ ] Verify in ALB access logs

## Phase 3: Test Nginx Proxy (Pre-Production)

**Note:** DNS has been updated by Terraform apply, so trigpointing.uk now points to ALB

- [ ] Test home page: `curl -I https://trigpointing.uk/`
- [ ] Should get response from legacy server (via proxy)
- [ ] Test various paths:
  - [ ] `/` - Home page
  - [ ] `/api/` - Legacy API
  - [ ] `/images/test.jpg` - Static content
  - [ ] `/user/login` - Authentication page
- [ ] Verify cookies and sessions work
- [ ] Test in browser: https://trigpointing.uk
- [ ] Check legacy server logs show requests coming from new IP ranges

## Phase 4: Monitor Production Traffic

```bash
# Monitor nginx proxy logs
aws logs tail /aws/ecs/trigpointing-nginx-proxy --follow --region eu-west-1

# Monitor ALB logs (if configured)
# Check CloudWatch metrics for target group health
```

- [ ] No 5xx errors in nginx proxy logs
- [ ] Target group remains healthy
- [ ] Response times acceptable (< 500ms)
- [ ] Legacy server handling requests normally

## Phase 5: Verify DNS Propagation

```bash
# Check DNS resolution
dig trigpointing.uk +short
dig www.trigpointing.uk +short

# Check from different locations
curl -I https://trigpointing.uk
curl -I https://www.trigpointing.uk
```

- [ ] DNS resolves to Cloudflare IPs (proxied)
- [ ] Both domains return 200 OK
- [ ] Content matches legacy server
- [ ] SSL certificate is valid

## Success Criteria

- ✓ Nginx proxy ECS service running with healthy targets
- ✓ ALB routes trigpointing.uk traffic to nginx proxy
- ✓ Nginx proxy successfully forwards to legacy server
- ✓ Legacy server receives and processes requests
- ✓ No user-facing errors or downtime
- ✓ Response times comparable to direct access
- ✓ Test endpoint (trigpointing.uk/health) returns FastAPI response

## Rollback Procedure

If critical issues occur:

1. **Immediate rollback** (Cloudflare UI):
   ```
   Go to Cloudflare Dashboard → trigpointing.uk → DNS
   Change @ record from CNAME to A record: 52.19.163.216
   Change www record from CNAME to A record: 52.19.163.216
   ```

2. **Terraform rollback** (after investigation):
   ```bash
   cd /home/ianh/dev/fastapi/terraform/common
   # Comment out the Cloudflare DNS records in cloudflare.tf
   terraform apply
   ```

3. **Full rollback** (if proxy needs to be removed):
   ```bash
   cd /home/ianh/dev/fastapi/terraform/common
   # Comment out all nginx-proxy resources
   terraform apply
   ```

## Monitoring Points

### Metrics to Watch
- ECS Service: Running count, CPU/Memory utilisation
- Target Group: Healthy host count, response time, error rate
- ALB: Request count, 4xx/5xx errors, target response time
- CloudWatch Logs: Error patterns in nginx proxy logs

### Alarms (Recommended)
- Target group unhealthy hosts > 0
- ALB 5xx error rate > 5%
- ECS service running count < desired count

## Post-Deployment Tasks

- [ ] Document any issues encountered
- [ ] Update monitoring dashboards
- [ ] Set up CloudWatch alarms for nginx proxy
- [ ] Plan path-based migration strategy
- [ ] Communicate success to team

## Notes

- DNS TTL: Cloudflare proxied records update instantly
- Legacy server: Remains completely untouched
- VPC CIDR overlap: 10.0.0.0/16 (prevents direct VPC peering)
- Nginx config updates: Modify SSM parameter, restart ECS service
- Cost: ~$10-15/month for nginx proxy ECS task

## Contact Points

- Legacy server: i-02ea789e9d1265a51 (52.19.163.216)
- VPC: vpc-0de7815a4b339c38d (legacy), vpc-059c258a05f9c2385 (new)
- Region: eu-west-1
- Documentation: NGINX_PROXY_IMPLEMENTATION.md

