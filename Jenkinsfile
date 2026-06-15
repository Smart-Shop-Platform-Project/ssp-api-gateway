pipeline {
    agent any
    environment { AWS_REGION = 'us-east-1' }
    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Setup Terraform & Get ECR Repo') {
            steps {
                script {
                    dir('terraform') {
                        sh 'terraform init -backend-config="bucket=ssp-terraform-state-bucket" -backend-config="key=services/api-gateway/terraform.tfstate" -backend-config="region=${AWS_REGION}"'
                        sh 'terraform workspace select dev || terraform workspace new dev'
                        env.ECR_REPOSITORY_URL = sh(script: 'terraform output -raw ecr_repository_url', returnStdout: true).trim()
                    }
                }
            }
        }
        stage('Build and Push Docker Image') {
            steps {
                script {
                    def dockerImage = docker.build("ssp-api-gateway:${env.BUILD_NUMBER}", ".")
                    docker.withRegistry("https://${env.ECR_REPOSITORY_URL}", 'ecr:us-east-1') {
                        dockerImage.push("${env.BUILD_NUMBER}")
                        dockerImage.push("latest")
                    }
                }
            }
        }
        stage('Deploy to ECS') {
            steps {
                script {
                    dir('terraform') {
                        def imageUrl = "${env.ECR_REPOSITORY_URL}:${env.BUILD_NUMBER}"
                        sh "terraform apply -auto-approve -var=\"container_image=${imageUrl}\""
                    }
                }
            }
        }
    }
}
