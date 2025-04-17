#!/usr/bin/env python3
"""
Instagram Proxy Checker v3.3
With Telegram Bot Integration
"""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import os
import sys
from colorama import init, Fore, Back, Style
from typing import List, Tuple, Dict, Set

# ========== INITIALIZATION ========== #
init(autoreset=True)

# ========== CONSTANTS ========== #
MAX_WORKERS = 50               # Increased thread pool size
TIMEOUT = 8                    # Reduced timeout
RESULTS_FILE = "instagram_proxies.txt"
LOG_FILE = "proxy_checker.log"
UNIQUE_PROXIES_FILE = "unique_proxies.txt"

# Telegram Bot Configuration
BOT_TOKEN = "8089727906:AAFLDk8a_V0EbNchoANhR-MaF8mPaJ5bXfM"
CHAT_ID = "8167507955"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

# ========== USER AGENTS ========== #
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Instagram 289.0.0.77.109 Android (33/13; 480dpi; 1080x2400; Google/google; Pixel 7; panther; panther; en_US)",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15"
]

# ========== UPDATED PROXY SOURCES ========== #
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http",
    "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
]

# ========== COLOR SCHEME ========== #
COLOR = {
    "success": Fore.GREEN + Style.BRIGHT,
    "error": Fore.RED + Style.BRIGHT,
    "warning": Fore.YELLOW + Style.BRIGHT,
    "info": Fore.CYAN + Style.BRIGHT,
    "proxy": Fore.MAGENTA,
    "highlight": Fore.WHITE + Back.BLUE,
    "timestamp": Fore.LIGHTBLACK_EX
}

# ========== CORE FUNCTIONS ========== #
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    banner = f"""
{COLOR['highlight']} ╔════════════════════════════════════════════════╗
{COLOR['highlight']} ║      INSTAGRAM PROXY CHECKER v3.3 (24/7)       ║
{COLOR['highlight']} ║    • Telegram Updates • Faster Checking •      ║
{COLOR['highlight']} ╚════════════════════════════════════════════════╝
    """
    print(banner)

def log(message: str, level: str = "info") -> None:
    timestamp = f"{COLOR['timestamp']}[{time.strftime('%H:%M:%S')}]"
    colored_msg = f"{timestamp} {COLOR[level]}{message}"
    print(colored_msg)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def get_random_headers() -> Dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest"
    }

# ========== TELEGRAM FUNCTIONS ========== #
def send_telegram_message(text: str) -> bool:
    try:
        params = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params=params,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        log(f"Failed to send Telegram message: {str(e)}", "error")
        return False

def send_telegram_file(filename: str, caption: str = "") -> bool:
    try:
        with open(filename, "rb") as file:
            files = {"document": file}
            data = {"chat_id": CHAT_ID, "caption": caption}
            response = requests.post(
                TELEGRAM_API_URL,
                files=files,
                data=data,
                timeout=20
            )
            return response.status_code == 200
    except Exception as e:
        log(f"Failed to send Telegram file: {str(e)}", "error")
        return False

# ========== PROXY MANAGEMENT ========== #
def fetch_proxies_from_source(url: str) -> Set[str]:
    try:
        response = requests.get(url, headers=get_random_headers(), timeout=15)
        response.raise_for_status()
        
        if "geonode" in url:
            return {f"{p['ip']}:{p['port']}" for p in response.json().get("data", [])}
        else:
            proxies = set()
            for line in response.text.splitlines():
                if ":" in line and "." in line:
                    proxy = line.strip()
                    if proxy.count(":") == 1:
                        proxies.add(proxy)
            return proxies
            
    except Exception as e:
        log(f"Failed {url.split('/')[2]}: {str(e)}", "warning")
        return set()

def fetch_fresh_proxies() -> List[str]:
    log("Fetching proxies from updated sources...", "info")
    
    proxies = set()
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_proxies_from_source, url): url for url in PROXY_SOURCES}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                new_proxies = future.result()
                proxies.update(new_proxies)
                log(f"Acquired {len(new_proxies)} proxies from {url.split('/')[2]}", "success")
            except Exception as e:
                log(f"Error fetching from {url.split('/')[2]}: {str(e)}", "error")
            time.sleep(0.5)  # Reduced delay
    
    return list(proxies)

