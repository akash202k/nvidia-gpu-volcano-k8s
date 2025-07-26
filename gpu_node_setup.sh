#!/bin/bash

echo "Setting up GPU nodes for Volcano demo..."

# Get GPU node names
GPU_NODES=$(kubectl get nodes --no-headers | grep g4dn | awk '{print $1}')

if [ -z "$GPU_NODES" ]; then
    echo "No g4dn GPU nodes found. Please check your node group."
    exit 1
fi

echo "Found GPU nodes:"
for node in $GPU_NODES; do
    echo "  - $node"
done

# Apply standard NVIDIA GPU taints
echo "Applying NVIDIA GPU taints..."
for node in $GPU_NODES; do
    kubectl taint nodes $node nvidia.com/gpu=present:NoSchedule --overwrite
    echo "Tainted node: $node"
done

echo "GPU node setup completed!"
echo ""
echo "Verify setup:"
echo "kubectl get nodes -o custom-columns=NAME:.metadata.name,GPU:.status.allocatable.'nvidia\.com/gpu'"