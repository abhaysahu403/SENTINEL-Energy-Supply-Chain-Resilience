resource "azurerm_postgresql_flexible_server" "this" {

  name                = var.server_name
  resource_group_name = var.resource_group_name
  location            = var.location

  administrator_login    = var.admin_username
  administrator_password = var.admin_password

  version = "16"
  sku_name = "B_Standard_B1ms"

  storage_mb = 32768

  backup_retention_days = 7

  delegated_subnet_id = var.subnet_id

  private_dns_zone_id = var.private_dns_zone_id

  public_network_access_enabled = false

  zone = "1"

  tags = var.tags
}