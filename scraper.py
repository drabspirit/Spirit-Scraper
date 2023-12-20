import requests
from lxml import html
import re
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

tf2_key_price = None

def clean_game_name(game_name):
    game_name = ' '.join(game_name.split())
    cleaned_game_name = re.sub(r'[^a-zA-Z0-9\s-]', '', game_name)
    cleaned_game_name = '-'.join(cleaned_game_name.split())
    cleaned_game_name = re.sub(r'-+', '-', cleaned_game_name)
    return cleaned_game_name.lower()

def generate_url(game_name):
    base_url = 'https://gg.deals/game/'
    cleaned_name = clean_game_name(game_name)
    return f'{base_url}{cleaned_name}/'

def scrape_tf2_key_price():
    global tf2_key_price
    if tf2_key_price is not None:
        return tf2_key_price

    url = 'https://backpack.tf/stats/Unique/Mann%20Co.%20Supply%20Crate%20Key/Tradable/Craftable'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        response = session.get(url, headers=headers)
        print(f"Request status code: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            element = soup.select_one("body > main > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1) > a:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1)")
            if element:
                tf2_key_price = element.text.strip().replace('~', '').replace('$', '')
                return tf2_key_price
            else:
                return "TF2 key price element not found"
        else:
            return f"Failed to fetch TF2 key price. Status code: {response.status_code}"

    except RequestException as e:
        return f"An error occurred while scraping TF2 key price: {e}"

def scrape_price(game_name):
    try:
        cleaned_game_name = clean_game_name(game_name)
        print(f"Cleaned game name: {cleaned_game_name}")

        url_formats = [
            f"https://gg.deals/game/{cleaned_game_name}/",
            f"https://gg.deals/game/{cleaned_game_name.replace('2', 'ii')}/",
            f"https://gg.deals/game/{cleaned_game_name.replace('2', 'two')}/"
        ]

        for url in url_formats:
            print(f"Trying URL: {url}")

            try:
                response = session.get(url)
            except RequestException as request_exception:
                print(f"An error occurred while accessing {url}: {request_exception}")
                continue

            if response.status_code == 200:
                print(f"URL {url} succeeded")

                tree = html.fromstring(response.content)
                price_element = tree.xpath("//span[@class='price']")

                if price_element:
                    price = price_element[0].text_content().strip()
                    return price
                else:
                    return None
            elif response.status_code == 404:
                print(f"URL {url} not found")
                continue
            else:
                return None

        return None
    except Exception as e:
        print(f"An error occurred while scraping price for {game_name}: {str(e)}")
        return None

def scrape_prices_from_file(input_file_path, output_file_path, retry_file_path):
    try:
        tf2_key_price = scrape_tf2_key_price()

        with open(input_file_path, "r") as file:
            lines = file.readlines()

        with open(output_file_path, "w") as output_file, open(retry_file_path, "w") as retry_file:
            output_file.write(f"TF2 Key Price: ${tf2_key_price}\n\n")
            output_file.write("Game Name | Price | TF2 Key/Price\n\n")

            for line in lines:
                # Skip empty lines
                if not line.strip():
                    continue

                # Process each non-empty line here
                cleaned_line = line.strip()  # Remove leading/trailing whitespace
                game_price = scrape_price(cleaned_line)  # Scrape price for the game
                if game_price:
                    # Remove non-numeric characters (e.g., '$') from the price before converting to float
                    cleaned_game_price = re.sub(r'[^\d.]', '', game_price)
                    ratio = round(float(cleaned_game_price) / float(tf2_key_price), 2)
                    output_line = f"{cleaned_line} | {game_price} | {ratio}\n"
                    output_file.write(output_line)
                    print(f"Processed: {output_line.strip()}")  # Print the processed line
                else:
                    retry_file.write(f"{cleaned_line}\n")
                    print(f"Game not found: {cleaned_line}")  # Print a message for games not found
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def main():
    input_method = input("Choose input method (manual/json/txt): ").strip().lower()

    if input_method == "manual":
        game_name = input("Enter game name: ").strip()
        price = scrape_price(game_name)
        print(f"The price of {game_name} is: {price}")
    elif input_method == "txt" or input_method == "json":
        current_dir = os.path.dirname(os.path.abspath(__file__))
        input_file_name = f"list.{input_method}"
        input_file_path = os.path.join(current_dir, input_file_name)
        output_file_path = os.path.join(current_dir, f"output.{input_method}")
        retry_file_path = os.path.join(current_dir, f"retry.{input_method}")
        scrape_prices_from_file(input_file_path, output_file_path, retry_file_path)
    else:
        print("Invalid input method.")

if __name__ == "__main__":
    main()
