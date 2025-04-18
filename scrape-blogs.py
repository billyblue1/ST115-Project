import os
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

os.makedirs("data", exist_ok=True)
outfile_path = os.path.join("data", "blogs.csv")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 10)

try:
    driver.get("https://blogs.lse.ac.uk/lse-research-blogs/")
    cards = driver.find_elements(By.CSS_SELECTOR, "div.cta-card")

    blogs = []
    for card in cards:
        base_link = card.find_element(By.TAG_NAME, "a").get_attribute("href").rstrip('/')
        
        url = None
        try:
            view_all = card.find_element(By.CSS_SELECTOR, "a.button.button--solid")
            url = view_all.get_attribute("href").rstrip('/')
        except:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(base_link)
            try:
                btn = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.button.button--solid")))
                url = btn.get_attribute("href").rstrip('/')
            except:
                url = f"{base_link}/recent-posts"
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        try:
            name = card.find_element(By.TAG_NAME, "strong").text.split("–")[0].strip()
        except:
            name = card.text.strip()

        blogs.append((name, url))

    with open(outfile_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "url"])
        writer.writerows(blogs)

    print(f"Scraped {len(blogs)} blogs (with proper 'View all posts' URLs) and saved to {outfile_path}")

finally:
    driver.quit()
