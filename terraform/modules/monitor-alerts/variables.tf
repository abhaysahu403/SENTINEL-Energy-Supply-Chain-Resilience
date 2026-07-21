variable "alert_name" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "target_resource_id" {
  type = string
}

variable "location" {
  type = string
}

variable "severity" {
  default = 2
}

variable "threshold" {
  default = 80
}