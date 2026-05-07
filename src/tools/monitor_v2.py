#!/usr/bin/env python3
"""
Trading Lab Real-Time Monitor v2
Shows download progress, watcher status, and backtest pipeline
"""

import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time
import os
import sys

def get_status():
    """Get complete status snapshot"""
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
    status['backtest_results_exist'] = results_path.exists()
    if results_path.exists():
        status['results_mod_time'] = datetime.fromtimestamp(results_path.stat().st_mtime)
    
    # Log activity
    log_path = Path('/workspaces/trading-lab/data/download.log')
    status['log_lines'] = []
    if log_path.exists():
        try:
            with open(log_path) as f:
                status['log_lines'] = f.readlines()[-3:]
        except:
            pass
    
    return status

def bar(current, total=150, width=60):
    """ASCII progress bar"""
    p = current / total if total > 0 else 0
    f = int(width * p)
    return '█' * f + '░' * (width - f) + f" {p*100:5.1f}%"

def format_bytes(bytes_val):
    """Format bytes to MB/GB"""
    mb = bytes_val / 1024 / 1024
    if mb > 1024:
        return f"{mb/1024:.1f} GB"
    return f"{mb:.1f} MB"

def main():
    print("\n🚀 Trading Lab Monitor Started\n")
    time.sleep(1)
    
    iteration = 0
    last_size = None
    last_update_time = None
    
    while True:
        iteration += 1
        status = get_status()
        now = datetime.now()
        
        # Clear screen
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Header
        print("\n" + "="*90)
        print(" TRADING LAB REAL-TIME MONITOR".center(90))
        print("="*90)
        
        current_time = now.strftime("%H:%M:%S UTC")
        print(f"\n⏰ {current_time} | Update #{iteration}")
        
        # Calculate speed
        size_mb = status.get('file_size_mb', 0)
        if last_size is not None:
            size_diff = size_mb - last_size
        else:
            size_diff = 0
        
        # Progress tracking
        print("\n" + "─"*90)
        print("📊 DATA DOWNLOAD PIPELINE")
        print("─"*90)
        
        dl_status = "✓ RUNNING" if status['download_running'] else "✗ STOPPED"
        print(f"  Status:        {dl_status}")
        print(f"  File Size:     {size_mb:.1f} MB / 150.0 MB")
        print(f"  Progress:      {bar(size_mb, 150)}")
        
        # Estimate ETA
        if size_mb > 0 and size_diff > 0:
            mb_per_sec = size_diff / 10  # Updates every 10 sec
            remaining_mb = 150 - size_mb
            if mb_per_sec > 0:
                eta_seconds = remaining_mb / mb_per_sec
                eta_time = (now + timedelta(seconds=eta_seconds)).strftime("%H:%M")
                print(f"  ETA:           ~{eta_time} UTC ({timedelta(seconds=int(eta_seconds))})")
            else:
                print(f"  ETA:           Calculating...")
        
        if status['rows']:
            print(f"  Data Points:   {status['rows']:,} M15 bars")
            date_range = f"{status['date_min'].date()} to {status['date_max'].date()}"
            print(f"  Date Range:    {date_range}")
        
        # Watcher status
        print("\n" + "─"*90)
        print("🔔 AUTO-TRIGGER WATCHER")
        print("─"*90)
        
        watcher_status = "✓ RUNNING" if status['watcher_running'] else "✗ STOPPED"
        print(f"  Status:        {watcher_status}")
        print(f"  Monitor:       Waiting for COMPLETE dataset (150 MB = 10 years M15)")
        
        ready = size_mb >= 150
        if ready:
            ready_status = "✓ COMPLETE (backtest will start now)"
        else:
            remaining = 150 - size_mb
            percent_needed = (remaining / 150) * 100
            ready_status = f"⏳ INCOMPLETE ({remaining:.1f} MB remaining, {percent_needed:.1f}% more data needed)"
        print(f"  Auto-Trigger:  {ready_status}")
        
        # Backtest pipeline
        print("\n" + "─"*90)
        print("⚗️  BACKTEST EXECUTION PIPELINE")
        print("─"*90)
        
        if status['backtest_running']:
            print(f"  Status:        🔄 RUNNING (executing 9 strategies × 7 timeframes)")
            print(f"  Expected Time: ~45 minutes")
            print(f"  Output:        results/backtest_full_results.csv (live)")
        
        elif status['backtest_results_exist']:
            # Check if results are fresh (from this run)
            results_age = now - status['results_mod_time']
            if results_age.total_seconds() < 3600:  # Less than 1 hour old = fresh
                print(f"  Status:        ✓ COMPLETED (fresh results)")
                try:
                    df = pd.read_csv('/workspaces/trading-lab/results/backtest_full_results.csv')
                    num_rows = len(df)
                    passing = len(df[df['all_objectives_ok'] == True])
                    
                    if num_rows >= 63:
                        print(f"  Results:       {num_rows} scenarios tested (9 strategies × 7 timeframes)")
                        print(f"  Passing:       {passing}/63 strategies met all objectives")
                        
                        if passing > 0:
                            best = df[df['all_objectives_ok'] == True].nlargest(1, 'sharpe_ratio').iloc[0]
                            print(f"  Best Strategy: {best['version']} on {best['timeframe']} timeframe")
                            print(f"                 Sharpe={best['sharpe_ratio']:.2f}, Return={best['avg_monthly_ret_pct']:.2f}%/mo, DD={best['max_drawdown_pct']:.1f}%")
                    else:
                        print(f"  Results:       {num_rows} rows (waiting for full M15 download to complete)")
                except Exception as e:
                    print(f"  Results:       (file exists but parsing error)")
            else:
                print(f"  Status:        ✓ PREVIOUS RESULTS (from {results_age.total_seconds()/3600:.1f} hours ago)")
                print(f"  Note:          These will be overwritten when M15 download completes and backtest auto-triggers")
        
        else:
            print(f"  Status:        ⏳ PENDING (waiting for complete M15 dataset)")
            remaining_mb = 150 - size_mb
            if remaining_mb > 0:
                print(f"  When:          After download reaches 150 MB ({remaining_mb:.1f} MB remaining)")
            print(f"  Expected Time: ~45-60 minutes to complete after all data is ready")
            print(f"  Output File:   results/backtest_full_results.csv")
        
        # Recent activity
        print("\n" + "─"*90)
        print("📋 RECENT LOG ACTIVITY")
        print("─"*90)
        
        if status['log_lines']:
            for line in status['log_lines']:
                line_clean = line.rstrip()
                if line_clean:
                    # Truncate and indent
                    if len(line_clean) > 88:
                        line_clean = line_clean[:85] + "..."
                    print(f"  {line_clean}")
        else:
            print("  (no recent activity)")
        
        # Footer
        print("\n" + "="*90)
        print(f"Next update in 10 seconds... (Press Ctrl+C to exit)".center(90))
        print("="*90 + "\n")
        
        last_size = size_mb
        last_update_time = now
        
        # Wait for next update
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n✓ Monitor stopped\n")
            sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n✓ Monitor stopped\n")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}\n")
        sys.exit(1)
