#!/usr/bin/env python3
"""
Script to extract timing information from mllog.txt and calculate average times per function.
Parses lines with format: (Time 0.01 (functionName Result))
"""

import re
from collections import defaultdict
from typing import Dict, List

def parse_timing_line(line: str) -> tuple[str, float] | None:
    """
    Parse a line to extract function name and time.
    Expected format: (Time 0.01 (functionName Result))
    Returns (function_name, time) or None if no match.
    """
    # Pattern to match (Time <number> (functionName ...))
    pattern = r'\(Time\s+([\d.]+)\s+\((\w+)'
    match = re.search(pattern, line)
    
    if match:
        time_value = float(match.group(1))
        function_name = match.group(2)
        return function_name, time_value
    
    return None

def analyze_timing_log(filename: str) -> Dict[str, List[float]]:
    """
    Read the log file and extract all timing information.
    Returns a dictionary mapping function names to lists of times.
    """
    function_times = defaultdict(list)
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                result = parse_timing_line(line.strip())
                if result:
                    function_name, time_value = result
                    function_times[function_name].append(time_value)
    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return {}
    except Exception as e:
        print(f"Error reading file: {e}")
        return {}
    
    return function_times

def calculate_averages(function_times: Dict[str, List[float]]) -> Dict[str, float]:
    """
    Calculate average time for each function.
    """
    averages = {}
    for function_name, times in function_times.items():
        if times:
            averages[function_name] = sum(times) / len(times)
    
    return averages

def main():
    filename = "mllog.txt"
    
    print(f"Analyzing timing data from {filename}...")
    
    # Extract timing data
    function_times = analyze_timing_log(filename)
    
    if not function_times:
        print("No timing data found in the file.")
        return
    
    # Calculate averages
    averages = calculate_averages(function_times)
    
    # Display results
    print("\nTiming Analysis Results:")
    print("=" * 50)
    print(f"{'Function Name':<20} {'Count':<8} {'Average Time':<12}")
    print("-" * 50)
    
    # Sort by function name for consistent output
    for function_name in sorted(averages.keys()):
        count = len(function_times[function_name])
        avg_time = averages[function_name]
        print(f"{function_name:<20} {count:<8} {avg_time:<12.6f}")
    
    print(f"\nTotal functions analyzed: {len(averages)}")
    
    # Show overall statistics
    all_times = [time for times in function_times.values() for time in times]
    if all_times:
        print(f"Total timing entries: {len(all_times)}")
        print(f"Overall average time: {sum(all_times) / len(all_times):.6f}")

if __name__ == "__main__":
    main()
