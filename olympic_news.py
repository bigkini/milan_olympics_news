import requests
import os
import json

# 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
HISTORY_FILE = "last_titles.txt"

def get_newsnow():
    """NewsNow 외신 상위 10개 추출"""
    URL = "https://www.newsnow.com/us/Sports/Olympics?type=ts"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(URL, headers=headers)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('.hl__inner')[:10]
        return [(a.select_one('.hll').text.strip(), a.select_one('.hll')['href']) for a in articles if a.select_one('.hll')]
    except: return []

def get_chosun_api():
    """조선일보 API 내신 상위 10개 추출 (kini 님이 찾으신 API 활용)"""
    # offset=0으로 설정하여 항상 최신 기사를 가져오도록 함
    API_URL = "https://www.chosun.com/pf/api/v3/content/fetch/story-feed?query=%7B%22excludeContentTypes%22%3A%22gallery%2C%20video%22%2C%22excludeSections%22%3A%22%2Fsports%2Fsports_photo%22%2C%22includeContentTypes%22%3A%22story%22%2C%22includeSections%22%3A%22%2Fsports%2Fsports_special%22%2C%22offset%22%3A0%2C%22size%22%3A10%7D&_website=chosun"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(API_URL, headers=headers)
        data = res.json()
        articles = data.get('content_elements', [])
        return [(a['headlines']['basic'], "https://www.chosun.com" + a['website_url']) for a in articles]
    except: return []

def send_telegram(message):
    if not message: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False}
    requests.post(url, json=payload)

def main():
    # 데이터 수집
    all_news = get_newsnow() + get_chosun_api()
    
    # 중복 체크
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            last_titles = set(f.read().splitlines())
    else:
        last_titles = set()

    new_articles = [n for n in all_news if n[0] not in last_titles]

    if new_articles:
        msg = "<b>[올림픽 소식 업데이트]</b>\n\n"
        for title, link in new_articles:
            msg += f"• {title}\n{link}\n\n"
        
        send_telegram(msg)
        
        # 새로운 타이틀 저장 (최신 100개 유지)
        updated_titles = [n[0] for n in all_news] + list(last_titles)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(updated_titles[:100]))

if __name__ == "__main__":
    main()
