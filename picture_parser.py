from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import requests

def download_images(search_query, folder_name, num_images=25):
    # Настройка драйвера
    driver = webdriver.Chrome()  # Убедитесь, что у вас установлен ChromeDriver
    driver.get("https://unsplash.com/")

    # Поиск по ключевому слову
    search_box = driver.find_element(By.NAME, "searchKeyword")
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)  # Подождать загрузки страницы

    # Прокрутка страницы для подгрузки изображений
    for _ in range(5):  # Прокручиваем 5 раз (или больше при необходимости)
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(2)

    # Сбор ссылок на изображения
    image_elements = driver.find_elements(By.CSS_SELECTOR, "img._2zEKz")  # CSS-селектор для картинок
    image_urls = [img.get_attribute("src") for img in image_elements[:num_images]]

    # Создание папки для сохранения изображений
    os.makedirs(folder_name, exist_ok=True)

    # Загрузка изображений
    for idx, url in enumerate(image_urls):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(os.path.join(folder_name, f"{search_query}_{idx + 1}.jpg"), "wb") as f:
                    f.write(response.content)
                print(f"Downloaded {search_query}_{idx + 1}.jpg")
        except Exception as e:
            print(f"Failed to download image {idx + 1}: {e}")

    driver.quit()

if __name__ == "__main__":
    tags = ["nature", "technology", "people"]  # Список ключевых слов
    for tag in tags:
        download_images(search_query=tag, folder_name=f"images_{tag}")
