#!/usr/bin/env python3
"""
Simple real-time progress monitor for Trading Lab
No fancy colors, just clean output that updates every 10 seconds
"""

import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time
import os

def get_status():
    """Get current status of all processes"""
    status = {}
    
    # Parquet file info
    parquet_path = Path('/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet')
    if parquet_path.exists():
        status['file_size_mb'] = parquet_path.stat().st_size / 1024 / 1024
        status['mod_time'] = datetime.fromtimestamp(parquet_path.stat().st_mtime)
        try:
            df = pd.read_parquet(str(parquet_path))
            status['rows'] = len(df)
            status['date_min'] = df.index.min()
            status['date_max'] = df.index.max()
        except:
            status['rows'] = None
    else:
        status['file_size_mb'] = 0
        status['rows'] = None
    
    # Process status
    try:
        output = subprocess.check_output(['ps', 'aux'], text=True)
        status['download_running'] = 'download_data.py' in output
        status['watcher_running'] = 'run_when_ready.py' in output
        status['backtest_running'] = 'backtest_full.py' in output
    except:
        status['download_running'] = False
        status['watcher_running'] = False
        status['backtest_running'] = False
    
    # Backtest completion
    results_path = Path('/workspaces/trading-lab/results/backtest_full_results.csv')
    status['backtest_completed'] = results_path.exists()
    
    # Log activity
    log_path = Path('/workspaces/trading-lab/data/download.log')
    status['log_lines'] = []
    if log_path.exists():
        try:
            with open(log_path) as f:
                status['log_lines'] = f.readlines()[-2:]
        except:
            pass
    
    return status

def format_progress_bar(current, total=150, width=50):
    """Create ASCII progress bar"""
    percent = current / total if total > 0 else 0
    filled = int(width * percent)
    bar = '█' * filled + '░' * (width - filled)
    return f"{bar} {percent*100:5.1f}%"

def print_status(iteration, last_size):
    """Print current status"""
    status = get_status()
    current_time = datetime.now().strftime("%H:%M:%S UTC")
    
    # Calculate speed
    size_mb = status.get('file_size_mb', 0)
    size_diff = size_mb - last_size if last_size is not None else 0
    
    # Calculate ETA
    if size_mb > 0:
        elapsed_minutes = iteration * 0.17  # ~10 seconds per iteration
        mb_per_minute = size_mb / elapsed_minutes if elapsed_minutes > 0 else 0
        if mb_per_minute > 0:
            remaining_mb = 150 - size_mb
            eta_minutes = remaining_mb / mb_per_minute
            eta_time = (datetime.now() + timedelta(minutes=eta_minutes)).strftime("%H:%M")
        else:
            eta_time = "?"
    else:
        eta_time = "?"
    
    # Clear and print
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("\n" + "="*80)
    print("  TRADING LAB — REAL-TIME PROGRESS MONITOR".center(80))
    print("="*80)
    
    print(f"\n⏰ {current_time} | Update #{iteration} | Speed: {size_diff:.1f} MB/10s")
    
    # Download Section
    print("\n📊 DUKASCOPY M15 DOWNLOAD:")
    print(f"   Status: {'✓ RUNNING' if status['download_running'] else '⏸ PAUSED'}")
    print(f"   File:   {size_mb:.1f} MB / 150.0 MB")
    print(f"   Bar:    {format_progress_bar(size_mb)}")
    
    if status['rows']:
        print(f"   Data:   {status['rows']:,} M15 bars")
        print(f"   Date:   {status['date_min'].date()} to {status['date_max'].date()}")
    
    print(f"   ETA:    ~{eta_time} (based on current speed)")
    
    # Watcher Status
    print("\n🔔 AUTO-TRIGGER WATCHER:")
    watcher_str = "✓ RUNNING" if status['watcher_running'] else "✗ STOPPED"
    print(f"   Status: {watcher_str}")
    print(f"   Watch:  Parquet >10MB → Auto-trigger backtest")
    print(f"   Ready:  {'YES ✓' if size_mb > 10 else f'NO ({size_mb:.1f} MB < 10 MB)'}")
    
    # Backtest Status
    print("\n⚗️  BACKTEST STATUS:")
    if status['backtest_completed']:
        print(f"   Status: ✓ COMPLETED")
        try:
            results = pd.read_csv('/workspaces/trading-lab/results/backtest_full_results.csv')
            passing = len(results[results['all_objectives_ok'] == True])
            print(f"   Result: {passing}/63 strategies passed objectives")
            if passing > 0:
                best = results[results['all_objectives_ok'] == True].nlargest(1, 'sharpe_ratio').iloc[0]
                print(f"   Best:   {best['version']} ({best['timeframe']}) Sharpe={best['sharpe_ratio']:.2f}")
        except:
            print(f"   Result: (parsing results...)")
    elif status['backtest_running']:
        print(f"   Status: 🔄 RUNNING NOW")
        print(f"   Note:   This will take ~45 minutes")
    else:
        percent_to_trigger = (10 / size_mb * 100) if size_mb > 0 else 0
        print(f"   Status: ⏳ PENDING")
        print(f"   When:   After download reaches 10 MB ({percent_to_trigger:.0f}% of current)")
    
    # Recent Activity
    if status['log_lines']:
        print("\n📋 RECENT LOG ACTIVITY:")
        for line in status['log_lines']:
            line_clean = line.rstrip()
            if line_clean:
                # Truncate if too long
                if len(line_clean) > 78:
                    line_clean = line_clean[:75] + "..."
                print(f"   {line_clean}")
    
    # Footer
    print("\n" + "="*80)
    print("Press Ctrl+C to stop monitoring".center(80))
    print("="*80 + "\n")
    
    return size_mb

if __name__ == '__main__':
    print("\n🚀 Starting real-time monitor...\n")
    time.sleep(2)
    
    iteration = 0
    last_size = None
    
    try:
        while True:
            iteration += 1
            last_size = print_status(iteration, last_size)
            time.sleep(10)  # Update every 10 seconds
    except KeyboardInterrupt:
        print("\n✓ Monitor stopped\n")
