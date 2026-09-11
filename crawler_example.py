import re
import sys
import time
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

EXCEL_FILE = "naverResult.xlsx"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_html(url):
    last_error = None

    for attempt in range(1, 4):
        try:
            response = requests.get(url, headers=headers, timeout=20)

            if response.status_code in (403, 429):
                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()
            return response.text

        except requests.RequestException as e:
            last_error = e
            if attempt < 3:
                time.sleep(1)

    raise RuntimeError(f"페이지 불러오기 실패: {url} ({last_error})")


def is_valid_article_link(href):
    href = href.strip()
    if not href:
        return False

    if href.startswith("//"):
        href = "https:" + href

    if "channelPromotion" in href or "/main/static/" in href:
        return False

    return "news.naver.com" in href or "n.news.naver.com" in href


def get_news_items(search_url):
    html = fetch_html(search_url)
    soup = BeautifulSoup(html, "html.parser")

    news_items = []
    seen_links = set()

    selectors = ["a.news_tit", "a._sp_each_title", "a[href*='news.naver.com']"]

    for selector in selectors:
        for a in soup.select(selector):
            href = a.get("href", "").strip()
            title = a.get_text(" ", strip=True)

            if not href or not title:
                continue

            if not is_valid_article_link(href):
                continue

            if href.startswith("//"):
                href = "https:" + href

            if href not in seen_links:
                seen_links.add(href)
                news_items.append({"title": title, "link": href})

    return news_items


def clean_text(text):
    text = text.replace("\xa0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def get_article_text(article_url):
    html = fetch_html(article_url)
    soup = BeautifulSoup(html, "html.parser")

    selectors = [
        "#dic_area",
        "#articleBodyContents",
        ".newsct_article",
        ".article_body",
        "article",
        "div#contents",
    ]

    for selector in selectors:
        article = soup.select_one(selector)
        if article:
            text = article.get_text("\n", strip=True)
            return clean_text(text)

    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)

    if paragraphs:
        return clean_text("\n".join(paragraphs))

    return clean_text(soup.get_text("\n", strip=True))


def save_to_excel(rows, filename=EXCEL_FILE):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "naver_news"

    sheet.append(["번호", "제목", "링크", "본문"])

    for row in rows:
        sheet.append([row["번호"], row["제목"], row["링크"], row["본문"]])

    for column_cells in sheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 120)

    workbook.save(filename)


class CrawlerWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            query = self.query.strip()
            if not query:
                raise ValueError("검색어를 입력하세요.")

            search_url = f"https://search.naver.com/search.naver?where=news&sm=tab_jum&query={quote(query)}"

            self.progress.emit(f"검색어: {query}")
            self.progress.emit(f"검색 URL: {search_url}")
            self.progress.emit("검색 결과를 가져오는 중...")

            news_items = get_news_items(search_url)
            self.progress.emit(f"총 {len(news_items)}개의 기사 링크를 찾았습니다.")

            results = []
            for idx, item in enumerate(news_items, 1):
                title = item["title"]
                link = item["link"]
                self.progress.emit(f"[{idx}] {title}")

                try:
                    text = get_article_text(link)
                    results.append(
                        {
                            "번호": idx,
                            "제목": title,
                            "링크": link,
                            "본문": text,
                        }
                    )
                    self.progress.emit(f"본문 추출 완료: {text[:80]}...")
                except Exception as e:
                    self.progress.emit(f"본문 추출 실패: {e}")
                    results.append(
                        {
                            "번호": idx,
                            "제목": title,
                            "링크": link,
                            "본문": "",
                        }
                    )

                self.progress.emit("-" * 60)

            save_to_excel(results, EXCEL_FILE)
            self.progress.emit(f"엑셀 저장 완료: {EXCEL_FILE}")
            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))


class NaverNewsCrawlerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 뉴스 크롤링 GUI")
        self.resize(1100, 700)
        self.results = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.label = QLabel("검색어를 입력하세요:")
        self.layout.addWidget(self.label)

        self.query_input = QLineEdit("반도체")
        self.layout.addWidget(self.query_input)

        self.run_button = QPushButton("검색 실행")
        self.run_button.clicked.connect(self.start_crawl)
        self.layout.addWidget(self.run_button)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("크롤링 결과가 여기에 표시됩니다.")
        self.layout.addWidget(self.output)

    def append_log(self, message):
        self.output.append(message)

    def start_crawl(self):
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "입력 오류", "검색어를 입력하세요.")
            return

        self.results = []
        self.output.clear()
        self.run_button.setEnabled(False)
        self.append_log("크롤링을 시작합니다...")

        self.thread = QThread()
        self.worker = CrawlerWorker(query)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.append_log)
        self.worker.finished.connect(self.handle_finished)
        self.worker.error.connect(self.handle_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def handle_finished(self, results):
        self.results = results
        self.run_button.setEnabled(True)
        self.append_log(f"총 {len(results)}건의 결과를 수집했습니다.")

    def handle_error(self, message):
        self.run_button.setEnabled(True)
        self.append_log(f"오류: {message}")
        QMessageBox.critical(self, "오류", message)


def main():
    app = QApplication(sys.argv)
    window = NaverNewsCrawlerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
