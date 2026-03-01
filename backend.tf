terraform {
  backend "gcs" {
    bucket = "my-sre-platform-tfstate"
    prefix = "terraform/state"
  }
}
