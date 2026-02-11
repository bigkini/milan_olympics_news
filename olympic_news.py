import requests
import os
import json

# 환경 변수 설정 (GitHub Secrets에 저장된 값 호출)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
HISTORY_FILE = "last_titles.txt"

def get_newsnow():
    """NewsNow 외신 상위 10개 기사 추출 (HTML 파싱)"""
    URL = "https://www.newsnow.com/us/Sports/Olympics?type=ts"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        from bs4 import BeautifulSoup
        res = requests.get(URL, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('.hl__inner')[:10]
        news = []
        for a in articles:
            link_tag = a.select_one('.hll')
            if link_tag:
                news.append((link_tag.text.strip(), link_tag['href']))
        return news
    except Exception as e:
        print(f"NewsNow 수집 에러: {e}")
        return []

def get_chosun_api():
    """조선일보 API 내신 상위 10개 기사 추출 (kini 님이 찾으신 API 활용)"""
    # offset=0으로 설정하여 가장 최신 뉴스 10개를 가져옵니다.
    API_URL = "https://www.chosun.com/pf/api/v3/content/fetch/story-feed?query=%7B%22excludeContentTypes%22%3A%22gallery%2C%20video%22%2C%22excludeSections%22%3A%22%2Fsports%2Fsports_photo%22%2C%22includeContentTypes%22%3A%22story%22%2C%22includeSections%22%3A%22%2Fsports%2Fsports_special%22%2C%22offset%22%3A0%2C%22size%22%3A10%7D&_website=chosun"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(API_URL, headers=headers, timeout=10)
        data = res.json()
        articles = data.get('content_elements', [])
        news = []
        for a in articles:
            title = a.get('headlines', {}).get('basic', '제목 없음')
            url = a.get('website_url', '')
            if not url.startswith('http'):
                url = "https://www.chosun.com" + url
            news.append((title, url))
        return news
    except Exception as e:
        print(f"조선일보 API 에러: {e}")
        return []

def send_telegram(message):
    """텔레그램 메시지 전송"""
    if not message: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"텔레그램 전송 에러: {e}")

def main():
    # 1. 뉴스 데이터 수집
    current_news = get_newsnow() + get_chosun_api()
    
    # 2. 기존 기록(History) 로드
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            last_titles = set(f.read().splitlines())
    else:
        last_titles = set()

    # 3. 새로운 기사만 필터링
    new_articles = [n for n in current_news if n[0] not in last_titles]

    # 4. 새 소식이 있으면 발송
    if new_articles:
        msg = "<b>[올림픽 소식 업데이트]</b>\n\n"
        for title, link in new_articles:
            msg += f"• {title}\n{link}\n\n"
        
        send_telegram(msg)
        
        # 5. 히스토리 파일 업데이트 (최신 100개 제목 유지)
        updated_titles = [n[0] for n in current_news] + list(last_titles)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(updated_titles[:100]))
    else:
        print("새로운 소식이 없습니다.")

if __name__ == "__main__":
    main()
