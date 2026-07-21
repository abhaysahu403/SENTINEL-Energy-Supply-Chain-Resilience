resource "azurerm_monitor_diagnostic_setting" "this" {

  name                       = var.name
  target_resource_id         = var.target_resource_id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  dynamic "enabled_log" {
    for_each = var.enabled_logs

    content {
      category = enabled_log.value
    }
  }

  dynamic "metric" {
    for_each = var.enabled_metrics

    content {
      category = metric.value
      enabled  = true
    }
  }
}

module "aks_diagnostics" {

  source = "../../modules/monitor-diagnostics"

  name = "aks-diagnostics"

  target_resource_id = module.aks.aks_cluster_id

  log_analytics_workspace_id = module.loganalytics.workspace_id

  enabled_logs = [
    "kube-apiserver",
    "kube-audit",
    "cluster-autoscaler"
  ]
}

module "postgres_diagnostics" {

  source = "../../modules/monitor-diagnostics"

  name = "postgres-diagnostics"

  target_resource_id = module.postgresql.postgresql_server_id

  log_analytics_workspace_id = module.loganalytics.workspace_id

  enabled_logs = [
    "PostgreSQLLogs"
  ]
}

module "storage_diagnostics" {

  source = "../../modules/monitor-diagnostics"

  name = "storage-diagnostics"

  target_resource_id = module.storage.storage_account_id

  log_analytics_workspace_id = module.loganalytics.workspace_id

  enabled_logs = []
}

module "keyvault_diagnostics" {

  source = "../../modules/monitor-diagnostics"

  name = "keyvault-diagnostics"

  target_resource_id = module.keyvault.keyvault_id

  log_analytics_workspace_id = module.loganalytics.workspace_id

  enabled_logs = [
    "AuditEvent"
  ]
}

