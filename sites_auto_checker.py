import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === 1. Загрузка конфигурации ===
with open("data.json", "r", encoding="utf-8") as f:
    config = json.load(f)

url = config["url"]
field = config["fields"][0]
selector = field["selector"]
values = field["values"]
submit_selector = config["submit"]
blocked_text = config.get("blocked_text", "Орган, принявший решение о внесении в реестр")
pause_seconds = config.get("pause_seconds", 15)

# === 2. Настройка Selenium ===
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

print(f"🌐 Загружаю сайт: {url}")
driver.get(url)
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
print("✅ Страница загружена")

# === 3. Цикл по ссылкам ===
for i, value in enumerate(values, start=1):
    print(f"\n🔹 Проверяю ссылку {i}/{len(values)}: {value}")

    # Очистка поля и ввод значения
    try:
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        element.clear()
        element.send_keys(value)
        print(f"➡️ Введено: {value}")
    except Exception as e:
        print(f"⚠ Ошибка при вводе: {e}")
        continue

    # === Блок капчи ===
    while True:
        print("🧩 Введи капчу вручную (или подожди, скрипт проверит через 6 сек).")
        time.sleep(6)

        try:
            # Найти инпут капчи (по name, id или типу — подстрой при необходимости)
            captcha_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[name*='captcha'], input[id*='captcha']")
            captcha_value = ""
            for inp in captcha_inputs:
                v = inp.get_attribute("value")
                if v and len(v.strip()) == 6:
                    captcha_value = v.strip()
                    break

            if captcha_value:
                print(f"🤖 Обнаружен ввод капчи ({captcha_value}) → автоотправка")
                button = driver.find_element(By.CSS_SELECTOR, submit_selector)
                button.click()
                print("🚀 Кнопка отправки нажата автоматически")
            else:
                input("⏸ Капча не заполнена. Введи вручную и нажми Enter → ")
                button = driver.find_element(By.CSS_SELECTOR, submit_selector)
                button.click()
                print("🚀 Кнопка нажата вручную")

        except Exception as e:
            print(f"⚠ Ошибка при обработке капчи: {e}")
            continue

        time.sleep(3)

        # Проверка на неверный защитный код
        try:
            modal = driver.find_element(By.ID, "divMsgModal")
            modal_text = modal.text.strip().lower()
            if "неверно указан защитный код" in modal_text:
                print("⚠ Неверно введён код. Повторите ввод капчи.")
                try:
                    close_btn = modal.find_element(By.XPATH, ".//button | .//input[@value='Закрыть']")
                    close_btn.click()
                except:
                    driver.execute_script("document.getElementById('divMsgModal').style.display='none';")
                time.sleep(1)
                continue  # Повторяем попытку
        except:
            pass

        break  # Всё успешно — выходим из while

    # Небольшая задержка для загрузки результатов
    time.sleep(5)

    # Проверка на блокировку ресурса
    wait = WebDriverWait(driver, 20)
    page_source = driver.page_source.lower()
    print("page_source = ", page_source)

    if blocked_text.lower() in page_source:
        try:
            # Найти элемент с текстом блокировки
            element = driver.find_element(By.XPATH, f"//*[contains(translate(., 'ОРГАНПРИНЯВШИЙРЕШЕНИЕОВНЕСЕНИИ', 'органпринявшийрешениеовнесении'), '{blocked_text.lower()}')]")
            screenshot_path = f"screens/blocked_{i}_{int(time.time())}.png"
            element.screenshot(screenshot_path)
            print(f"📸 Сохранён фрагмент страницы: {screenshot_path}")
        except Exception as e:
            print(f"⚠ Не удалось сделать скриншот блока: {e}")
            fallback_path = f"blocked_full_{i}_{int(time.time())}.png"
            driver.save_screenshot(fallback_path)

            print(f"📸 Сохранён полный скриншот: {fallback_path}")
        time.sleep(pause_seconds)
    else:
        print("✅ Ресурс не заблокирован")

    # Возврат на главную страницу
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

print("\n🎯 Проверка завершена.")
driver.quit()
