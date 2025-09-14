#!/bin/bash

# Package the Lambda function for deployment
echo "Packaging Lambda function..."

# Create the zip file
zip rotation_lambda.zip rotation_lambda.py

echo "Lambda function packaged as rotation_lambda.zip"
