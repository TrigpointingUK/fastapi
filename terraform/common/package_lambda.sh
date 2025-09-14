#!/bin/bash
# Package Lambda function for secret rotation

# Create a temporary directory
mkdir -p lambda_package

# Copy the Python file
cp rotation_lambda.py lambda_package/index.py

# Install dependencies
cd lambda_package
pip install pymysql boto3 -t .

# Create the zip file
zip -r ../rotation_lambda.zip .

# Clean up
cd ..
rm -rf lambda_package

echo "Lambda package created: rotation_lambda.zip"
