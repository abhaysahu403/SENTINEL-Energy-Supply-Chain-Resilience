variable "namespace_name" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "sku" {
  type    = string
  default = "Standard"
}

variable "queue_name" {
  type = string
}

variable "topic_name" {
  type = string
}

variable "subscription_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}