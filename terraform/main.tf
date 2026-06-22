terraform {
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
  backend "s3" {}
}

provider "aws" { region = var.aws_region }

data "aws_caller_identity" "current" {}

# IAM Policy for SSM Parameter Store Access
resource "aws_iam_policy" "ssm_policy" {
  name        = "ssp-api-gateway-ssm-policy-${var.environment}"
  description = "Allows the API Gateway to read its configuration from SSM"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = "ssm:GetParameter",
        Effect   = "Allow",
        # Grant access to all parameters under this gateway's specific path
        Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/ssp/${var.environment}/api-gateway/*"
      }
    ]
  })
}

data "terraform_remote_state" "base_infra" {
  backend = "s3"
  config = {
    bucket = "ssp-terraform-state-bucket"
    key    = "infrastructure/base/terraform.tfstate"
    region = var.aws_region
  }
}

module "ecr" {
  source          = "git::https://github.com/DeathGod049/terraform-infra-child.git//modules/ecr?ref=v0.1.0"
  repository_name = "ssp-api-gateway"
  environment     = var.environment
}

module "ecs_service" {
  source                  = "git::https://github.com/DeathGod049/terraform-infra-child.git//modules/ecs-service?ref=v0.1.0"
  service_name            = "ssp-api-gateway"
  environment             = var.environment
  aws_region              = var.aws_region
  cluster_id              = data.terraform_remote_state.base_infra.outputs.ecs_cluster_id
  vpc_id                  = data.terraform_remote_state.base_infra.outputs.vpc_id
  private_subnets         = data.terraform_remote_state.base_infra.outputs.private_subnets
  cloudmap_namespace_id   = data.terraform_remote_state.base_infra.outputs.cloudmap_namespace_id
  container_image         = var.container_image
  container_port          = 80

  # Attach the new SSM policy to the ECS task role
  task_policy_arns        = [aws_iam_policy.ssm_policy.arn]

  # Pass the ENVIRONMENT variable to the container
  environment_variables = [
    { name = "ENVIRONMENT", value = var.environment }
  ]
}
