terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ----------------------------------------
# VPC Network
# ----------------------------------------
resource "google_compute_network" "vpc" {
  name                    = "sre-platform-vpc"
  auto_create_subnetworks = false
}

# ----------------------------------------
# Subnet
# ----------------------------------------
resource "google_compute_subnetwork" "subnet" {
  name          = "sre-platform-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/16"
  }
}

# ----------------------------------------
# Firewall Rule
# ----------------------------------------
resource "google_compute_firewall" "allow_internal" {
  name    = "allow-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
}

# ----------------------------------------
# GKE Cluster
# ----------------------------------------
resource "google_container_cluster" "primary" {
  name     = "sre-platform-cluster"
  location = var.zone

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  # Remove default node pool after creation
  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
}

# ----------------------------------------
# GKE Node Pool
# ----------------------------------------
resource "google_container_node_pool" "primary_nodes" {
  name       = "sre-platform-node-pool"
  location   = var.zone
  cluster    = google_container_cluster.primary.name
  node_count = var.gke_num_nodes

  node_config {
    machine_type = "e2-medium"  # cheap, 2 vCPU 4GB — good for learning
    disk_size_gb = 30

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      env = "sre-platform"
    }
  }
}

# ----------------------------------------
# GCS Bucket for app storage
# ----------------------------------------
resource "google_storage_bucket" "app_bucket" {
  name          = "${var.project_id}-app-storage"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

