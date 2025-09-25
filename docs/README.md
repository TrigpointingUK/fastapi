### Orientation model (optional)

We use AWS Rekognition for content moderation and an optional ONNX model for image orientation (0/90/180/270) when scene cues are weak.

Generate the model locally (self-supervised rotations):

1. Put any photos under `res/orientation_data/` (subfolders are fine; images are auto-discovered).
2. Run:

```
make orientation-model
```

This exports `res/models/orientation_classifier.onnx`.

Enable in the API by setting env vars:

```
ORIENTATION_MODEL_ENABLED=true
ORIENTATION_MODEL_PATH=/models/orientation_classifier.onnx
ORIENTATION_MODEL_THRESHOLD=0.65
```

Bake the ONNX into the container (copy to `/models/`) or mount from EFS/S3.

# FastAPI Project Documentation

This directory contains all documentation for the FastAPI project, organized by category.

## Directory Structure

```
docs/
├── README.md                           # This file
├── ANSIBLE_SETUP.md                   # Ansible infrastructure management
├── database/                          # Database documentation
│   └── schema_documentation.md
├── infrastructure/                    # Infrastructure setup and configuration
│   ├── terraform-setup.md
│   ├── mysql-setup.md
│   ├── CLOUDFLARE_SETUP.md
│   └── INFRASTRUCTURE_CONFIGURATION_EXPLANATION.md
├── security/                          # Security configuration
│   └── SECURITY_CONFIGURATION_GUIDE.md
├── auth/                              # Authentication configuration
│   └── AUTH0_AUDIENCE_CONFIGURATION.md
└── migration/                         # Migration guides
    ├── MIGRATION_GUIDE.md
    └── legacy-migration.md
```

## Quick Start

### Infrastructure Management
- **[Ansible Setup](ANSIBLE_SETUP.md)** - Complete guide for managing infrastructure with Ansible
- **[Terraform Setup](infrastructure/terraform-setup.md)** - Infrastructure as code configuration

### Database
- **[Database Schema](database/schema_documentation.md)** - Complete database schema documentation
- **[MySQL Setup](infrastructure/mysql-setup.md)** - MySQL configuration and user management

### Security
- **[Security Configuration](security/SECURITY_CONFIGURATION_GUIDE.md)** - Security best practices and configuration

### Migration
- **[Migration Guide](migration/MIGRATION_GUIDE.md)** - Current migration procedures
- **[Legacy Migration](migration/legacy-migration.md)** - Legacy system migration guide

## Infrastructure Overview

The FastAPI project uses a modern, cloud-native architecture:

### AWS Services
- **ECS Fargate**: Container orchestration
- **RDS MySQL**: Managed database
- **ALB**: Application load balancer
- **Secrets Manager**: Credential management
- **CloudFlare**: DNS and CDN

### Infrastructure Management
- **Terraform**: Infrastructure as code
- **Ansible**: Configuration management
- **GitHub Actions**: CI/CD pipeline

### Security
- **Private subnets**: Database and application servers
- **Bastion host**: Secure access to private resources
- **Secrets Manager**: Encrypted credential storage
- **CloudFlare**: DDoS protection and SSL termination

## Getting Started

1. **Set up infrastructure**: Follow the [Terraform Setup](infrastructure/terraform-setup.md) guide
2. **Configure Ansible**: Follow the [Ansible Setup](ANSIBLE_SETUP.md) guide
3. **Set up database**: Follow the [MySQL Setup](infrastructure/mysql-setup.md) guide
4. **Configure security**: Follow the [Security Configuration](security/SECURITY_CONFIGURATION_GUIDE.md) guide

## Contributing

When adding new documentation:
1. Place files in the appropriate subdirectory
2. Update this README with the new file
3. Use descriptive filenames
4. Include a brief description in the file listing above

## Support

For questions or issues:
1. Check the relevant documentation first
2. Review the infrastructure setup guides
3. Check the migration guides for deployment issues
4. Contact the development team for additional support
