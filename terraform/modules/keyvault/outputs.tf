output "keyvault_id" {
  value = azurerm_key_vault.this.id
}

output "keyvault_name" {
  value = azurerm_key_vault.this.name
}

output "vault_uri" {
  value = azurerm_key_vault.this.vault_uri
}