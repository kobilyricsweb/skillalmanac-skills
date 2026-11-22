variable "db_password" {
  type      = string
  default   = "hunter2hunter2"
  sensitive = true
}

variable "api_token" {
  type    = string
  default = ""
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "admin_secret" {
  type    = string
  default = "REPLACE_ME"
}
