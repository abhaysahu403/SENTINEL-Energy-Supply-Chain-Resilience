output "namespace_id" {
  value = azurerm_servicebus_namespace.this.id
}

output "namespace_name" {
  value = azurerm_servicebus_namespace.this.name
}

output "queue_name" {
  value = azurerm_servicebus_queue.this.name
}

output "topic_name" {
  value = azurerm_servicebus_topic.this.name
}