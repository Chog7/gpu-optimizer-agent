import csv
from datetime import datetime

csv_filename = "gpu_log.csv"

# Configuration for our "Idle Rule"
IDLE_THRESHOLD_PERCENT = 5
IDLE_DURATION_SECONDS = 60 * 15 # 15 minutes (must be idle for this long to count)

def analyze_log(filename):
    idle_time_seconds = 0
    total_time_seconds = 0
    
    current_idle_streak = 0
    last_timestamp = None
    
    try:
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                timestamp_str = row['timestamp']
                utilization = int(row['utilization_percent'])
                
                current_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                if last_timestamp:
                    time_diff = (current_time - last_timestamp).total_seconds()
                    total_time_seconds += time_diff
                    
                    if utilization <= IDLE_THRESHOLD_PERCENT:
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
                
        # Catch any idle streak that was still ongoing at the end of the file
        if current_idle_streak >= IDLE_DURATION_SECONDS:
            idle_time_seconds += current_idle_streak
            print(f"Flagged Idle Period: {current_idle_streak / 60:.1f} minutes ending at {last_timestamp}")
            
    except FileNotFoundError:
        print(f"Could not find {filename}. Make sure to run the tracker first.")
        return

    # Calculate mock cost just for fun (pretending your 3070 Ti is a rented instance)
    mock_hourly_rate = 1.00 # $1 per hour
    mock_savings = (idle_time_seconds / 3600) * mock_hourly_rate

    print("-" * 40)
    print("GPU Usage Report")
    print("-" * 40)
    print(f"Total Time Tracked:    {total_time_seconds / 3600:.2f} hours")
    print(f"Total True Idle Time:  {idle_time_seconds / 3600:.2f} hours")
    print(f"Mock Savings ($1/hr):  ${mock_savings:.2f}")

if __name__ == "__main__":
    analyze_log(csv_filename)
