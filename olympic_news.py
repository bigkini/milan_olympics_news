import requests
import os
from bs4 import BeautifulSoup

# 환경 변수 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
HISTORY_FILE = "last_titles.txt"

def get_newsnow(url):
    """NewsNow 에디션별 상위 10개 추출"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        articles = soup.select('.hl__inner')[:10]
        return [(a.select_one('.hll').text.strip(), a.select_one('.hll')['href']) 
                for a in articles if a.select_one('.hll')]
    except: return []

def get_chosun_api():
    """조선일보 API 최신 10개 추출"""
    API_URL = "https://www.chosun.com/pf/api/v3/content/fetch/story-feed?query=%7B%22excludeContentTypes%22%3A%22gallery%2C%20video%22%2C%22excludeSections%22%3A%22%2Fsports%2Fsports_photo%22%2C%22includeContentTypes%22%3A%22story%22%2C%22includeSections%22%3A%22%2Fsports%2Fsports_special%22%2C%22offset%22%3A0%2C%22size%22%3A10%7D&_website=chosun"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(API_URL, headers=headers, timeout=10)
        data = res.json()
        articles = data.get('content_elements', [])
        news = []
        for a in articles:
            title = a.get('headlines', {}).get('basic', '').strip()
            path = a.get('canonical_url') or a.get('website_url', '')
            url = "https://www.chosun.com" + path if path and not path.startswith('http') else path
            if title and url: news.append((title, url))
        return news
    except: return []

def main():
    # 1. 외신 소스 수집 (미-영-캐-호)
    newsnow_urls = [
        "https://www.newsnow.com/us/Sports/Olympics?type=ts",
        "https://www.newsnow.co.uk/h/Sport/Olympics?type=ts",
        "https://www.newsnow.com/ca/Sports/Olympics?type=ts",
        "https://www.newsnow.com/au/Sport/Olympics?type=ts"
    ]
    
    foreign_raw = []
    for url in newsnow_urls:
        foreign_raw.extend(get_newsnow(url))

    # 2. 외신들 사이에서만 제목 중복 제거 (국가 간 겹치는 기사 방지)
    unique_foreign = {}
    for title, url in foreign_raw:
        if title not in unique_foreign:
            unique_foreign[title] = url

    # 3. 한국 기사 수집 (중복 검사 대상에서 제외, 리스트로 별도 관리)
    domestic_news = get_chosun_api()

    # 4. 기존 기록(파일) 로드
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            last_titles = set(line.strip() for line in f.read().splitlines())
    else:
        last_titles = set()

    # 5. 최종 알림 리스트 생성
    final_alerts = []

    # 5-1. 한국 기사 먼저 추가 (새로운 것이라면 무조건 포함)
    for title, url in domestic_news:
        if title not in last_titles:
            final_alerts.append(f"<b>[KR]</b> {title}\n{url}")
            last_titles.add(title)

    # 5-2. 외신 기사 추가 (새로운 것이라면 포함)
    for title, url in unique_foreign.items():
        if title not in last_titles:
            final_alerts.append(f"<b>[Global]</b> {title}\n{url}")
            last_titles.add(title)

    # 6. 텔레그램 발송
    if final_alerts:
        # 가독성을 위해 상위 25개 정도로 조절
        header = "<b>[2026 밀라노-코르티나 올림픽 업데이트]</b>\n\n"
        msg = header + "\n\n".join(final_alerts[:25])
        
        t_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(t_url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        
        # 7. 히스토리 업데이트 (최신 500개 유지)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(list(last_titles)[-500:]))
    else:
        print("새로운 업데이트가 없습니다.")

if __name__ == "__main__":
    main()
