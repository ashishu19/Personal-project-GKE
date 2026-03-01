# GCP Kubernetes Platform — Infrastructure as Code

A production-grade Kubernetes platform built on Google Cloud Platform using Terraform, demonstrating real-world SRE and platform engineering practices including infrastructure as code, remote state management, network segmentation, and workload deployment.

---

## What This Project Does

This project provisions a fully functional Kubernetes environment on GCP from scratch using Terraform. It simulates how platform and SRE engineers build and manage cloud infrastructure in production environments.

**Key capabilities:**
- Provisions a private VPC with custom subnets and firewall rules
- Deploys a GKE (Google Kubernetes Engine) cluster with a managed node pool
- Stores Terraform state remotely in GCS for team collaboration and disaster recovery
- Connects and validates workloads via kubectl and GCP LoadBalancer

This is not a click-through tutorial — every resource is defined as code, versioned in Git, and reproducible from scratch.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      GCP Project                        │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │                 Custom VPC                      │   │
│   │           (sre-platform-vpc)                    │   │
│   │                                                 │   │
│   │   ┌─────────────────────────────────────────┐   │   │
│   │   │           Subnet (10.0.0.0/24)          │   │   │
│   │   │                                         │   │   │
│   │   │   Pods CIDR:     10.1.0.0/16            │   │   │
│   │   │   Services CIDR: 10.2.0.0/16            │   │   │
│   │   │                                         │   │   │
│   │   │   ┌───────────────────────────────┐     │   │   │
│   │   │   │       GKE Cluster             │     │   │   │
│   │   │   │   (sre-platform-cluster)      │     │   │   │
│   │   │   │                               │     │   │   │
│   │   │   │   ┌────────┐  ┌────────┐      │     │   │   │
│   │   │   │   │ Node 1 │  │ Node 2 │      │     │   │   │
│   │   │   │   │e2-med  │  │e2-med  │      │     │   │   │
│   │   │   │   └────────┘  └────────┘      │     │   │   │
│   │   │   └───────────────────────────────┘     │   │   │
│   │   └─────────────────────────────────────────┘   │   │
│   │                                                 │   │
│   │   Firewall: allow internal traffic (10.0.0.0/8) │   │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
│   ┌──────────────────────┐  ┌────────────────────────┐  │
│   │   GCS Bucket         │  │   GCS Bucket           │  │
│   │   (Terraform State)  │  │   (App Storage)        │  │
│   │   versioning: ON     │  │   versioning: ON       │  │
│   └──────────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

Traffic Flow:
Internet → GCP LoadBalancer → GKE Service → Pod → App
```

**Terraform File Structure:**
```
sre-platform/
└── terraform/
    ├── backend.tf      # Remote state config (GCS)
    ├── main.tf         # All GCP resources
    ├── variables.tf    # Input variables
    └── outputs.tf      # Output values after apply
```

---

## Prerequisites

- GCP account with billing enabled ($300 free credits available)
- Tools installed on your machine:
  - [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.0
  - [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
  - [kubectl](https://kubernetes.io/docs/tasks/tools/)

---

## How to Run It

### 1. Authenticate with GCP

```bash
gcloud auth login
gcloud auth application-default login
```

### 2. Create GCP Project and Enable APIs

```bash
gcloud projects create my-sre-platform --name="SRE Platform"
gcloud config set project my-sre-platform

gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable iam.googleapis.com
```

### 3. Create GCS Bucket for Terraform State

> This must be done manually before Terraform runs — it's the backend Terraform will use to store state.

```bash
gsutil mb -p my-sre-platform -l us-central1 gs://my-sre-platform-tfstate
gsutil versioning set on gs://my-sre-platform-tfstate
```

### 4. Clone and Configure

```bash
git clone https://github.com/ashishu19/sre-platform.git
cd sre-platform/terraform
```

Update `variables.tf` if you want to change project ID, region, or node count.

### 5. Initialize Terraform

```bash
terraform init
```

This downloads the GCP provider and connects to the remote GCS backend.

### 6. Plan and Apply

```bash
# Preview what will be created
terraform plan

# Create all infrastructure
terraform apply
# Type 'yes' when prompted
```

> GKE cluster creation takes approximately 5-10 minutes.

### 7. Connect kubectl to Your Cluster

```bash
gcloud container clusters get-credentials sre-platform-cluster \
  --zone us-central1-a \
  --project my-sre-platform
```

### 8. Verify the Cluster

```bash
kubectl get nodes
```

Expected output:
```
NAME                STATUS   ROLES    AGE   VERSION
gke-sre-platform-  Ready    <none>   2m    v1.27.x
gke-sre-platform-  Ready    <none>   2m    v1.27.x
```

### 9. Deploy a Test Workload

```bash
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=LoadBalancer
kubectl get service nginx --watch
```

Once an EXTERNAL-IP appears, open it in your browser. Nginx welcome page = cluster is healthy.

### 10. Clean Up (to avoid GCP charges)

```bash
# Remove test workload
kubectl delete deployment nginx
kubectl delete service nginx

# Destroy all infrastructure
cd terraform
terraform destroy
```

---

## What I Learned

### Infrastructure as Code (Terraform)
Writing infrastructure as code rather than clicking through a console means every resource is versioned, reviewable, and reproducible. I learned how Terraform tracks state, what happens when state drifts from reality, and why remote state in GCS is critical for any real environment.

### Why Remote State Matters
Storing Terraform state locally is fine for a single developer but breaks immediately when collaborating or if your machine is lost. GCS backend with versioning means state is backed up, recoverable, and safe.

### Kubernetes Network Architecture
GKE requires three non-overlapping IP ranges — nodes, pods, and services. I learned why these must be planned carefully upfront and how secondary IP ranges in GCP subnets support this. Getting this wrong causes routing failures that are hard to debug.

### The Default Node Pool Problem
GKE creates a default node pool automatically but it has limited configuration options. The production pattern is to immediately delete it and create a custom node pool — this gives full control over machine type, disk size, labels, and autoscaling configuration.

### Security Through Network Segmentation
Rather than using GCP's default VPC (which is shared and has auto-created subnets in every region), creating a custom VPC with explicit firewall rules enforces least-privilege networking. Internal traffic is allowed only within the `10.0.0.0/8` range.

### GCP IAM and API Gating
GCP disables all service APIs by default for security and billing control. Enabling only the APIs you need (container, compute, storage, IAM) is a security best practice — it reduces the attack surface if credentials are ever compromised.

### kubectl and Cluster Authentication
`gcloud container clusters get-credentials` writes cluster certificates and API server endpoints to `~/.kube/config`. Understanding how kubeconfig works — contexts, clusters, users — is foundational for managing multiple Kubernetes environments.

---

## Next Steps

This project is Layer 1 of a larger SRE platform build:

- **Layer 2:** GitOps with ArgoCD — declarative, Git-driven deployments
- **Layer 3:** CI/CD pipeline with GitLab CI
- **Layer 4:** Secrets management with HashiCorp Vault
- **Layer 5:** Observability with Prometheus, Grafana, and SLO alerting

---

## Author

Built as part of a hands-on SRE/Platform Engineering portfolio to demonstrate real-world infrastructure skills.
