module "resource_group" {
  source = "../../modules/resource-group"

  resource_group_name = var.resource_group_name
  location            = var.location

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
    Owner       = "Abhay Sahu"
  }
}

module "network" {

  source = "../../modules/network"

  resource_group_name = module.resource_group.resource_group_name

  location = module.resource_group.resource_group_location

  vnet_name = "sentinel-vnet"

  address_space = ["10.0.0.0/16"]

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "loganalytics" {
  source = "../../modules/loganalytics"

  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.resource_group_location

  workspace_name = "law-sentinel-dev"

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "acr" {

  source = "../../modules/acr"

  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.resource_group_location

  acr_name = "acrsentineldev2026"

  sku = "Basic"

  admin_enabled = false

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "managed_identity" {

  source = "../../modules/managed-identity"

  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.resource_group_location

  identity_name = "id-sentinel-dev"

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "aks" {

  source = "../../modules/aks"

  resource_group_name = module.resource_group.resource_group_name

  location = module.resource_group.resource_group_location

  cluster_name = "aks-sentinel-dev"

  dns_prefix = "sentinel"

  node_count = 1

  vm_size = "Standard_D2_v3"

  subnet_id = module.network.aks_subnet_id

  log_analytics_workspace_id = module.loganalytics.workspace_id

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

data "azurerm_client_config" "current" {}

module "keyvault" {

  source = "../../modules/keyvault"

  resource_group_name = module.resource_group.resource_group_name

  location = module.resource_group.resource_group_location

  keyvault_name = "kv-sentinel-dev-403"

  tenant_id = data.azurerm_client_config.current.tenant_id

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "role_assignments" {

  source = "../../modules/role-assignments"

  principal_id = module.managed_identity.principal_id

  acr_id = module.acr.acr_id

  keyvault_id = module.keyvault.keyvault_id
}

module "postgresql" {

  source = "../../modules/postgresql"

  resource_group_name = module.resource_group.resource_group_name

  location = module.resource_group.resource_group_location

  server_name = "pgsql-sentinel-dev"

  admin_username = "sentineladmin"

  admin_password = "ChangeMe123@"

  subnet_id = module.network.private_subnet_id

  private_dns_zone_id = module.private_dns.private_dns_zone_id

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}


module "private_dns" {

  source = "../../modules/private-dns"

  resource_group_name = module.resource_group.resource_group_name

  location = module.resource_group.resource_group_location

  dns_zone_name = "privatelink.postgres.database.azure.com"

  vnet_id = module.network.vnet_id

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}


module "storage" {

  source = "../../modules/storage"

  resource_group_name = module.resource_group.resource_group_name

  location = module.resource_group.resource_group_location

  storage_account_name = "stsentineldev2026"

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "application_insights" {

  source = "../../modules/application-insights"

  name = "appi-sentinel-dev"

  location = module.resource_group.resource_group_location

  resource_group_name = module.resource_group.resource_group_name

  workspace_id = module.loganalytics.workspace_id

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "aks_cpu_alert" {

  source = "../../modules/monitor-alerts"

  alert_name = "aks-high-cpu"

  resource_group_name = module.resource_group.resource_group_name

  target_resource_id = module.aks.cluster_id

  location = module.resource_group.resource_group_location

  threshold = 80
}

module "servicebus" {

  source = "../../modules/servicebus"

  namespace_name = "sb-sentinel-dev"

  resource_group_name = module.resource_group.resource_group_name

  location = module.resource_group.resource_group_location

  queue_name = "orders"

  topic_name = "notifications"

  subscription_name = "backend"

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

module "aks_nsg" {

  source = "../../modules/nsg"

  name = "nsg-aks-dev"

  location = module.resource_group.resource_group_location

  resource_group_name = module.resource_group.resource_group_name

  subnet_id = module.network.aks_subnet_id

  security_rules = [

    {
      name                       = "AllowHTTPS"
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "443"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    },

    {
      name                       = "AllowHTTP"
      priority                   = 110
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "80"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    }
  ]

  tags = {
    Project     = "SENTINEL"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}