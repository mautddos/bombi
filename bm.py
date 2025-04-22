import requests
import random
import time
import threading
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

console = Console()

def generate_token():
    versions = ('1', '2', '5', '6')
    prefixes = ('AAF', 'BBQ', 'BBA', 'XYZ')
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
    
    token = (
        f"{random.choice(versions)}"
        f"{random.randint(100000000, 999999999)}:"
        f"{random.choice(prefixes)}"
        f"{''.join(random.choices(chars, k=32))}"
    )
    return token

def check_token(token):
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=5
        ).json()
        
        if response.get('ok'):
            bot_info = response['result']
            console.print(Panel.fit(
                f"[bold green]VALID TOKEN FOUND![/]\n\n"
                f"🔑 [yellow]{token}[/]\n"
                f"🆔 [cyan]{bot_info['id']}[/]\n"
                f"👤 @{bot_info.get('username', 'N/A')}\n"
                f"📛 {bot_info.get('first_name', 'N/A')}",
                title="✅ SUCCESS",
                border_style="green"
            ))
            return True
    except:
        pass
    return False

def main():
    console.print(Panel.fit(
        "[bold red]TELEGRAM BOT TOKEN CHECKER[/]",
        border_style="red"
    ))
    
    threads = int(input("Enter number of threads (recommended 10-50): "))
    total_tokens = int(input("Enter number of tokens to check: "))
    
    valid_count = 0
    checked = 0
    
    with Progress() as progress:
        task = progress.add_task("Checking tokens...", total=total_tokens)
        
        def worker():
            nonlocal valid_count, checked
            while checked < total_tokens:
                token = generate_token()
                if check_token(token):
                    valid_count += 1
                checked += 1
                progress.update(task, advance=1)
        
        thread_pool = []
        for _ in range(threads):
            t = threading.Thread(target=worker)
            t.start()
            thread_pool.append(t)
        
        for t in thread_pool:
            t.join()
    
    console.print(Panel.fit(
        f"Scan completed!\n"
        f"Total checked: [cyan]{checked}[/]\n"
        f"Valid tokens: [green]{valid_count}[/]",
        title="📊 RESULTS",
        border_style="blue"
    ))

if __name__ == "__main__":
    main()
