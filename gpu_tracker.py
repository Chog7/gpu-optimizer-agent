import pynvml
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

# Create the CSV and write headers if it's empty
with open(csv_filename, mode='a', newline='') as file:
    writer = csv.writer(file)
    if file.tell() == 0:
        writer.writerow(["timestamp", "utilization_percent", "memory_used_mb", "memory_total_mb"])

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
        
        # Append the new row to the CSV
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, utilization.gpu, mem_used_mb, mem_total_mb])
            
        # Log every 10 seconds
        time.sleep(10)
        
except KeyboardInterrupt:
    print("\nTracking stopped.")
finally:
    pynvml.nvmlShutdown()
