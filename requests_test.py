import re
import sys
import requests
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

host_pattern = r'https://[^\s/$.?#].[^\s]*$'
def check_format(value):
    for i in value.split(','):
        if not re.match(host_pattern, i):
            raise argparse.ArgumentTypeError("В строке содержатся невалидные ссылки")
    return value

parser = argparse.ArgumentParser(description="Доступность серверов")
group = parser.add_mutually_exclusive_group(required=False)
group.add_argument("-H", type=check_format, help="Хосты")
parser.add_argument("-C", type=int, help="Количество запросов", default=1)
group.add_argument("-F", help="Хосты")
parser.add_argument("-O", nargs= '?', default=sys.stdout, help="Вывод в файл")
args = parser.parse_args()
count = args.C
if args.F:
    try:
        with open(args.F, 'r', encoding='utf-8') as f:
            servers = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Ошибка: Файл {args.F} не найден")
        sys.exit(1)
elif args.H:
    servers = args.H.split(',')
else:
    print("Необходимо указать либо -F, либо -H")
    sys.exit(1)

def check_server(url, count, text=""):
    success = 0
    failed = 0
    errors = 0
    latencies = []
    for i in range(0, count):
        try:
            start_time = time.time()

            response = requests.get(url)
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            latencies.append(latency)

            if response.status_code == 200:
                success += 1
            elif response.status_code == 400 or response.status_code == 500:
                failed += 1
            else:
                print(f"[WARN] {url} - Код: {response.status_code}")

        except requests.exceptions.RequestException as e:
            errors +=1
    text += "\nНOST = " + str(url) + "\nSUCCESS = " + str(success) + "\nFAILED = " + str(failed) + "\nERRORS = " + str(errors)
    if latencies != []:
        text += "\nMIN = " + str(min(latencies)) + "\nMAX = " + str(max(latencies)) + "\nAVG = " + str(sum(latencies) / len(latencies))

    return text

if __name__ == "__main__":
    print("--- Запуск проверки серверов ---")
    result = ""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [ executor.submit(check_server, server, count) for server in servers]
        for future in as_completed(futures):
            result += future.result()

    if args.O == sys.stdout:
        output_file = sys.stdout
        print(result)
    else:
        output_file = open(args.O,'w', encoding='utf-8')
        print("Вывод в файл:", args.O)
        output_file.write(result)
        output_file.close()
    print("--- Проверка завершена ---")

