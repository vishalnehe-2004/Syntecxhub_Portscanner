import socket
import argparse
import logging
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scan_results.log"),
        logging.StreamHandler()
    ]
)

def scan_port(ip, port, timeout):
    """
    Scans a single port on the target IP.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            if result == 0:
                logging.info(f"[+] Port {port} is OPEN on {ip}")
                return port
    except Exception as e:
        pass # Pass silently to keep logs clean
    return None

def main():
    # --- 1. Hybrid Argument Parsing ---
    parser = argparse.ArgumentParser(description="Multi-threaded TCP Port Scanner")
    
    # We use nargs='?' to make the host OPTIONAL. 
    # If provided, it uses it. If not, we ask for it later.
    parser.add_argument("host", nargs='?', help="Target Hostname or IP address")
    parser.add_argument("--start", type=int, default=1, help="Start Port (default: 1)")
    parser.add_argument("--end", type=int, default=1024, help="End Port (default: 1024)")
    parser.add_argument("--threads", type=int, default=100, help="Number of threads")
    parser.add_argument("--timeout", type=float, default=0.5, help="Socket timeout")
    
    args = parser.parse_args()

    # --- 2. Handle Missing Arguments (The Fix) ---
    # If the user ran the script without arguments, use localhost as default
    if args.host is None:
        print("\n" + "="*40)
        print(" >> DEFAULT MODE: Using localhost")
        print("="*40)
        args.host = "localhost"

    # --- 3. Resolve Hostname ---
    try:
        target_ip = socket.gethostbyname(args.host)
    except socket.gaierror:
        logging.error(f"Could not resolve hostname: {args.host}")
        return

    # --- 4. Start Scan ---
    print("-" * 50)
    print(f"Scanning Target: {target_ip} ({args.host})")
    print(f"Scanning Ports:  {args.start} to {args.end}")
    print(f"Time Started:    {datetime.now()}")
    print("-" * 50)

    start_time = datetime.now()
    open_ports = []

    try:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            # Launch all threads
            futures = {
                executor.submit(scan_port, target_ip, port, args.timeout): port 
                for port in range(args.start, args.end + 1)
            }
            
            # Gather results
            for future in futures:
                result = future.result()
                if result:
                    open_ports.append(result)

    except KeyboardInterrupt:
        print("\nScan interrupted by user!")
        return

    # --- 5. Summary ---
    duration = datetime.now() - start_time
    print("-" * 50)
    print(f"Scan completed in {duration}")
    if open_ports:
        print(f"Open Ports: {sorted(open_ports)}")
    else:
        print("No open ports found.")
    print("-" * 50)

if __name__ == "__main__":
    main()