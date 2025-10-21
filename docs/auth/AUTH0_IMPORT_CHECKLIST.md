# Auth0 Production Import Checklist

Use this checklist to track your progress through the Auth0 tenant import process.

## Pre-Import Setup

- [ ] **Created Terraform M2M Application**
  - [ ] Application name: "Terraform Management"
  - [ ] Type: Machine to Machine
  - [ ] Authorised for Auth0 Management API
  - [ ] ALL permissions granted
  - [ ] Client ID saved: `________________`
  - [ ] Client Secret saved: `________________`

- [ ] **Verified Tenant Information**
  - [ ] Tenant domain identified: `________________`
  - [ ] Tenant region confirmed: [ ] EU / [ ] US / [ ] AU / [ ] Other: `______`
  - [ ] Custom domain confirmed: `auth.trigpointing.uk`

- [ ] **Retrieved Existing M2M Secret**
  - [ ] Found existing M2M client name: `________________`
  - [ ] Client secret retrieved (or rotated): `________________`
  - [ ] Secret updated in AWS Secrets Manager (if rotated)

## Resource ID Collection

- [ ] **Installed Prerequisites**
  - [ ] `jq` installed (`sudo apt-get install jq`)
  - [ ] `curl` available
  - [ ] Auth0 credentials ready

- [ ] **Ran Resource ID Script**
  ```bash
  export AUTH0_DOMAIN="trigpointing.eu.auth0.com"
  export AUTH0_M2M_CLIENT_ID="<your_terraform_client_id>"
  export AUTH0_M2M_CLIENT_SECRET="<your_terraform_client_secret>"
  ./scripts/get-auth0-ids.sh > auth0-resource-ids.txt
  ```
  - [ ] Script ran successfully
  - [ ] Output saved to file
  - [ ] Output reviewed

- [ ] **Recorded Resource IDs**
  - [ ] Connection ID: `________________`
  - [ ] API Identifier: `________________`
  - [ ] M2M Client ID: `________________`
  - [ ] Swagger Client ID: `________________`
  - [ ] Website Client ID: `________________`
  - [ ] Android Client ID: `________________`
  - [ ] Forum Client ID (if exists): `________________`
  - [ ] Wiki Client ID (if exists): `________________`
  - [ ] Admin Role ID: `________________`
  - [ ] Post-Reg Action ID (if exists): `________________`
  - [ ] Post-Login Action ID (if exists): `________________`
  - [ ] Custom Domain ID: `________________`
  - [ ] M2M→API Grant ID: `________________`
  - [ ] M2M→Mgmt Grant ID: `________________`

## Configuration

- [ ] **Created Terraform Variables File**
  ```bash
  cd terraform/production
  cp auth0.auto.tfvars.template auth0.auto.tfvars
  ```
  - [ ] File created
  - [ ] `auth0_tenant_domain` filled in
  - [ ] `auth0_custom_domain` filled in
  - [ ] `auth0_terraform_client_id` filled in
  - [ ] `auth0_terraform_client_secret` filled in
  - [ ] `auth0_m2m_client_secret` filled in
  - [ ] File is gitignored (verify with `git status`)

- [ ] **Updated Import Script**
  - [ ] Edited `scripts/import-auth0-production.sh`
  - [ ] All resource ID variables filled in
  - [ ] Optional resources marked correctly (forum, wiki, actions)

## Import Execution

- [ ] **Terraform Initialised**
  ```bash
  cd terraform/production
  terraform init
  ```
  - [ ] No errors
  - [ ] Providers downloaded
  - [ ] Backend configured

- [ ] **Ran Import Script**
  ```bash
  ./scripts/import-auth0-production.sh
  ```
  - [ ] Connection imported
  - [ ] API resource server imported
  - [ ] API scopes imported
  - [ ] M2M client imported
  - [ ] Swagger client imported
  - [ ] Website client imported
  - [ ] Android client imported
  - [ ] Forum client imported (if exists)
  - [ ] Wiki client imported (if exists)
  - [ ] Connection clients imported
  - [ ] Client grants imported (both)
  - [ ] Admin role imported
  - [ ] Admin role permissions imported
  - [ ] Actions imported (if exist)
  - [ ] Trigger bindings imported (if exist)
  - [ ] Custom domain imported
  - [ ] DNS record imported
  - [ ] Prompt config imported
  - [ ] Branding imported
  - [ ] Tenant settings imported
  - [ ] Email provider imported (or skipped)
  - [ ] AWS IAM resources imported (if exist)

- [ ] **Import Summary**
  - Total resources attempted: `______`
  - Successfully imported: `______`
  - Skipped (optional): `______`
  - Failed: `______`

## Verification

- [ ] **Reviewed Terraform Plan**
  ```bash
  terraform plan
  ```
  - [ ] Plan generated without errors
  - [ ] Output saved/reviewed: `terraform plan > plan-output.txt`

- [ ] **Drift Analysis**
  - [ ] No changes needed ✅ (ideal)
  - [ ] Minor acceptable changes (list below)
  - [ ] Significant changes requiring review (list below)

  **Changes Found:**
  ```
  [List any resources showing drift here]
  
  
  
  ```

