import csv
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

MAIN_URL = "https://finance.naver.com/sise/sise_index.naver?code=KPI200"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}
FIELDNAMES = ["종목별", "현재가", "전일비", "등락률", "거래량", "거래대금(백만)", "시가총액(억)"]


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    if response.encoding is None or response.encoding.lower() in {"utf-8", "utf8"}:
        response.encoding = "euc-kr"

    return response.text


def clean_text(text: str) -> str:
    if text is None:
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_entry_url(main_html: str) -> str:
    soup = BeautifulSoup(main_html, "html.parser")

    iframe = soup.find("iframe", src=re.compile(r"/sise/entryJongmok\.naver"))
    if iframe is None:
        raise RuntimeError("편입종목상위 iframe 주소를 찾지 못했습니다.")

    return urljoin(MAIN_URL, iframe["src"])


def extract_kospi200_members(html: str):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="type_1")

    if table is None:
        raise RuntimeError("편입종목상위 테이블을 찾지 못했습니다.")

    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) != 7:
            continue

        name_cell = cells[0]
        stock_name = clean_text(name_cell.get_text(" ", strip=True))
        if not stock_name:
            continue

        values = [clean_text(td.get_text(" ", strip=True)) for td in cells[1:]]
        if len(values) != 6:
            continue

        row = {
            "종목별": stock_name,
            "현재가": values[0],
            "전일비": values[1],
            "등락률": values[2],
            "거래량": values[3],
            "거래대금(백만)": values[4],
            "시가총액(억)": values[5],
        }
        rows.append(row)

    return rows


def collect_kospi200_members(base_url: str, limit: int = 200):
    all_rows = []
    page = 1

    while len(all_rows) < limit:
        page_url = f"{base_url}&page={page}"
        page_html = fetch_html(page_url)
        page_rows = extract_kospi200_members(page_html)

        if not page_rows:
            break

        all_rows.extend(page_rows)

        if len(page_rows) < 10:
            break

        page += 1

    return all_rows[:limit]


def save_csv(rows, file_name="kospi200_members.csv"):
    output_path = Path(file_name)

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})

    print(f"CSV 저장 완료: {output_path.resolve()}")


def save_excel(rows, file_name="klspi200.xlsx"):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "KPI200"

    sheet.append(FIELDNAMES)
    for row in rows:
        sheet.append([row.get(field, "") for field in FIELDNAMES])

    workbook.save(file_name)
    print(f"Excel 저장 완료: {Path(file_name).resolve()}")


class KPI200Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KPI200 편입종목상위")
        self.resize(1200, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("데이터를 불러오려면 아래 버튼을 눌러주세요.")
        self.status_label.setStyleSheet("font-size: 12px; margin-bottom: 5px;")

        self.load_button = QPushButton("데이터 불러오기")
        self.load_button.clicked.connect(self.load_data)

        self.save_excel_button = QPushButton("엑셀 저장")
        self.save_excel_button.clicked.connect(self.save_excel_data)

        self.table = QTableWidget()
        self.table.setColumnCount(len(FIELDNAMES))
        self.table.setHorizontalHeaderLabels(FIELDNAMES)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.status_label)
        layout.addWidget(self.load_button)
        layout.addWidget(self.save_excel_button)
        layout.addWidget(self.table)

    def load_data(self):
        try:
            self.status_label.setText("데이터를 수집 중입니다...")
            self.load_button.setEnabled(False)

            main_html = fetch_html(MAIN_URL)
            entry_url = get_entry_url(main_html)
            rows = collect_kospi200_members(entry_url)

            self.rows = rows
            self.populate_table(rows)
            save_csv(rows)
            self.status_label.setText(f"총 {len(rows)}개의 편입종목상위 데이터가 로드되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 수집 중 오류가 발생했습니다.\n{e}")
            self.status_label.setText("데이터 로드에 실패했습니다.")
        finally:
            self.load_button.setEnabled(True)

    def save_excel_data(self):
        try:
            if not hasattr(self, "rows") or not self.rows:
                QMessageBox.warning(self, "알림", "먼저 데이터를 불러와 주세요.")
                return

            save_excel(self.rows, "klspi200.xlsx")
            self.status_label.setText("엑셀 파일이 저장되었습니다: klspi200.xlsx")
            QMessageBox.information(self, "완료", "엑셀 파일이 저장되었습니다.\nklspi200.xlsx")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 저장 중 오류가 발생했습니다.\n{e}")

    def populate_table(self, rows):
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(FIELDNAMES))
        self.table.setHorizontalHeaderLabels(FIELDNAMES)

        for row_index, row in enumerate(rows):
            for col_index, field_name in enumerate(FIELDNAMES):
                value = row.get(field_name, "")
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, col_index, item)

        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


def main():
    app = QApplication(sys.argv)
    window = KPI200Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
