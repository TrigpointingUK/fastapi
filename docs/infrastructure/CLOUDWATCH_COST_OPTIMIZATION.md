# CloudWatch Cost Optimisation

**Date:** 27 October 2025  
**Objective:** Reduce CloudWatch costs (approximately 40% of monthly AWS spend) while maintaining basic monitoring for day-to-day troubleshooting and autoscaling capabilities.

## Summary of Changes

This document outlines the CloudWatch cost optimisations implemented to significantly reduce monitoring costs whilst preserving essential monitoring capabilities for troubleshooting and autoscaling.

### 1. **Disabled ECS Container Insights** ✅ (HIGHEST IMPACT)

**File:** `terraform/common/ecs.tf`

**Change:**
```hcl
setting {
  name  = "containerInsights"
  value = "disabled"  # Changed from "enabled"
}
```

**Impact:**
- **Cost Reduction:** ~70-80% of CloudWatch costs
- Container Insights charges for custom metrics at $0.30 per metric per month
- Typical ECS cluster with 5-10 services can generate 100+ custom metrics
- **Monthly Savings:** Estimated £50-150 depending on cluster size

**What You Keep:**
- Basic ECS metrics (CPU, memory utilisation) remain available at no extra cost
- These metrics are sufficient for autoscaling policies
- CloudWatch Logs for application output still function normally

**What You Lose:**
- Task-level CPU/memory metrics (only service-level remains)
- Network metrics per task
- Storage metrics per task
- Enhanced Container Insights dashboard widgets

### 2. **Reduced Log Retention from 30 Days to 7 Days** ✅

**Files Changed:**
- `terraform/production/main.tf` (30 → 7 days)
- `terraform/staging/main.tf` (14 → 7 days)
- `terraform/modules/nginx-proxy/main.tf` (30 → 7 days)
- `terraform/modules/phpbb/main.tf` (30 → 7 days)
- `terraform/modules/mediawiki/main.tf` (30 → 7 days)
- `terraform/modules/phpmyadmin/main.tf` (14 → 7 days)
- `terraform/common/valkey.tf` (already 7 days)

**Impact:**
- **Cost Reduction:** ~15-25% of CloudWatch costs
- CloudWatch Logs charges for storage beyond 7 days
- Pricing: $0.03 per GB per month for storage
- **Monthly Savings:** Estimated £10-30 depending on log volume

**Rationale:**
- You indicated logs are rarely used beyond the last week
- 7 days provides adequate time for investigating recent issues
- Critical incidents should be investigated within a week
- For compliance/audit requirements, logs can be exported to S3 for long-term archival at much lower cost

### 3. **Disabled RDS Enhanced Monitoring** ✅

**File:** `terraform/common/rds.tf`

**Change:**
```hcl
monitoring_interval = 0  # Changed from 60 (disabled)
```

**Impact:**
- **Cost Reduction:** ~5-10% of CloudWatch costs
- Enhanced Monitoring at 60-second granularity: $0.50/instance/month
- Enhanced Monitoring disabled: $0.00/instance/month
- **Monthly Savings:** ~£0.50 per RDS instance (~£6/year)

**Trade-offs:**
- No OS-level RDS metrics (memory, swap, processes)
- CloudWatch basic metrics (1-minute intervals) still available:
  - CPU utilisation
  - Database connections
  - Free storage space
  - Read/Write IOPS
  - Network throughput
- These basic metrics are sufficient for most troubleshooting
- If you need detailed OS metrics, you can temporarily re-enable by setting to 60

**To Re-enable:** Set `monitoring_interval = 60` if you need detailed OS-level metrics for diagnostics

### 4. **Already Optimised (No Changes Needed)** ✅

The following cost optimisations were already in place:

#### Synthetic Canaries - DISABLED
- All canary resources in `terraform/monitoring/canaries.tf` are commented out
- Canaries cost ~$0.0012 per run + Lambda execution time
- Running hourly = ~$0.87/month per canary (4 canaries = ~£3.50/month)

#### CloudWatch Alarms - DISABLED
- All alarm resources in `terraform/monitoring/alarms.tf` are commented out
- Alarms cost $0.10 per alarm per month
- You had 4 alarms configured (£0.40/month saved)

#### CloudWatch Dashboards - NONE CONFIGURED
- Custom dashboards cost $3 per dashboard per month
- No dashboards found in the Terraform configuration

#### ALB Access Logs - NOT ENABLED
- Access logs can be expensive for high-traffic sites
- Not enabled in `terraform/common/alb.tf`

#### VPC Flow Logs - NOT ENABLED
- No VPC Flow Logs found in the configuration
- Flow Logs can add significant costs for high-throughput VPCs

#### RDS Performance Insights - DISABLED
- `db_performance_insights_enabled = false` (default)
- Performance Insights costs $0.10 per vCPU per month beyond 7-day retention
- Keeping this disabled

## Cost Impact Summary

| Optimisation | Monthly Savings (Est.) | Annual Savings (Est.) |
|--------------|------------------------|----------------------|
| Container Insights | £50-150 | £600-1,800 |
| Log Retention (30→7 days) | £10-30 | £120-360 |
| RDS Enhanced Monitoring | £0.50 | £6 |
| **Total Estimated Savings** | **£60-180** | **£726-2,166** |

**Note:** Actual savings depend on:
- Number of ECS tasks and services
- Log volume (GB per day)
- Number of custom metrics used
- CloudWatch API call frequency

If CloudWatch was 40% of your AWS bill, these optimisations could reduce your **total AWS costs by 25-35%**.

## What Monitoring Remains Available

