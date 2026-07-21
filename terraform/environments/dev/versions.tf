terraform {

  required_version = ">=1.7"

  backend "azurerm" {

    resource_group_name = "rg-terraform-state"

    storage_account_name = "stsentineltfstate01"

    container_name = "tfstate"

    key = "dev.terraform.tfstate"
  }

  required_providers {

    azurerm = {

      source = "hashicorp/azurerm"

      version = "~>4.0"

    }

  }

}