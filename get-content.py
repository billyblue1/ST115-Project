import os
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def scrape_article(driver, url, wait):
    """
    Given an article URL, navigate and extract author, reading time, shares, comments, and content.
    """
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.main-container')))

    try:
        author = driver.find_element(By.CSS_SELECTOR, '.single-post__main-sidebar h3').text.strip()
    except Exception:
        author = ''

    try:
        rt_elem = driver.find_element(By.CSS_SELECTOR, 'p.reading-time')
        reading_time = rt_elem.text.replace('Estimated reading time: ', '').strip()
    except Exception:
        reading_time = ''

    try:
        comments = driver.find_element(By.CSS_SELECTOR, '.post-main-image__meta a[href="#comments"]').text.split()[0]
    except Exception:
        comments = ''

    try:
        meta_text = driver.find_element(By.CSS_SELECTOR, '.post-main-image__meta').text
        parts = meta_text.split('|')
        shares = parts[-1].strip().split()[0] if len(parts) > 1 else ''
    except Exception:
        shares = ''

    paragraphs = []
    for p in driver.find_elements(By.CSS_SELECTOR, '.post-content p'):
        text = p.text.strip()
        if text:
            paragraphs.append(text)
    content = "\n\n".join(paragraphs)

    return author, reading_time, shares, comments, content


def main():
    infile = os.path.join('data', 'articles.csv')
    
    df = pd.read_csv(infile, dtype={
        'blog_name': str, 
        'blog_url': str, 
        'article_title': str, 
        'article_url': str,
        'article_date': str,
        'author': str,
        'reading_time': str,
        'shares': str,
        'comments': str,
        'content': str
    })

    for col in ['author', 'reading_time', 'shares', 'comments', 'content']:
        if col not in df.columns:
            df[col] = ''
    
    already_scraped = df['content'].notna() & (df['content'] != '')
    to_scrape = ~already_scraped
    print(f"Found {already_scraped.sum()} articles already scraped, {to_scrape.sum()} articles remaining.")

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    wait = WebDriverWait(driver, 10)

    try:
        start_time = time.time()
        articles_scraped = 0
        articles_failed = 0
        
        for idx, row in df.iterrows():
            if already_scraped.iloc[idx]:
                continue
                
            url = row.get('article_url')
            if not isinstance(url, str) or not url.strip():
                continue

            try:
                author, rt, shares, comments, content = scrape_article(driver, url, wait)
                df.at[idx, 'author'] = author
                df.at[idx, 'reading_time'] = rt
                df.at[idx, 'shares'] = shares
                df.at[idx, 'comments'] = comments
                df.at[idx, 'content'] = content
                articles_scraped += 1
                
                if articles_scraped % 10 == 0:
                    df.to_csv(infile, index=False)
                    elapsed = time.time() - start_time
                    rate = articles_scraped / elapsed if elapsed > 0 else 0
                    print(f"Progress: {articles_scraped} scraped, {articles_failed} failed, {rate:.2f} articles/sec")
                
                print(f"Scraped: {url}")
            except Exception as e:
                articles_failed += 1
                print(f"Error scraping {url}: {e}")

    finally:
        driver.quit()

    df.to_csv(infile, index=False)
    
    print(f"Scraping complete. Total articles scraped: {articles_scraped}, failed: {articles_failed}")


if __name__ == '__main__':
    main()
