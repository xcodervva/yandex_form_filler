import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === 1. Загрузка конфигурации ===
with open("announcement.json", "r", encoding="utf-8") as f:
    config = json.load(f)

url = config["url"]
dashboard = config["dashboard"]
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

days_range = [x.lower() for x in config.get("days_range", ["сегодня"])]

# === 3. Загрузка шаблонов ===
with open("patterns.txt", "r", encoding="utf-8") as f:
    patterns = [line.strip().lower() for line in f if line.strip()]

# === 4. Поиск таблиц объявлений по диапазону ===
tables = driver.find_elements(By.CSS_SELECTOR, "table[style*='width: 445px']")
filtered_tables = []

for t in tables:
    try:
        header_el = t.find_element(By.XPATH, "preceding-sibling::b[1]")
        if header_el and any(day in header_el.text.lower() for day in days_range):
            filtered_tables.append(t)
    except:
        continue

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

    for pattern in patterns:
        if pattern in text:
            with open("matched_links.log", "a", encoding="utf-8") as log:
                log.write(f"{url} | Фраза: {pattern}\n")
            print(f"✅ Совпадение найдено: {pattern}")
            break

    time.sleep(1)
    driver.back()
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

print("🏁 Проверка завершена.")
driver.quit()