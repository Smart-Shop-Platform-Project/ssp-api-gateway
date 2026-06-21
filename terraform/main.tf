terraform {
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
  backend "s3" {}
}
provider "aws" { region = var.aws_region }
data "terraform_remote_state" "base_infra" {
  backend = "s3"
  config = {
    bucket = "ssp-terraform-state-bucket-kuntal2098"
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
  source              = "git::https://github.com/DeathGod049/terraform-infra-child.git//modules/ecs-service?ref=v0.1.0"
  service_name        = "ssp-api-gateway"
  environment         = var.environment
  cluster_id          = data.terraform_remote_state.base_infra.outputs.ecs_cluster_id
  vpc_id              = data.terraform_remote_state.base_infra.outputs.vpc_id
  private_subnets     = data.terraform_remote_state.base_infra.outputs.private_subnets
  container_image     = var.container_image
  container_port      = 80
  environment_variables = [
    { name = "AUTH_SERVICE_URL", value = "http://ssp-auth-service.local:80" },
    { name = "PRODUCT_SERVICE_URL", value = "http://ssp-product-service.local:80" },
    { name = "ORDER_SERVICE_URL", value = "http://ssp-order-service.local:80" },
    { name = "CART_SERVICE_URL", value = "http://ssp-cart-service.local:80" },
    { name = "PAYMENT_SERVICE_URL", value = data.terraform_remote_state.base_infra.outputs.payment_lambda_url },
    { name = "SEARCH_SERVICE_URL", value = "http://ssp-search-service.local:80" }
  ]
}
