# SSP API Gateway

This service is the single, unified entry point for all client requests to the Smart Shop Platform. It is a critical component responsible for routing, security, and resilience. It is built with FastAPI and designed to run on AWS ECS Fargate.

## Core Responsibilities & Features

1.  **Dynamic Service Routing:**
    *   Acts as a reverse proxy, forwarding incoming requests to the appropriate downstream microservice (e.g., `/api/v1/product/*` is routed to the `ssp-product-service`).
    *   Service locations are not hardcoded; they are dynamically loaded from environment variables, allowing for flexible infrastructure.

2.  **Rate Limiting:**
    *   To protect backend services from being overwhelmed, the gateway implements a global rate limit.
    *   It uses the `slowapi` library to enforce a limit (e.g., 100 requests per minute per client IP), preventing abuse and ensuring fair usage.

3.  **Resilience (Automatic Retries):**
    *   The gateway improves system stability by automatically retrying requests to downstream services if they fail with transient network errors (e.g., `ConnectError`, `ReadTimeout`).
    *   It uses the `tenacity` library to perform retries with exponential backoff, giving a service time to recover.

4.  **Centralized Logging:**
    *   Provides a single point to log and inspect every incoming request to the platform.
    *   Uses structured JSON logging, which integrates seamlessly with AWS CloudWatch for powerful querying and monitoring.

5.  **Security (Future):**
    *   This service is the ideal place to implement centralized authentication logic. While currently forwarding requests, it would be enhanced to validate JWTs before routing to protected services.

## Architecture
- **Framework:** **FastAPI** for its high performance and async capabilities.
- **Deployment:** **AWS ECS Fargate** for serverless container orchestration.
- **Dependencies:**
    - `httpx`: For making asynchronous HTTP requests to downstream services.
    - `slowapi`: For rate limiting.
    - `tenacity`: For the retry mechanism.

## Local Development

1.  Create a virtual environment: `python3 -m venv venv`
2.  Activate it: `source venv/bin/activate`
3.  Install dependencies: `pip install -r requirements.txt`
4.  **Set Environment Variables:** The gateway needs to know where the other services are. For local testing, you would set these to point to the other services running on your machine.
    ```bash
    export AUTH_SERVICE_URL="http://localhost:8001"
    export PRODUCT_SERVICE_URL="http://localhost:8002"
    export ORDER_SERVICE_URL="http://localhost:8003"
    # ... and so on for other services
    ```
5.  Run the application:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
    You would then make all your requests to `http://localhost:8000`.
