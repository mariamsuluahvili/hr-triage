variable "group_number" {
  type    = number
  default = 3

  validation {
    condition     = var.group_number >= 1 && var.group_number <= 99
    error_message = "group_number must be between 1 and 99."
  }
}

variable "image_name" {
  type    = string
  default = "hr-triage:local"
}

variable "scenario_id" {
  type    = string
  default = "g03"
}

variable "llm_provider" {
  type    = string
  default = "mock"

  validation {
    condition     = contains(["mock", "local"], var.llm_provider)
    error_message = "llm_provider must be mock or local."
  }
}

variable "llm_base_url" {
  type    = string
  default = "http://host.docker.internal:1234/v1"
}

variable "llm_model" {
  type    = string
  default = ""
}

variable "llm_timeout" {
  type    = number
  default = 60
}

variable "llm_max_tokens" {
  type    = number
  default = 300
}
