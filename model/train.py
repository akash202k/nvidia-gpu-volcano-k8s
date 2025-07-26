# model/train.py
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import numpy as np
import os
import socket
import subprocess
import json
import boto3
from datetime import datetime
import traceback
import uuid

# S3 Configuration
S3_BUCKET = "volcano-akashplay"
S3_LOGS_PREFIX = "logs"

def get_s3_client():
    """Initialize S3 client"""
    try:
        return boto3.client('s3')
    except Exception as e:
        print(f"Failed to initialize S3 client: {e}")
        return None

def get_system_info():
    """Collect comprehensive system information"""
    info = {
        "timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "python_version": tf.__version__,
    }
    
    # CPU info
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpu_info = f.read()
            cpu_count = cpu_info.count('processor')
            cpu_model_lines = [line for line in cpu_info.split('\n') if 'model name' in line]
            cpu_model = cpu_model_lines[0].split(':')[1].strip() if cpu_model_lines else "Unknown"
        info["cpu"] = {
            "cores": cpu_count,
            "model": cpu_model
        }
    except Exception as e:
        info["cpu"] = {"error": str(e)}
    
    # Memory info
    try:
        with open('/proc/meminfo', 'r') as f:
            mem_info = f.read()
            mem_total_line = [line for line in mem_info.split('\n') if 'MemTotal' in line]
            mem_available_line = [line for line in mem_info.split('\n') if 'MemAvailable' in line]
            mem_total = int(mem_total_line[0].split()[1]) if mem_total_line else 0
            mem_available = int(mem_available_line[0].split()[1]) if mem_available_line else 0
        info["memory"] = {
            "total_mb": mem_total // 1024,
            "available_mb": mem_available // 1024
        }
    except Exception as e:
        info["memory"] = {"error": str(e)}
    
    return info

def get_kubernetes_info():
    """Collect Kubernetes information"""
    return {
        "pod_name": os.environ.get('HOSTNAME', 'Unknown'),
        "node_name": os.environ.get('KUBERNETES_NODE_NAME', 'Unknown'),
        "namespace": os.environ.get('KUBERNETES_NAMESPACE', 'default'),
        "service_account": os.environ.get('KUBERNETES_SERVICE_ACCOUNT', 'Unknown'),
        "pod_ip": os.environ.get('KUBERNETES_POD_IP', 'Unknown')
    }

def get_aws_metadata():
    """Get AWS instance metadata"""
    metadata = {}
    
    try:
        import urllib.request
        
        def get_metadata(path):
            url = f"http://169.254.169.254/latest/meta-data/{path}"
            try:
                with urllib.request.urlopen(url, timeout=3) as response:
                    return response.read().decode('utf-8')
            except:
                return "Unable to fetch"
        
        metadata = {
            "instance_id": get_metadata('instance-id'),
            "instance_type": get_metadata('instance-type'),
            "availability_zone": get_metadata('placement/availability-zone'),
            "region": get_metadata('placement/region'),
            "local_ipv4": get_metadata('local-ipv4'),
            "public_ipv4": get_metadata('public-ipv4')
        }
        
    except Exception as e:
        metadata = {"error": f"AWS metadata unavailable: {str(e)}"}
    
    return metadata

def get_gpu_info():
    """Get comprehensive GPU information"""
    gpu_info = {
        "tensorflow_version": tf.__version__,
        "cuda_built": tf.test.is_built_with_cuda(),
        "gpu_available": tf.test.is_gpu_available(),
        "physical_devices": []
    }
    
    # List all physical devices
    physical_devices = tf.config.list_physical_devices()
    for device in physical_devices:
        gpu_info["physical_devices"].append(str(device))
    
    # GPU-specific info
    gpus = tf.config.list_physical_devices('GPU')
    gpu_info["gpu_count"] = len(gpus)
    gpu_info["gpu_details"] = []
    
    for i, gpu in enumerate(gpus):
        gpu_detail = {"index": i, "device": str(gpu)}
        try:
            details = tf.config.experimental.get_device_details(gpu)
            gpu_detail["details"] = details
        except Exception as e:
            gpu_detail["details"] = {"error": str(e)}
        gpu_info["gpu_details"].append(gpu_detail)
    
    # NVIDIA-SMI info
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu', 
                               '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            nvidia_gpus = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(', ')
                    if len(parts) >= 5:
                        nvidia_gpus.append({
                            "name": parts[0],
                            "memory_total_mb": parts[1],
                            "memory_used_mb": parts[2],
                            "utilization_percent": parts[3],
                            "temperature_c": parts[4]
                        })
            gpu_info["nvidia_smi"] = nvidia_gpus
    except Exception as e:
        gpu_info["nvidia_smi"] = {"error": str(e)}
    
    return gpu_info