### ECS Monitoring
- ✅ Service-level CPU utilisation (for autoscaling)
- ✅ Service-level memory utilisation (for autoscaling)
- ✅ Application logs (7-day retention)
- ✅ Task health checks
- ❌ Task-level granular metrics
- ❌ Network metrics per task

### RDS Monitoring
- ✅ Standard CloudWatch metrics (1-minute intervals)
  - CPU Utilisation
  - Database Connections
  - Free Storage Space
  - Read/Write IOPS
  - Network Throughput
- ✅ Slow query logs (still enabled in parameter group)
- ❌ Enhanced Monitoring (disabled to save costs)
  - OS-level metrics (memory, swap, processes)
- ❌ Performance Insights (not enabled)

### Application Logs
- ✅ All service logs available for 7 days
- ✅ Real-time log streaming
- ✅ CloudWatch Logs Insights queries
- ❌ Historical logs beyond 7 days

## Autoscaling Impact

**No impact on autoscaling responsiveness.** The autoscaling policies use:
- ECS Service Average CPU Utilisation
- ECS Service Average Memory Utilisation

These metrics are:
1. **Free** - included with ECS (no Container Insights needed)
2. **1-minute resolution** - unchanged
3. **Available regardless of Container Insights**

Your autoscaling configuration remains:
- `scale_in_cooldown = 300s` (5 minutes)
- `scale_out_cooldown = 60s` (1 minute)

This means the system will still react to traffic spikes within 1-2 minutes for scale-out.

## Recommendations for Further Optimisation

If you need additional savings:

### 1. Reduce Log Retention to 3 Days
- Change: `retention_in_days = 3`
- Additional savings: ~£5-10/month
- Trade-off: Less time to investigate issues

### 2. Re-enable RDS Enhanced Monitoring if Needed
- Change: `monitoring_interval = 60`
- Additional cost: ~£0.50/month
- Benefit: Get OS-level RDS metrics (memory, swap, processes)

### 3. Export Logs to S3 for Long-Term Storage
- Use CloudWatch Logs subscription filters to export to S3
- S3 Standard storage: $0.023/GB (80% cheaper than CloudWatch)
- S3 Glacier Deep Archive: $0.00099/GB (99% cheaper!)
- Useful for compliance/audit requirements

### 4. Implement Log Sampling
- Modify application logging to sample non-error logs
- Send only 10% of INFO logs, 100% of ERROR logs
- Can reduce log volume by 50-70%

### 5. Use CloudWatch Logs Insights Instead of Dashboards
- Query logs on-demand rather than maintaining dashboards
- Save $3/dashboard/month

## Deployment Instructions

### 1. Review Changes
```bash
cd terraform/common
terraform plan
```

### 2. Apply to Staging First
```bash
cd terraform/staging
terraform plan
terraform apply
```

### 3. Monitor for 48 Hours
- Verify autoscaling still works correctly
- Check that logs are available for troubleshooting
- Confirm no alerts are missing

### 4. Apply to Production
```bash
cd terraform/production
terraform plan
terraform apply
```

### 5. Update Common Infrastructure
```bash
cd terraform/common
terraform plan
terraform apply
```

**⚠️ Important:** The ECS cluster change (Container Insights) requires updating the common infrastructure, which is shared across all environments. Ensure this is deployed carefully.

## Monitoring the Cost Reduction

After applying these changes, monitor your AWS Cost Explorer:

1. Navigate to AWS Cost Explorer
2. Filter by Service: "CloudWatch"
3. Set granularity to "Daily"
4. Compare costs before/after deployment

**Expected timeline for cost reduction:**
- **Immediate:** Container Insights (within 24 hours)
- **1-7 days:** Log retention (as old logs expire)
- **30 days:** Full monthly savings visible

## Rollback Instructions

If you need to restore previous monitoring levels:

### Restore Container Insights
```hcl
# terraform/common/ecs.tf
setting {
  name  = "containerInsights"
  value = "enabled"
}
```

### Restore Log Retention
```hcl
# Change all log groups back to:
retention_in_days = 30
```

### Re-enable RDS Enhanced Monitoring
```hcl
# terraform/common/rds.tf
monitoring_interval = 60  # Or 30, 15, 10, 5, 1 for more frequent monitoring
```

Then run `terraform apply` in the respective directories.

## Questions & Answers

### Q: Will autoscaling still work?
**A:** Yes, autoscaling uses basic ECS metrics that are always available for free.

### Q: Can I still troubleshoot production issues?
**A:** Yes, you have 7 days of logs and all standard CloudWatch metrics available.

### Q: What if I need historical data beyond 7 days?
**A:** For specific investigations, you can export logs to S3 before they expire. For ongoing needs, implement a CloudWatch Logs subscription filter to automatically export to S3.

### Q: Will this affect my ability to debug issues?
**A:** Not significantly. Most debugging uses recent logs (past 24-48 hours). The 7-day retention provides ample time to investigate issues after they occur.

### Q: Can I re-enable Container Insights temporarily?
**A:** Yes, you can enable it through the AWS Console without Terraform changes if you need detailed metrics for a specific investigation. However, be aware that it will start charging immediately.

### Q: Will this affect health checks or uptime monitoring?
**A:** No, ECS health checks are independent of CloudWatch Container Insights. Your services will continue to be monitored for health.

## Contact & Support

If you have questions or encounter issues after deploying these changes, please review the Terraform plan output carefully before applying, and test in staging first.

---

**Document Version:** 1.0  
**Last Updated:** 27 October 2025  
**Author:** Claude (AI Assistant) with ianh

