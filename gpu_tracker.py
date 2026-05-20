import pynvml
import psutil
import time
import csv
from datetime import datetime

# Initialize the NVML library
try:
    pynvml.nvmlInit()
except pynvml.NVMLError as error:
    print(f"Failed to initialize NVML: {error}")
    print("Make sure you have NVIDIA drivers installed.")
    exit(1)

# We assume you have 1 GPU (index 0)
device_index = 0
handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
gpu_name = pynvml.nvmlDeviceGetName(handle)

# If it's returning a bytes object (older pynvml versions), decode it
if isinstance(gpu_name, bytes):
    gpu_name = gpu_name.decode('utf-8')

print(f"Tracking GPU: {gpu_name}")

csv_filename = "gpu_log.csv"

# Cloud Configuration (In the future, your API will supply this)
SSH_PORT = 22

def get_ssh_connections():
    count = 0
    try:
        for conn in psutil.net_connections(kind='tcp'):
            # Look for established connections on the designated SSH port
            if conn.laddr and conn.laddr.port == SSH_PORT and conn.status == 'ESTABLISHED':
                count += 1
    except psutil.AccessDenied:
        pass
    return count

def get_jupyter_kernels():
    count = 0
    for proc in psutil.process_iter(['cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline:
                cmd_str = ' '.join(cmdline).lower()
                if 'ipykernel' in cmd_str or 'jupyter' in cmd_str or '-m notebook' in cmd_str:
                    if 'gpu_tracker.py' not in cmd_str: # Prevent the tracker from counting itself
                        count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return count

# Create the CSV and write headers if it's empty
with open(csv_filename, mode='a', newline='') as file:
    writer = csv.writer(file)
    if file.tell() == 0:
        writer.writerow(["timestamp", "gpu_utilization_percent", "gpu_memory_used_mb", "gpu_memory_total_mb", "cpu_utilization_percent", "ssh_connections", "jupyter_kernels"])

print(f"Logging metrics to {csv_filename}. Press Ctrl+C to stop.")

try:
    while True:
        # Get utilization rates (compute)
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        
        # Get memory info
        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        mem_used_mb = memory_info.used / (1024 ** 2)
        mem_total_mb = memory_info.total / (1024 ** 2)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get system CPU utilization
        cpu_utilization = psutil.cpu_percent(interval=None)

        ssh_count = get_ssh_connections()
        jupyter_count = get_jupyter_kernels()

        # Append the new row to the CSV
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, utilization.gpu, mem_used_mb, mem_total_mb, cpu_utilization, ssh_count, jupyter_count])
            
        # Log every 10 seconds
        time.sleep(10)
        
except KeyboardInterrupt:
    print("\nTracking stopped.")
finally:
    pynvml.nvmlShutdown()
