output "api_url" {
  value = "http://localhost:${local.api_port}"
}

output "ui_url" {
  value = "http://localhost:${local.ui_port}"
}

output "network_name" {
  value = docker_network.group.name
}

output "volume_name" {
  value = docker_volume.data.name
}
