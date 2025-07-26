# NVIDIA GPU Volcano Kubernetes Batch Jobs

## Architecture Diagram

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/94335330-0360-41aa-836a-8263d70cded6" />

---

## Project Overview


Minimal demo to showcase **gang scheduling** using [Volcano](https://volcano.sh/en/) on Kubernetes. Runs a lightweight TensorFlow job that requires multiple pods to start together.

## ✅ Features

* Gang scheduling with `minAvailable: 2`
* Runs on a single `g4dn.xlarge` GPU instance
* Simulates resource contention to demonstrate blocking
* Cross-platform Docker build (Mac M1 → Linux AMD64)
* Complete run under 15 minutes and \~\$0.05 (spot instance)

## 📁 Structure

```
.
├── Dockerfile
├── model/
│   └── train.py
├── manifests/
│   ├── gpu-node-label-taint.sh
│   ├── tensorflow-job.yaml
│   ├── volcano-queue.yaml
│   └── blocker-pod.yaml
└── README.md
```

## 🚀 Run Demo

```bash
# 1. Label and taint GPU node
chmod +x manifests/gpu-node-label-taint.sh
./manifests/gpu-node-label-taint.sh

# 2. Create Volcano queue
kubectl apply -f manifests/volcano-queue.yaml

# 3. Simulate GPU contention
kubectl apply -f manifests/blocker-pod.yaml

# 4. Deploy gang scheduled job
kubectl apply -f manifests/tensorflow-job.yaml

# 5. Watch pods (should stay Pending)
kubectl get pods -w

# 6. Delete blocker to allow gang job to run
kubectl delete pod blocker
```

## 🧹 Cleanup

```bash
kubectl delete -f manifests/
docker rmi tf-volcano-demo
```

## 💰 Cost Tips

* Use `g4dn.xlarge` **spot instance**
* Total cost: **<\$0.05** (runtime \~15 mins)
