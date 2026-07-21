# Terraform Infrastructure

This directory contains the Azure infrastructure as code using Terraform.

## Structure

```
terraform/
├── modules/           # Reusable Terraform modules
│   ├── resource-group/
│   ├── network/
│   ├── acr/
│   ├── aks/
│   ├── keyvault/
│   ├── storage/
│   ├── postgres/
│   ├── redis/
│   ├── servicebus/
│   ├── loganalytics/
│   ├── appinsights/
│   ├── monitor/
│   ├── managed-identity/
│   ├── role-assignments/
│   └── tags/
├── environments/      # Environment-specific configurations
│   ├── dev/
│   ├── qa/
│   └── prod/
├── scripts/           # Utility scripts
└── README.md
```

## Prerequisites

- Terraform >= 1.0.0
- Azure CLI
- Appropriate Azure subscription access

## Usage

```bash
# Initialize Terraform
cd terraform/environments/{environment}
terraform init

# Plan infrastructure changes
terraform plan

# Apply infrastructure changes
terraform apply
```

## Modules

Each module is self-contained with:
- `main.tf` - Resource definitions
- `variables.tf` - Input variables
- `outputs.tf` - Output values