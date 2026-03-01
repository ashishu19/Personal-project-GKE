  variable "project_id" {
    description = "GCP Project ID"
    type = string
    default = "project-0d0e97b5-4743-4762-845"
  }
  variable "region" {
    description = "GCP region"
    type = string
    default = "us-central1"
  }
  
  variable "zone" { 
    description = "GCP zone"
    type = string
    default = "us-central1-a"
  }

  variable "gke_num_nodes" {
    description = "Number of GKE nodes"
    type = number
    default = 2
  }