def get_resource_limits():
    """Get container resource limits"""
    limits = {}
    
    # CPU limits
    try:
        with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us', 'r') as f:
            cpu_quota = int(f.read().strip())
        with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us', 'r') as f:
            cpu_period = int(f.read().strip())
        if cpu_quota > 0:
            limits["cpu_limit_cores"] = cpu_quota / cpu_period
        else:
            limits["cpu_limit_cores"] = "unlimited"
    except Exception as e:
        limits["cpu_limit"] = {"error": str(e)}
    
    # Memory limits
    try:
        with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
            mem_limit = int(f.read().strip())
        if mem_limit < 9223372036854775807:  # Not unlimited
            limits["memory_limit_mb"] = mem_limit // (1024*1024)
        else:
            limits["memory_limit_mb"] = "unlimited"
    except Exception as e:
        limits["memory_limit"] = {"error": str(e)}
    
    return limits

def upload_to_s3(s3_client, data, filename):
    """Upload JSON data to S3"""
    if not s3_client:
        print(f"No S3 client available, saving locally: {filename}")
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return False
    
    try:
        s3_key = f"{S3_LOGS_PREFIX}/{filename}"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )
        print(f"Successfully uploaded to s3://{S3_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        print(f"Failed to upload to S3: {e}")
        # Save locally as backup
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return False

def run_training():
    """Run the TensorFlow training and return results"""
    training_log = {
        "status": "started",
        "start_time": datetime.now().isoformat(),
        "dataset": {
            "samples": 10000,
            "features": 10,
            "target_shape": 1
        },
        "model": {
            "layers": [
                {"type": "Dense", "units": 64, "activation": "relu"},
                {"type": "Dense", "units": 64, "activation": "relu"},
                {"type": "Dense", "units": 1, "activation": "linear"}
            ]
        },
        "training_config": {
            "optimizer": "adam",
            "loss": "mse",
            "epochs": 5,
            "batch_size": 64
        }
    }
    
    try:
        print("Generating random dataset...")
        X = np.random.rand(10000, 10)
        y = np.random.rand(10000, 1)
        
        print("Building model...")
        model = Sequential([
            Dense(64, activation='relu', input_shape=(10,)),
            Dense(64, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        
        # Determine device
        device_name = '/GPU:0' if tf.config.list_physical_devices('GPU') else '/CPU:0'
        training_log["device_used"] = device_name
        
        print(f"Training on device: {device_name}")
        print("Starting training...")
        
        with tf.device(device_name):
            history = model.fit(X, y, epochs=5, batch_size=64, verbose=1)
        
        # Training completed successfully
        training_log.update({
            "status": "success",
            "end_time": datetime.now().isoformat(),
            "final_loss": float(history.history['loss'][-1]),
            "loss_history": [float(loss) for loss in history.history['loss']],
            "total_epochs_completed": len(history.history['loss'])
        })
        
        print(f"Training completed successfully. Final loss: {training_log['final_loss']:.6f}")
        
    except Exception as e:
        training_log.update({
            "status": "failed",
            "end_time": datetime.now().isoformat(),
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        print(f"Training failed: {e}")
        raise
    
    return training_log

def main():
    """Main execution function"""
    # Generate unique run ID
    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"=== Volcano Training Job Started ===")
    print(f"Run ID: {run_id}")
    print(f"Timestamp: {timestamp}")
    
    # Initialize S3 client
    s3_client = get_s3_client()
    
    # Collect system information
    print("Collecting system information...")
    log_data = {
        "run_id": run_id,
        "job_type": "volcano_tensorflow_training",
        "system_info": get_system_info(),
        "kubernetes_info": get_kubernetes_info(),
        "aws_metadata": get_aws_metadata(),
        "gpu_info": get_gpu_info(),
        "resource_limits": get_resource_limits()
    }
    
    try:
        # Run training
        training_results = run_training()
        log_data["training_results"] = training_results
        
        # Upload success log
        filename = f"volcano_training_success_{timestamp}_{run_id}.json"
        upload_to_s3(s3_client, log_data, filename)
        
        print("=== Training Completed Successfully ===")
        
    except Exception as e:
        # Handle failure
        log_data["training_results"] = {
            "status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "end_time": datetime.now().isoformat()
        }
        
        # Upload failure log
        filename = f"volcano_training_failed_{timestamp}_{run_id}.json"
        upload_to_s3(s3_client, log_data, filename)
        
        print("=== Training Failed ===")
        print(f"Error: {e}")
        
        # Re-raise to ensure pod shows failure
        raise

if __name__ == "__main__":
    main()