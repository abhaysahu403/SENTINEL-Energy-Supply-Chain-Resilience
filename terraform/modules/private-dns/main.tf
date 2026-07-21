resource "azurerm_private_dns_zone" "this" {

  name                = var.dns_zone_name
  resource_group_name = var.resource_group_name

  tags = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "this" {

  name = "postgres-dns-link"

  resource_group_name = var.resource_group_name

  private_dns_zone_name = azurerm_private_dns_zone.this.name

  virtual_network_id = var.vnet_id

  registration_enabled = false

  tags = var.tags
}