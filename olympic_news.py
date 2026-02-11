import requests
from bs4 import BeautifulSoup
import os

# 설정
URL = "https://www.newsnow.com/us/Sports/Olympics?type=ts"
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
HISTORY_FILE = "last_titles.txt"

def get_news():
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(URL, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 상위 10개 기사 추출 (NewsNow 구조 기준)
    articles = soup.select('.hl__inner')[:10]
    news_list = []
    for art in articles:
        title = art.select_one('.hll').text.strip()
        link = art.select_one('.hll')['href']
        news_list.append((title, link))
    return news_list

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def main():
    current_news = get_news()
    
    # 이전 기록 불러오기
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            last_titles = f.read().splitlines()
    else:
        last_titles = []

    new_articles = [n for n in current_news if n[0] not in last_titles]

    if new_articles:
        msg = "<b>[새로운 올림픽 뉴스]</b>\n\n"
        for title, link in new_articles:
            msg += f"• {title}\n{link}\n\n"
        
        send_telegram(msg)
        
        # 새로운 타이틀 저장 (최신 50개 정도만 유지)
        all_titles = [n[0] for n in current_news] + last_titles
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(list(set(all_titles))[:50]))

if __name__ == "__main__":
    main()