- [ ] **Drift Resolution**
  - [ ] Reviewed each change
  - [ ] Updated Terraform code to match reality (if needed)
  - [ ] Accepted Terraform changes (if appropriate)
  - [ ] Re-ran `terraform plan` after fixes
  - [ ] Plan now acceptable

## Pre-Apply Safety

- [ ] **User Backup Created**
  - [ ] Export command run: `auth0 users export --format ndjson > backup.ndjson`
  - [ ] Or manual export from dashboard completed
  - [ ] Backup file location: `________________`
  - [ ] Backup verified (file size > 0)

- [ ] **Safety Checks**
  - [ ] NO user deletions in plan
  - [ ] NO connection deletions in plan
  - [ ] NO database recreation in plan
  - [ ] NO client secret rotations (unless intended)
  - [ ] All changes reviewed and understood

- [ ] **Stakeholder Notification**
  - [ ] Team notified of upcoming change
  - [ ] Maintenance window scheduled (if needed)
  - [ ] Rollback plan documented

## Apply Changes

- [ ] **Created Execution Plan**
  ```bash
  terraform plan -out=tfplan
  ```
  - [ ] Plan file created
  - [ ] Plan reviewed one final time

- [ ] **Applied Changes**
  ```bash
  terraform apply tfplan
  ```
  - [ ] Apply completed successfully
  - [ ] No errors reported
  - [ ] Timestamp: `________________`

## Post-Apply Testing

- [ ] **Existing User Tests**
  - [ ] User can log in: `________________`
  - [ ] No password reset required
  - [ ] User metadata intact
  - [ ] User profile displays correctly

- [ ] **Legacy Integration Test**
  - [ ] `/v1/legacy/login` endpoint works
  - [ ] New users can be created via legacy flow
  - [ ] Users sync to Auth0 correctly

- [ ] **New User Registration Test**
  - [ ] Created test user: `________________`
  - [ ] Registration succeeded
  - [ ] Post-registration action fired (if configured)
  - [ ] FastAPI webhook received request (if configured)
  - [ ] User can log in immediately

- [ ] **Client Authentication Tests**
  - [ ] Website login works: `www.trigpointing.uk`
  - [ ] API M2M token generation works
  - [ ] Swagger OAuth2 works: `api.trigpointing.uk/docs`
  - [ ] Android app login works (if available)
  - [ ] Forum login works (if configured)
  - [ ] Wiki login works (if configured)

- [ ] **Token Verification**
  - [ ] Access tokens contain correct claims
  - [ ] Roles included in tokens (if configured)
  - [ ] Custom claims present (if configured)
  - [ ] Token expiry correct (24h)

- [ ] **Email Tests**
  - [ ] Password reset email sent successfully
  - [ ] Welcome email sent (if configured)
  - [ ] Verification email sent (if configured)
  - [ ] Emails have correct branding

## Monitoring & Validation

- [ ] **Checked Auth0 Logs**
  - [ ] No errors in last hour
  - [ ] Login attempts succeeding
  - [ ] Actions executing successfully (if configured)
  - [ ] No unusual activity

- [ ] **Application Monitoring**
  - [ ] FastAPI logs show successful Auth0 integration
  - [ ] No authentication errors
  - [ ] User endpoints responding correctly
  - [ ] Legacy login endpoint operational

- [ ] **24-Hour Check**
  - Date/Time: `________________`
  - [ ] No user complaints
  - [ ] No authentication errors
  - [ ] Monitoring shows normal operation

## Documentation & Cleanup

- [ ] **Updated Documentation**
  - [ ] Recorded actual tenant domain used
  - [ ] Documented any drift that was accepted
  - [ ] Noted any manual steps that were required
  - [ ] Updated team wiki/docs with new process

- [ ] **Secured Sensitive Files**
  - [ ] `auth0.auto.tfvars` not committed
  - [ ] `auth0-resource-ids.txt` deleted or secured
  - [ ] User backup stored securely
  - [ ] Terraform plan output cleaned up

- [ ] **Terraform State**
  - [ ] State file backed up
  - [ ] Remote state working (if used)
  - [ ] State lock functioning

## Success Criteria Met

- [ ] ✅ All resources imported successfully
- [ ] ✅ Terraform plan shows no unexpected changes
- [ ] ✅ Existing users can log in
- [ ] ✅ No password resets required
- [ ] ✅ Legacy login integration works
- [ ] ✅ All clients authenticate correctly
- [ ] ✅ Post-registration actions work (if configured)
- [ ] ✅ No errors in Auth0 logs
- [ ] ✅ Production operating normally

## Sign-Off

- **Import Started:** `________________`
- **Import Completed:** `________________`
- **Tested By:** `________________`
- **Approved By:** `________________`
- **Status:** [ ] Success / [ ] Partial / [ ] Rolled Back

## Notes

```
[Add any additional notes, issues encountered, or lessons learned]




```

---

## If Something Went Wrong

- [ ] **Issue Identified:** `________________`
- [ ] **Impact Assessment:** [ ] Critical / [ ] Major / [ ] Minor
- [ ] **Rollback Decision:** [ ] Yes / [ ] No
- [ ] **Rollback Executed:** `________________`
- [ ] **Post-Rollback Verification:** [ ] Complete
- [ ] **Root Cause:** `________________`
- [ ] **Prevention Steps:** `________________`

