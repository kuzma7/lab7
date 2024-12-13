import asyncio
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging
import csv
import time

# Настройка логирования
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('anekdotov_scraper.log', mode='a', encoding='utf-8'),
                        logging.StreamHandler()  # Вывод в консоль
                    ])

ua = UserAgent(min_percentage=10)
base_url = 'https://anekdotov.me/'

# Функция для получения супа
async def get_soup(session, url: str):
    try:
        async with session.get(url, headers={'User-Agent': ua.random}) as response:
            response.encoding = 'utf-8'
            if response.status == 200:
                logging.info(f"Запрос на {url} выполнен успешно.")
                html = await response.text()
                return BeautifulSoup(html, 'lxml')
            else:
                logging.warning(f"Ошибка при запросе на {url}. Код статуса: {response.status}")
                return None
    except Exception as e:
        logging.error(f"Ошибка при запросе на {url}: {e}")
        return None


# Функция для получения общего числа страниц
async def get_all_count_page(session):
    soup = await get_soup(session, base_url)
    if soup:
        try:
            total_pages = int(soup.find('span', attrs={'random'}).text)
            logging.info(f"Общее количество страниц: {total_pages}")
            return total_pages
        except Exception as e:
            logging.error(f"Ошибка при извлечении количества страниц: {e}")
    return 0


# Функция для получения анекдотов с одной страницы
async def get_anecdotes_from_page(session, page_num):
    page_url = f'{base_url}page/{page_num}/'
    logging.info(f"Начинаем обработку страницы {page_url}.")
    soup = await get_soup(session, page_url)
    if soup:
        anecdotes = []
        # Извлекаем элементы анекдотов
        results = soup.find_all('article')
        for result in results:
            try:
                # Извлекаем текст анекдота
                anekdot_text = result.find('p', class_='short-desc').text.strip()
                # Извлекаем категорию анекдота
                category = result.find('a', rel='nofollow').text.strip()
                anecdotes.append((category, anekdot_text))
            except Exception as e:
                logging.warning(f"Ошибка при обработке элемента анекдота: {e}")
        logging.info(f"Извлечено {len(anecdotes)} анекдотов с страницы {page_num}.")
        return anecdotes
    return []


# Функция для записи анекдотов в файл
async def write_data(anecdotes):
    try:
        with open('res.csv', 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            # Пишем заголовки
            writer.writerow(["Категория", "Анекдот"])
            # Пишем данные
            writer.writerows(anecdotes)
        logging.info("Данные успешно записаны в файл 'res.csv'.")
    except Exception as e:
        logging.error(f"Ошибка при записи в файл: {e}")


# Функция для сбора анекдотов со всех страниц
async def collect_all_anecdotes():
    all_anecdotes = []

    async with aiohttp.ClientSession() as session:
        total_pages = await get_all_count_page(session)
        tasks = []

        # Запуск асинхронных задач для каждой страницы
        for page in range(1, total_pages + 1):
            tasks.append(get_anecdotes_from_page(session, page))

        # Получаем результаты всех задач
        pages_anecdotes = await asyncio.gather(*tasks)

        # Объединяем анекдоты со всех страниц
        for anecdotes in pages_anecdotes:
            all_anecdotes.extend(anecdotes)

        # Записываем все анекдоты в файл
        await write_data(all_anecdotes)


# Функция для поиска анекдотов по слову
def find_anecdotes(word, anecdotes, count=5):
    filtered_anecdotes = [anekdot for category, anekdot in anecdotes if word.lower() in anekdot.lower()]
    logging.info(f"Найдено {len(filtered_anecdotes)} анекдотов, содержащих слово '{word}'.")
    return filtered_anecdotes[:count]


# Главная асинхронная функция
async def main():
    # Сбор всех анекдотов с сайта
    await collect_all_anecdotes()

    # Запрашиваем слово для поиска
    word_to_search = input("Введите слово для поиска: ")

    # Читаем данные из файла и ищем анекдоты по слову
    with open('res.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)  # Пропускаем заголовок
        all_anecdotes = [(row[0], row[1]) for row in reader]

    # Находим и выводим первые 5 анекдотов, содержащих это слово
    result = find_anecdotes(word_to_search, all_anecdotes)

    if result:
        logging.info(f"Первые 5 анекдотов с '{word_to_search}':")
        for idx, anekdot in enumerate(result, 1):
            print(f"{idx}. {anekdot}")
        logging.info("Показаны анекдоты.")
    else:
        logging.warning(f"Не найдено анекдотов, содержащих слово '{word_to_search}'.")


# Запуск асинхронной программы
if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    logging.info(f"Время выполнения: {time.time() - start_time} секунд.")
