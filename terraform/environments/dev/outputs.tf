output "resource_group_name" {
  value = module.resource_group.resource_group_name
}

output "resource_group_location" {
  value = module.resource_group.resource_group_location
}

output "resource_group_id" {
  value = module.resource_group.resource_group_id
}

output "vnet_name" {
  value = module.network.vnet_name
}

output "vnet_id" {
  value = module.network.vnet_id
}

output "aks_subnet_id" {
  value = module.network.aks_subnet_id
}

output "private_subnet_id" {
  value = module.network.private_subnet_id
}

output "log_analytics_workspace_id" {
  value = module.loganalytics.workspace_id
}

output "log_analytics_workspace_name" {
  value = module.loganalytics.workspace_name
}

output "acr_name" {
  value = module.acr.acr_name
}

output "acr_login_server" {
  value = module.acr.login_server
}

output "managed_identity_id" {
  value = module.managed_identity.identity_id
}

output "managed_identity_principal_id" {
  value = module.managed_identity.principal_id
}

output "aks_cluster_name" {
  value = module.aks.cluster_name
}

output "aks_cluster_id" {
  value = module.aks.cluster_id
}

output "keyvault_name" {
  value = module.keyvault.keyvault_name
}

output "keyvault_uri" {
  value = module.keyvault.vault_uri
}

output "private_dns_zone_id" {
  value = module.private_dns.private_dns_zone_id
}

output "storage_account_name" {
  value = module.storage.storage_account_name
}

output "storage_blob_endpoint" {
  value = module.storage.primary_blob_endpoint
}

output "application_insights_id" {
  value = module.application_insights.application_insights_id
}

output "application_insights_connection_string" {
  value     = module.application_insights.connection_string
  sensitive = true
}