import csv
from datetime import datetime

# Configuration for our "Idle Rule"
IDLE_THRESHOLD_PERCENT = 5
CPU_IDLE_THRESHOLD_PERCENT = 15 # CPU usage must be below this to be considered idle
IDLE_DURATION_SECONDS = 60 * 15 # 15 minutes (must be idle for this long to count)

def analyze_log(filename):
    total_time_seconds = 0
    idle_time_seconds = 0
    current_idle_streak = 0
    last_timestamp = None
    
    try:
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    timestamp_str = row['timestamp']
                    
                    # Fallbacks added so older CSV rows without these columns won't break
                    gpu_util = int(row.get('gpu_utilization_percent', row.get('utilization_percent', 0)))
                    cpu_util = float(row.get('cpu_utilization_percent', 0))
                    ssh_count = int(row.get('ssh_connections', 0))
                    jupyter_count = int(row.get('jupyter_kernels', 0))
                    
                    current_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError, KeyError):
                    # Skip blank or corrupted rows caused by stopping the tracker abruptly
                    continue

                if last_timestamp:
                    time_diff = (current_time - last_timestamp).total_seconds()
                    
                    # If the time difference is larger than 60 seconds, the tracker was turned off.
                    if time_diff > 60:
                        # Check if the streak before the tracker was turned off was long enough
                        if current_idle_streak >= IDLE_DURATION_SECONDS:
                            idle_time_seconds += current_idle_streak
                            print(f"Flagged Idle Period: {current_idle_streak / 60:.1f} minutes ending at {last_timestamp}")
                        
                        # Reset the streak, and DO NOT add the gap to total_time_seconds
                        current_idle_streak = 0
                    else:
                        total_time_seconds += time_diff
                        
                        # Only count as idle if GPU & CPU are low, and NO ONE is logged in
                        is_idle = (
                            gpu_util <= IDLE_THRESHOLD_PERCENT and
                            cpu_util <= CPU_IDLE_THRESHOLD_PERCENT and
                            ssh_count == 0 and
                            jupyter_count == 0
                        )
                        
                        if is_idle:
                            # Add time to the current idle streak
                            current_idle_streak += time_diff
                        else:
                            # Utilization spiked! The streak is broken.
                            # Check if the streak was long enough to be considered a "True Idle" period
                            if current_idle_streak >= IDLE_DURATION_SECONDS:
                                idle_time_seconds += current_idle_streak
                                print(f"Flagged Idle Period: {current_idle_streak / 60:.1f} minutes ending at {timestamp_str}")
                            
                            # Reset the streak
                            current_idle_streak = 0
                        
                last_timestamp = current_time

        # After the loop, check the final streak
        if current_idle_streak >= IDLE_DURATION_SECONDS:
            idle_time_seconds += current_idle_streak

    except FileNotFoundError:
        print(f"Error: Could not find {filename}.")
        return

    lambda_hourly_rate = 1.10 
    mock_savings = (idle_time_seconds / 3600) * lambda_hourly_rate

    print("-" * 40)
    print("GPU Usage Report")
    print("-" * 40)
    print(f"Total Time Tracked:    {total_time_seconds / 3600:.2f} hours")
    print(f"Total True Idle Time:  {idle_time_seconds / 3600:.2f} hours")
    print(f"Lambda Savings (${lambda_hourly_rate}/hr): ${mock_savings:.2f}")

if __name__ == "__main__":
    analyze_log("gpu_log.csv")