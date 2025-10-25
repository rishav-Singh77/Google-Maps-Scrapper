from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote
import re


query = input("Enter search query : ")
url = "https://www.google.co.in/maps/search/"+quote(query)

data = {
    'Name': [], 'Rating': [], 'Reviews': [], 'Address': [], 'Phone': [],
    'City': [], 'State': [], 'Pincode': []
}

start_time = time.time()

options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--enable-unsafe-webgpu")
options.add_argument("--use-gl=swiftshader")

driver = webdriver.Chrome(options=options)

driver.get(url)
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')

# Scroll the listing
MAX_SCROLLS = 50
for _ in range(MAX_SCROLLS):
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
    time.sleep(1)

listings = driver.find_elements(By.CLASS_NAME, 'hfpxzc')
print(f"Found {len(listings)} listings...")

links = []
for l in listings:
    href = l.get_attribute("href")
    if href: links.append(href)

for i, link in enumerate(links):
    try:
        driver.get(link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'DUwDvf')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        name = soup.find('h1', class_='DUwDvf lfPIob')
        name = name.get_text(strip=True) if name else 'N/A'

        rating_tag = soup.find('span', class_='MW4etd')
        rating = rating_tag.get_text(strip=True) if rating_tag else 'N/A'

        reviews_tag = soup.find('span', class_='UY7F9')
        reviews = reviews_tag.get_text(strip=True) if reviews_tag else 'N/A'

        phone_tag = soup.find('button', attrs={'aria-label': lambda x: x and 'Phone:' in x})
        phone = phone_tag['aria-label'].replace('Phone: ', '').strip() if phone_tag else 'N/A'

        addr_tag = soup.find('button', attrs={'aria-label': lambda x: x and 'Address:' in x})
        address = addr_tag['aria-label'].replace('Address: ', '').strip() if addr_tag else 'N/A'

        # Extract city, state, pincode
        city = state = pincode = 'N/A'
        if address != 'N/A':
            pin_match = re.search(r"\b\d{6}\b", address)
            pincode = pin_match.group() if pin_match else 'N/A'
            parts = [p.strip() for p in address.split(',') if p.strip()]
            if parts:
                if pincode != 'N/A' and len(parts) >= 3:
                    if len(parts[-1]) >= 7:
                        state = parts[-1].replace(pincode, '').strip()
                        city = parts[-2]
                    else:
                        state = parts[-2]
                        city = parts[-3]
                elif len(parts) >= 2:
                    state = parts[-1]
                    city = parts[-2]

        # Append to data
        data['Name'].append(name)
        data['Rating'].append(rating)
        data['Reviews'].append(reviews)
        data['Phone'].append(phone)
        data['Address'].append(address)
        data['City'].append(city)
        data['State'].append(state)
        data['Pincode'].append(pincode)

        print(f"{i+1}. {name} — ✅")

    except Exception as e:
        print(f"❌ Failed to process detail page: {e}")
        continue

driver.quit()
df = pd.DataFrame(data)
df.to_csv("Extracted_data.csv", index=False, encoding='utf-8-sig')