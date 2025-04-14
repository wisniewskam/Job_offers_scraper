from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import sqlite3


# Loader of keywords
def load_keywords_from_file(file_path="keywords.txt"):
    with open(file_path, "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip()]
    return keywords

# Connection to SQLite database
def connect_to_db(conn, cur):
    cur.execute('''
        CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        title TEXT,
        company TEXT,
        date TEXT,
        link TEXT
    )
    ''')
    conn.commit()

# Save keyword, title, company, expiration date and link to SQLite database
def save_to_db(cur, keyword, title, company, date, link):
    try:
        cur.execute('''
            INSERT OR IGNORE INTO offers (keyword, title, company, date, link)
            VALUES (?, ?, ?, ?, ?)
        ''', (keyword, title, company, date, link))
        cur.connection.commit()
    except Exception as e:
        print(f"Error while saving to database: {e}")


def search_jobs(keyword, writer):
    conn = sqlite3.connect('job_offers.sqlite')
    cur = conn.cursor()
    connect_to_db(conn, cur)

    print(f"\nSearch for jobs with: {keyword}")

    # Configuration of Chrome
    options = Options()
    # options.add_argument("--headless")  # in the background

    driver = webdriver.Chrome(options=options)

    # Link with keywords and location: Warszawa
    encoded_keyword = keyword.replace(" ", "%20")
    url = f"https://www.pracuj.pl/praca/{encoded_keyword};kw/warszawa;wp?rd=30"

    driver.get(url)
    time.sleep(3) # sec

    # Cookie banner handling
    try:
        wait = WebDriverWait(driver, 3)
        cookie_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test="button-submitCookie"]')))
        cookie_btn.click()
        time.sleep(5)
    except:
        print("No cookies detected")

    initial_count = len(driver.find_elements(By.CSS_SELECTOR, 'a[data-test="link-offer"]'))

    for i in range(initial_count):
        offer_links = driver.find_elements(By.CSS_SELECTOR, 'a[data-test="link-offer"]')

        offer = offer_links[i]

        driver.execute_script("arguments[0].click();", offer)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        link = driver.current_url

        # Find elements
        try:
            title = driver.find_element(By.CSS_SELECTOR, "[data-test='text-positionName']").text
            company = driver.find_element(By.CSS_SELECTOR, "[data-test='text-employerName']").text
            date = driver.find_element(By.CSS_SELECTOR, "div.lowercase-description.d1urwcho").text

            print(title, company, date, link)
            writer.writerow([keyword, title, company, date, link])
        except Exception as e:
            print(f"Error while scrapping in the offer: {e}")

        # Save above elements to db
        try:
            save_to_db(cur, keyword, title, company, date, link)
            print("Saved to sql db")
        except Exception as e:
            print(f"Error while saving the offer in sqlite db: {e}")
            
        time.sleep(2)
        driver.back()
        time.sleep(2)

    conn.close()
    driver.quit()

if __name__ == "__main__":
    keywords = load_keywords_from_file("keywords.txt")

    # Save to csv
    with open("offers.csv", mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Keyword", "Title", "Company", "Expiration", "Link"])

        for kw in keywords:
            search_jobs(kw, writer)

    print("\nSaved in 'offers.csv'")
