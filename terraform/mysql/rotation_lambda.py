import json
import logging
import os
import secrets
import string

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def generate_password(length=32):
    """Generate a secure random password"""
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    password = []

    # Ensure at least one of each required character type
    password.append(secrets.choice(string.ascii_lowercase))
    password.append(secrets.choice(string.ascii_uppercase))
    password.append(secrets.choice(string.digits))
    password.append(secrets.choice(special_chars))

    # Fill the rest with random characters
    all_chars = string.ascii_letters + string.digits + special_chars
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def handler(event, context):
    """Lambda function to rotate RDS admin password"""
    logger.info(f"Received event: {json.dumps(event)}")

    # Get the secret ARN from environment variable
    secret_arn = os.environ.get("SECRET_ARN")
    if not secret_arn:
        raise ValueError("SECRET_ARN environment variable not set")

    # Get the secret name from the ARN
    secret_name = secret_arn.split(":")[-1]

    # Create Secrets Manager client
    secrets_client = boto3.client("secretsmanager")

    try:
        # Get current secret value
        response = secrets_client.get_secret_value(SecretId=secret_name)
        current_secret = json.loads(response["SecretString"])

        # Generate new password
        new_password = generate_password()

        # Update the secret with new password
        new_secret = current_secret.copy()
        new_secret["password"] = new_password

        # Update the secret
        secrets_client.put_secret_value(
            SecretId=secret_name, SecretString=json.dumps(new_secret)
        )

        logger.info(f"Successfully rotated password for secret: {secret_name}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Password rotation completed successfully",
                    "secretName": secret_name,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error rotating password: {str(e)}")
        raise e
