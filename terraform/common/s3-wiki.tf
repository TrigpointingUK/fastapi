# S3 Bucket for MediaWiki file uploads and attachments
resource "aws_s3_bucket" "wiki" {
  bucket = "trigpointinguk-wiki"

  tags = {
    Name        = "trigpointinguk-wiki"
    Description = "MediaWiki file uploads and attachments"
  }
}

# Enable versioning for the wiki bucket
resource "aws_s3_bucket_versioning" "wiki" {
  bucket = aws_s3_bucket.wiki.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "wiki" {
  bucket = aws_s3_bucket.wiki.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access (allow public read via bucket policy)
resource "aws_s3_bucket_public_access_block" "wiki" {
  bucket = aws_s3_bucket.wiki.id

  block_public_acls       = true
  block_public_policy     = false # Allow bucket policy for public reads
  ignore_public_acls      = true
  restrict_public_buckets = false # Allow public reads via bucket policy
}

# Bucket policy to allow public read access to objects
resource "aws_s3_bucket_policy" "wiki_public_read" {
  bucket = aws_s3_bucket.wiki.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.wiki.arn}/*"
      }
    ]
  })
}

# CORS configuration for MediaWiki uploads
resource "aws_s3_bucket_cors_configuration" "wiki" {
  bucket = aws_s3_bucket.wiki.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["https://wiki.trigpointing.uk"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Lifecycle policy to manage old versions
resource "aws_s3_bucket_lifecycle_configuration" "wiki" {
  bucket = aws_s3_bucket.wiki.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# IAM policy for MediaWiki ECS task to access S3 bucket
resource "aws_iam_role_policy" "mediawiki_s3_access" {
  name = "${var.project_name}-mediawiki-s3-access"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetObjectVersion",
          "s3:DeleteObjectVersion"
        ]
        Resource = [
          aws_s3_bucket.wiki.arn,
          "${aws_s3_bucket.wiki.arn}/*"
        ]
      }
    ]
  })
}
