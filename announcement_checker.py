import json
import time
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

### 
### python announcement_checker.py --days "Сегодня, Вчера"
### или если хочешь из конфигурации:
### python announcement_checker.py

# === 0. Аргументы командной строки ===
parser = argparse.ArgumentParser(description="Парсер объявлений с фильтром по дням")
parser.add_argument("--days", type=str, help="Диапазон дней, например: 'Сегодня, Вчера'")
args = parser.parse_args()

# === 1. Загрузка конфигурации ===
with open("announcement.json", "r", encoding="utf-8") as f:
    config = json.load(f)

url = config["url"]
dashboard = config["dashboard"]

# Если аргумент --days передан — используем его, иначе из конфигурации
if args.days:
    days_range = [x.strip().lower() for x in args.days.split(",")]
else:
    days_range = [x.lower() for x in config.get("days_range", ["Сегодня"])]

print(f"📅 Диапазон поиска: {', '.join(days_range)}")

selectorLogin = config["selectorLogin"]
valueLogin = config["valueLogin"]
selectorPass = config["selectorPass"]
valuePass = config["valuePass"]
submit_selector = config["submit"]
pause_seconds = config.get("pause_seconds", 15)

# === 2. Настройка Selenium ===
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

print(f"🌐 Загружаю сайт: {url}")
driver.get(url)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
print("✅ Страница загружена")

element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectorLogin)))
element.clear()
element.send_keys(valueLogin)
time.sleep(3)

element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selectorPass)))
element.clear()
element.send_keys(valuePass)
time.sleep(3)

button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, submit_selector)))
driver.execute_script("arguments[0].scrollIntoView(true);", button)
time.sleep(3)
driver.execute_script("arguments[0].click();", button)

time.sleep(3)
print(f"🌐 Загружаю объявления: {dashboard}")
driver.get(dashboard)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
print("✅ Страница загружена")

days_range = [x.lower() for x in config.get("days_range", ["Сегодня"])]

# === 3. Загрузка шаблонов ===
time.sleep(5)

patterns = []

with open("patterns.txt", "r", encoding="utf-8") as f:
    block = []
    for line in f:
        line = line.strip().lower()
        if not line:
            if block:
                patterns.append(block)
                block = []
        else:
            block.append(line)
    if block:
        patterns.append(block)

# === 4. Поиск таблиц объявлений по диапазону ===
tables = driver.find_elements(By.CSS_SELECTOR, "table[style*='width: 445px']")

filtered_tables = []

for day in days_range:
    try:
        headers = driver.find_elements(By.XPATH, f"//h3[contains(translate(., 'СВЯДН', 'свядн'), '{day.lower()}')]")

        for header in headers:
            try:
                # ищем таблицу внутри того же td, где и <h3>
                parent_td = header.find_element(By.XPATH, "./ancestor::td[1]")
                table = parent_td.find_element(By.XPATH, ".//table[contains(@style, 'width: 445px')]")
                filtered_tables.append(table)
                print(f"📦 Найдена таблица для '{day}'")
            except Exception as e:
                print(f"⚠️ Не удалось найти таблицу для '{day}': {e}")

    except Exception as e:
        print(f"⚠️ Ошибка при поиске блока '{day}': {e}")

print(f"📅 Обнаружено таблиц за выбранный диапазон: {len(filtered_tables)}")

# === 5. Сбор ссылок из выбранных таблиц ===
urls = []
for table in filtered_tables:
    links = table.find_elements(By.CSS_SELECTOR, "a[href]")
    urls.extend([a.get_attribute("href") for a in links])

print(f"🔗 Найдено {len(urls)} ссылок в выбранных таблицах")

# === 6. Проверка объявлений ===
for i, url in enumerate(urls, start=1):
    print(f"➡️ [{i}/{len(urls)}] Проверяю {url}")
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    text = driver.find_element(By.TAG_NAME, "body").text.lower()

    for pattern_group in patterns:
        if all(p in text for p in pattern_group):
            with open("matched_links.log", "a", encoding="utf-8") as log:
                log.write(f"{url} | Совпадение: {'; '.join(pattern_group)}\n")
            print(f"✅ Найдено совпадение по группе: {pattern_group}")
            break


    time.sleep(1)
    driver.back()
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

print("🏁 Проверка завершена.")
driver.quit()