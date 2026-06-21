import boto3
import os
from botocore.exceptions import ClientError


class Settings:
    def __init__(self):
        self.env = os.getenv("ENVIRONMENT", "dev")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.ssm = boto3.client("ssm", region_name=self.region)

        # Prefixes for your parameters (e.g., /ssp/dev/api-gateway/auth-url)
        self.param_prefix = f"/ssp/{self.env}/api-gateway"

    def get_parameter(self, name, secret=False):
        try:
            response = self.ssm.get_parameter(
                Name=f"{self.param_prefix}/{name}",
                WithDecryption=secret
            )
            return response["Parameter"]["Value"]
        except ClientError as e:
            print(f"Error fetching parameter {name}: {e}")
            return None


settings = Settings()

# Fetching details from SSM
SERVICE_URLS = {
    "auth": settings.get_parameter("auth-url"),
    "product": settings.get_parameter("product-url"),
    "order": settings.get_parameter("order-url"),
    "cart": settings.get_parameter("cart-url"),
    "payment": settings.get_parameter("payment-url"),
    "search": settings.get_parameter("search-url"),
}
API_GATEWAY_KEY = settings.get_parameter("api-key", secret=True)
