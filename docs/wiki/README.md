# MediaWiki Docker Image

This directory contains the Dockerfile and configuration for building a custom MediaWiki image with OpenID Connect authentication and AWS S3 storage support.

## Extensions Included

- **PluggableAuth** (REL1_43) - Pluggable authentication framework
- **OpenIDConnect** (REL1_43) - OpenID Connect authentication
- **AWS** - AWS S3 storage backend for file uploads

## Building the Image

The image is automatically built by GitHub Actions when changes are pushed to the `develop` or `main` branches:
- Changes to `develop` branch build a `develop` tagged image
- Changes to `main` branch build a `main` tagged image and `latest` tag

The image is published to: `ghcr.io/ianh/fastapi/mediawiki`

## Deployment

The image is deployed to ECS Fargate in the `common` infrastructure. The ECS task:
- Runs in private subnets with no public IP
- Connects to the shared RDS MySQL instance (`mediawiki` database)
- Mounts `LocalSettings.php` from AWS Secrets Manager
- Is accessible via the ALB at `wiki.trigpointing.uk`

## LocalSettings.php Configuration

The `LocalSettings.php` file is stored in AWS Secrets Manager and mounted into the container at runtime. To update it:

1. Use AWS Console or CLI to update the secret: `trigpointing-mediawiki-localsettings`
2. Restart the ECS service to pick up the new configuration

Example AWS CLI command:
```bash
aws secretsmanager update-secret --secret-id trigpointing-mediawiki-localsettings \
  --secret-string file://LocalSettings.php \
  --region eu-west-1
```

## Database Configuration

Database credentials are managed in the `terraform/mysql/` directory:
- Database name: `mediawiki`
- Database user: `mediawiki_user`
- Credentials stored in AWS Secrets Manager: `trigpointing-mediawiki-credentials`

## Manual Testing

To test the image locally:
```bash
docker build -t mediawiki-test .
docker run -p 8080:80 mediawiki-test
```

Note: You'll need to provide a `LocalSettings.php` file or mount one for the wiki to work properly.

## Security Notes

- Never commit `LocalSettings.php` to the repository
- Database credentials are automatically generated and stored in AWS Secrets Manager
- The ECS task runs with minimal IAM permissions
- All traffic goes through CloudFlare and the ALB with HTTPS
