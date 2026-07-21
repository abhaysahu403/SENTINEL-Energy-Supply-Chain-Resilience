resource "azurerm_monitor_metric_alert" "cpu" {

  name                = var.alert_name
  resource_group_name = var.resource_group_name

  scopes = [
    var.target_resource_id
  ]

  description = "High CPU Alert"

  severity = var.severity

  frequency   = "PT5M"
  window_size = "PT5M"

  criteria {

    metric_namespace = "Microsoft.ContainerService/managedClusters"

    metric_name = "node_cpu_usage_percentage"

    aggregation = "Average"

    operator = "GreaterThan"

    threshold = var.threshold
  }
}