# ========== PROXY VALIDATION ========== #
def verify_instagram(proxy: str) -> Tuple[bool, int]:
    test_url = "https://www.instagram.com/data/shared_data/"
    try:
        start_time = time.time()
        response = requests.get(
            test_url,
            proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
            headers=get_random_headers(),
            timeout=TIMEOUT
        )
        
        if response.status_code == 200 and "config" in response.text:
            return (True, int((time.time() - start_time) * 1000))
    except:
        pass
    
    return (False, 0)

# ========== MAIN SYSTEM ========== #
def main_loop():
    print_banner()
    log("Starting Instagram Proxy Checker with Telegram integration", "success")
    send_telegram_message("🚀 <b>Instagram Proxy Checker Started</b> 🚀")
    
    # Initialize files
    for file in [RESULTS_FILE, LOG_FILE, UNIQUE_PROXIES_FILE]:
        if os.path.exists(file):
            os.remove(file)
    
    while True:
        try:
            # Get fresh proxies
            proxies = fetch_fresh_proxies()
            if not proxies:
                log("No proxies acquired. Retrying...", "warning")
                send_telegram_message("⚠️ No proxies acquired. Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            log(f"Testing {len(proxies)} fresh proxies against Instagram...", "info")
            send_telegram_message(f"🔍 Testing {len(proxies)} fresh proxies against Instagram...")
            
            # Validate proxies
            working_proxies = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_proxy = {executor.submit(verify_instagram, proxy): proxy for proxy in proxies}
                
                for future in as_completed(future_to_proxy):
                    proxy = future_to_proxy[future]
                    try:
                        is_valid, speed = future.result()
                        if is_valid and speed < 8000:  # Filter slow proxies
                            log(f"Valid {COLOR['proxy']}{proxy.ljust(21)} {COLOR['success']}({speed}ms)", "success")
                            working_proxies.append((proxy, speed))
                    except Exception as e:
                        pass
            
            # Save results
            if working_proxies:
                with open(RESULTS_FILE, "a") as f:
                    for proxy, speed in working_proxies:
                        f.write(f"{proxy}|{speed}\n")
                
                with open(UNIQUE_PROXIES_FILE, "a") as f:
                    unique_proxies = set()
                    if os.path.exists(UNIQUE_PROXIES_FILE):
                        with open(UNIQUE_PROXIES_FILE, "r") as f_read:
                            unique_proxies.update(line.split("|")[0] for line in f_read.readlines())
                    
                    new_proxies = 0
                    for proxy, speed in working_proxies:
                        if proxy not in unique_proxies:
                            f.write(f"{proxy}|{speed}\n")
                            new_proxies += 1
                    
                    log(f"Added {new_proxies} new unique proxies", "info")
            
            summary_msg = (
                f"<b>Proxy Check Results</b>\n\n"
                f"✅ Working: <b>{len(working_proxies)}</b>\n"
                f"❌ Failed: <b>{len(proxies) - len(working_proxies)}</b>\n"
                f"🆕 New: <b>{new_proxies}</b>\n"
                f"📊 Total Unique: <b>{len(unique_proxies) + new_proxies}</b>"
            )
            
            log(f"\nResults: {len(working_proxies)}/{len(proxies)} working proxies", "highlight")
            send_telegram_message(summary_msg)
            
            # Send the results file if we have new proxies
            if new_proxies > 0:
                if send_telegram_file(RESULTS_FILE, f"📄 {new_proxies} new working proxies"):
                    log("Sent results to Telegram", "success")
                else:
                    log("Failed to send results to Telegram", "error")
            
            log("Starting next check...\n", "info")
            time.sleep(60)  # Wait 1 minute before next check
            
        except KeyboardInterrupt:
            log("\nStopped by user. Exiting...", "error")
            send_telegram_message("🛑 <b>Proxy Checker Stopped</b> by user")
            sys.exit(0)
        except Exception as e:
            log(f"Critical error: {str(e)}. Restarting...", "error")
            send_telegram_message(f"🔥 <b>Critical Error</b>: {str(e)}\nRestarting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    try:
        # Test Telegram connection
        if send_telegram_message("🔌 <b>Proxy Checker Connection Test</b>\nBot is online and ready!"):
            log("Telegram connection test successful", "success")
        else:
            log("Telegram connection failed - continuing without notifications", "warning")
        
        main_loop()
    except Exception as e:
        log(f"Fatal error: {str(e)}", "error")
        send_telegram_message(f"💀 <b>Fatal Error</b>: {str(e)}\nProxy Checker has crashed!")
        sys.exit(1)
