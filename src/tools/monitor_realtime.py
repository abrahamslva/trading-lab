#!/usr/bin/env python3
"""
Real-time monitoring dashboard for Trading Lab pipeline
- Dukascopy M15 download progress
- Auto-trigger watcher status
- Backtest execution tracking
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def get_parquet_info():
    """Get parquet file stats"""
    parquet_path = Path('/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet')
    if not parquet_path.exists():
        return None, None, None
    
    file_size_mb = parquet_path.stat().st_size / 1024 / 1024
    mod_time = datetime.fromtimestamp(parquet_path.stat().st_mtime)
    
    try:
        df = pd.read_parquet(str(parquet_path))
        rows = len(df)
        return file_size_mb, rows, mod_time
    except Exception as e:
        return file_size_mb, None, mod_time

def get_download_log():
    """Read last 3 lines of download log"""
    log_path = Path('/workspaces/trading-lab/data/download.log')
    if not log_path.exists():
        return []
    
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
        return lines[-5:]
    except:
        return []

def get_processes_status():
    """Check if download and watcher are running"""
    try:
        output = subprocess.check_output(['ps', 'aux'], text=True)
        download_running = 'download_data.py' in output and 'grep' not in output
        watcher_running = 'run_when_ready.py' in output
        return download_running, watcher_running
    except:
        return False, False

def get_backtest_status():
    """Check if backtest is running or completed"""
    try:
        output = subprocess.check_output(['ps', 'aux'], text=True)
        backtest_running = 'backtest_full.py' in output
        
        results_path = Path('/workspaces/trading-lab/results/backtest_full_results.csv')
        if results_path.exists():
            return 'completed', None
        elif backtest_running:
            return 'running', None
        else:
            return 'pending', None
    except:
        return 'unknown', None

def calculate_eta(current_mb, target_mb=150):
    """Estimate time to completion"""
    log_path = Path('/workspaces/trading-lab/data/download.log')
    if not log_path.exists():
        return None
    
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        # Find timestamps
        first_line_time = None
        last_line_time = None
        
        for line in lines:
            if 'Checkpoint' in line:
                # Try to parse time from log
                pass
        
        # Simple estimate: assume 150MB total, calculate rate
        if current_mb > 0:
            elapsed_hours = 6  # Session is ~6 hours old
            mb_per_hour = current_mb / elapsed_hours if elapsed_hours > 0 else 0
            if mb_per_hour > 0:
                remaining_mb = target_mb - current_mb
                hours_remaining = remaining_mb / mb_per_hour
                return timedelta(hours=hours_remaining)
    except:
        pass
    
    return None

def draw_progress_bar(current, total, width=40):
    """Draw ASCII progress bar"""
    percent = current / total if total > 0 else 0
    filled = int(width * percent)
    bar = '█' * filled + '░' * (width - filled)
    return f"{bar} {percent*100:.1f}%"

def print_header():
    """Print dashboard header"""
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "═"*74 + "╗")
    print("║" + " "*74 + "║")
    print("║" + "  🚀 TRADING LAB — REAL-TIME MONITORING DASHBOARD".center(74) + "║")
    print("║" + " "*74 + "║")
    print("╚" + "═"*74 + "╝")
    print(f"{Colors.ENDC}")

def print_section(title):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}┌─ {title} " + "─" * (70 - len(title)) + "┐{Colors.ENDC}")

def print_line(label, value, status=None):
    """Print formatted line"""
    if status == 'ok':
        status_str = f"{Colors.GREEN}✅{Colors.ENDC}"
    elif status == 'warning':
        status_str = f"{Colors.YELLOW}⚠️{Colors.ENDC}"
    elif status == 'error':
        status_str = f"{Colors.RED}❌{Colors.ENDC}"
    elif status == 'pending':
        status_str = f"{Colors.GRAY}⏳{Colors.ENDC}"
    elif status == 'running':
        status_str = f"{Colors.CYAN}🔄{Colors.ENDC}"
    else:
        status_str = ""
    
    status_part = f" {status_str}" if status_str else ""
    print(f"│ {label:30s} {value:39s}{status_part} │")

def main_loop():
    """Main monitoring loop"""
    iteration = 0
    last_size = 0
    last_check = time.time()
    
    while True:
        iteration += 1
        print_header()
        
        # ===== DOWNLOAD STATUS =====
        print_section("📊 DUKASCOPY M15 DOWNLOAD")
        
        file_size_mb, rows, mod_time = get_parquet_info()
        download_running, watcher_running = get_processes_status()
        
        if file_size_mb is None:
            print_line("Status", "File not created yet", 'pending')
            print_line("Progress", "0 / 150 MB", 'warning')
        else:
            status = 'running' if download_running else 'paused'
            status_emoji = 'running' if download_running else 'warning'
            
            print_line("Status", status, status_emoji)
            print_line("File Size", f"{file_size_mb:.1f} / 150.0 MB", 'ok' if file_size_mb > 10 else 'warning')
            print_line("Progress", draw_progress_bar(file_size_mb, 150), 'ok' if file_size_mb > 10 else 'warning')
            
            if rows:
                print_line("Data Points", f"{rows:,} M15 bars", 'ok')
            
            # ETA
            eta = calculate_eta(file_size_mb)
            if eta:
                eta_str = str(eta).split('.')[0]  # Remove microseconds
                eta_time = (datetime.now() + eta).strftime("%H:%M UTC")
                print_line("ETA", f"{eta_str} remaining (~{eta_time})", 'ok' if eta.total_seconds() < 7200 else 'warning')
            
            if mod_time:
                time_since = datetime.now() - mod_time
                if time_since.total_seconds() < 60:
                    last_update = f"{int(time_since.total_seconds())}s ago"
                else:
                    last_update = f"{int(time_since.total_seconds()/60)}min ago"
                print_line("Last Update", last_update, 'ok' if time_since.total_seconds() < 120 else 'warning')
        
        # ===== WATCHER STATUS =====
        print_section("🔔 AUTO-TRIGGER WATCHER")
        
        watcher_status = 'running' if watcher_running else 'stopped'
        watcher_status_emoji = 'ok' if watcher_running else 'warning'
        print_line("Status", watcher_status, watcher_status_emoji)
        print_line("Function", "Polling every 30s for parquet >10MB", 'ok')
        print_line("Auto-Trigger", "src/backtest_full.py (when ready)", 'pending' if file_size_mb and file_size_mb < 10 else 'ok')
        
        # ===== BACKTEST STATUS =====
        print_section("⚗️  BACKTEST EXECUTION")
        
        backtest_status, _ = get_backtest_status()
        
        if backtest_status == 'pending':
            print_line("Status", "Pending (waiting for data)", 'pending')
            print_line("Combinations", "63 (9 strategies × 7 timeframes)", 'ok')
            print_line("Expected Runtime", "~45 minutes", 'gray')
            print_line("Output", "results/backtest_full_results.csv", 'gray')
        elif backtest_status == 'running':
            print_line("Status", "Running NOW!", 'running')
            print_line("Combinations", "63 (9 strategies × 7 timeframes)", 'ok')
            print_line("Expected Runtime", "~45 minutes from start", 'warning')
            print_line("Output", "results/backtest_full_results.csv", 'gray')
        elif backtest_status == 'completed':
            print_line("Status", "COMPLETED ✓", 'ok')
            print_line("Results File", "results/backtest_full_results.csv", 'ok')
            
            try:
                results = pd.read_csv('/workspaces/trading-lab/results/backtest_full_results.csv')
                passing = len(results[results['all_objectives_ok'] == True])
                print_line("Strategies Passing", f"{passing}/63 meet objectives", 'ok' if passing > 0 else 'warning')
                
                if passing > 0:
                    best = results[results['all_objectives_ok'] == True].nlargest(1, 'sharpe_ratio').iloc[0]
                    print_line("Best Strategy", f"{best['version']} ({best['timeframe']})", 'ok')
                    print_line("Best Sharpe", f"{best['sharpe_ratio']:.2f}", 'ok')
            except Exception as e:
                print_line("Results", "Available (parsing error)", 'warning')
        
        # ===== RECENT LOG =====
        print_section("📋 RECENT LOG ACTIVITY")
        
        log_lines = get_download_log()
        if log_lines:
            for line in log_lines[-3:]:
                line_clean = line.strip()
                if line_clean:
                    # Truncate to fit
                    if len(line_clean) > 72:
                        line_clean = line_clean[:69] + "..."
                    print(f"│ {line_clean:<72} │")
        else:
            print(f"│ {'(No log activity yet)':^72} │")
        
        # ===== FOOTER =====
        print(f"│ {Colors.GRAY}Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Iteration #{iteration}{Colors.ENDC:72} │")
        print(f"└" + "─"*74 + "┘")
        
        print(f"\n{Colors.YELLOW}Press Ctrl+C to exit monitoring{Colors.ENDC}\n")
        
        # Wait for next update
        try:
            time.sleep(10)  # Update every 10 seconds
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}✓ Monitoring stopped{Colors.ENDC}\n")
            sys.exit(0)

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}✓ Monitoring stopped{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.ENDC}")
        sys.exit(1)
