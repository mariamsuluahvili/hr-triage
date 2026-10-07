terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "4.0.0"
    }
  }
}

provider "docker" {}

locals {
  group_id = format("g%02d", var.group_number)
  prefix   = "hr-triage-${local.group_id}"
  api_port = 8000 + var.group_number
  ui_port  = 8500 + var.group_number
}

data "docker_image" "app" {
  name = var.image_name
}

resource "docker_network" "group" {
  name = "${local.prefix}-net"
}

resource "docker_volume" "data" {
  name = "${local.prefix}-data"
}

resource "docker_container" "api" {
  name    = "${local.prefix}-api"
  image   = data.docker_image.app.id
  restart = "unless-stopped"

  env = [
    "LLM_PROVIDER=${var.llm_provider}",
    "SCENARIO_ID=${var.scenario_id}",
    "DB_PATH=/data/analyses.db",
    "LLM_BASE_URL=${var.llm_base_url}",
    "LLM_MODEL=${var.llm_model}",
    "LLM_TIMEOUT=${var.llm_timeout}",
    "LLM_MAX_TOKENS=${var.llm_max_tokens}",
  ]

  ports {
    internal = 8000
    external = local.api_port
  }

  volumes {
    volume_name    = docker_volume.data.name
    container_path = "/data"
  }

  networks_advanced {
    name = docker_network.group.name
  }

  healthcheck {
    test     = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
    interval = "10s"
    timeout  = "5s"
    retries  = 5
  }
}

resource "docker_container" "ui" {
  name    = "${local.prefix}-ui"
  image   = data.docker_image.app.id
  restart = "unless-stopped"

  command = [
    "python", "-m", "streamlit", "run", "ui/app.py",
    "--server.port=8501",
    "--server.address=0.0.0.0",
    "--server.headless=true",
  ]

  env = [
    "API_URL=http://${docker_container.api.name}:8000",
  ]

  ports {
    internal = 8501
    external = local.ui_port
  }

  networks_advanced {
    name = docker_network.group.name
  }
}
