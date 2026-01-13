import requests
from bs4 import BeautifulSoup
import json
import argparse
from datetime import datetime, timedelta
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

CONFIG_FILE = "config.json"
console = Console()

def save_credentials(login, password):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'id': login, 'password': password}, f)
    console.print("[green]✅ Данные для входа сохранены![/green]")

def load_credentials():
    if not os.path.exists(CONFIG_FILE):
        console.print("[red]❌ Ошибка: Учетные данные не найдены. Используйте: gs --s -l ID -p PASSWORD[/red]")
        return None
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_schedule(date_str):
    creds = load_credentials()
    if not creds: return

    login_url = "https://system.fgoupsk.ru/student/login"
    schedule_url = f"https://system.fgoupsk.ru/student/?mode=ucheba&d={date_str}"

    session = requests.Session()
    
    with console.status(f"[bold blue]Загрузка расписания на {date_str}..."):
        try:
            res = session.post(login_url, data={'id': creds['id'], 'password': creds['password'], 'submit': ''})
            if res.status_code != 200:
                console.print("[red]❌ Ошибка авторизации[/red]")
                return

            response = session.get(schedule_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table', class_='table table-striped')

            if len(tables) <= 1:
                console.print(Panel(f"[yellow]На {date_str} занятий не найдено или расписание еще не опубликовано.[/yellow]"))
                return

            table = tables[0]
            rows = table.find_all('tr')[1:]

            display_table = Table(title=f"📅 Расписание на {date_str}", show_header=True, header_style="bold magenta")
            display_table.add_column("№", style="dim", width=4)
            display_table.add_column("Предмет")
            display_table.add_column("Преподаватель")
            display_table.add_column("Каб.", justify="center")

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    display_table.add_row(
                        cols[0].get_text(strip=True),
                        cols[1].get_text(strip=True),
                        cols[2].get_text(strip=True),
                        cols[4].get_text(strip=True)
                    )
            
            console.print(display_table)

        except Exception as e:
            console.print(f"[red]❌ Ошибка соединения: {e}[/red]")

def main():
    parser = argparse.ArgumentParser(description="GetSchedule (gs) — Парсер расписания")
    
    # Ключи для даты
    parser.add_argument('-td', action='store_true', help='Расписание на сегодня')
    parser.add_argument('-to', action='store_true', help='Расписание на завтра')
    
    # Подкоманда для сохранения настроек
    parser.add_argument('--s', action='store_true', help='Сохранить логин и пароль')
    parser.add_argument('-l', '--login', type=str, help='ID пользователя')
    parser.add_argument('-p', '--password', type=str, help='Пароль')

    args = parser.parse_args()

    if args.s:
        if args.login and args.password:
            save_credentials(args.login, args.password)
        else:
            console.print("[red]❌ Укажите -l и -p вместе с --s[/red]")
    elif args.td:
        date = datetime.now().strftime("%d.%m.%Y")
        get_schedule(date)
    elif args.to:
        date = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        get_schedule(date)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()