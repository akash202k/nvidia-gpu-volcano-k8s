# NVIDIA GPU Volcano Kubernetes Batch Jobs

## Architecture Diagram

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/94335330-0360-41aa-836a-8263d70cded6" />

---

## Project Overview

This project demonstrates a production-grade Proof-of-Concept (PoC) for running **GPU-accelerated machine learning batch jobs** on Kubernetes using:

* **Volcano** (version 1.12.1 via Helm chart) for advanced batch scheduling and gang scheduling capabilities
* **Karpenter** for dynamic provisioning and autoscaling of NVIDIA GPU nodes
* **AWS EKS** as the Kubernetes platform leveraging cost-effective GPU instance types (e.g., `g4dn.xlarge`)
* **TensorFlow GPU containers** for ML model training workloads

The setup enables efficient orchestration of scalable ML batch pipelines, ensuring resource optimization, workload reliability, and cost-effectiveness.

---

## Key Concepts

* **Gang Scheduling:** Volcano schedules pods as a group, ensuring all required pods start together or none at all, which is crucial for distributed ML workloads.
* **Dynamic GPU Node Provisioning:** Karpenter automatically scales GPU-enabled nodes up and down based on workload demand, reducing idle costs.
* **Resource Isolation:** GPU nodes are tainted and tolerations are used to ensure GPU workloads run only on appropriate nodes.
* **Batch Job Reliability:** Volcano handles retries, priorities, and queue management to improve batch job success rates.

---

## Project Aim

To showcase how a DevOps engineer can build and manage a cloud-native ML batch job pipeline with GPU acceleration on Kubernetes, demonstrating production best practices for scheduling, scaling, and cost optimization.

---
- Akash Pawar
