variable "name" {
  type = string
}

variable "target_resource_id" {
  type = string
}

variable "log_analytics_workspace_id" {
  type = string
}

variable "enabled_logs" {
  type = list(string)
  default = []
}

variable "enabled_metrics" {
  type = list(string)
  default = ["AllMetrics"]
}