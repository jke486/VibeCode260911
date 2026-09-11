import sqlite3
import sys
from pathlib import Path

from openpyxl import Workbook
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

DB_PATH = Path("products.db")


class ProductManagerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_product_id = None
        self.init_ui()
        self.create_table()
        self.load_products()

    def init_ui(self):
        self.setWindowTitle("Products 관리 프로그램")
        self.resize(900, 650)
        self.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a, stop:0.5 #1e293b, stop:1 #111827);
                color: #e2e8f0;
                font-family: 'Malgun Gothic';
            }
            QLabel {
                color: #f8fafc;
                font-size: 13px;
            }
            QLineEdit {
                background-color: rgba(30, 41, 59, 0.9);
                border: 1px solid #475569;
                border-radius: 10px;
                padding: 8px 10px;
                color: #f8fafc;
                selection-background-color: #8b5cf6;
            }
            QLineEdit:focus {
                border: 2px solid #a78bfa;
            }
            QPushButton {
                border: none;
                border-radius: 10px;
                padding: 8px 14px;
                color: white;
                font-weight: bold;
                min-height: 32px;
            }
            QPushButton:hover {
                filter: brightness(1.08);
            }
            QPushButton:pressed {
                filter: brightness(0.95);
            }
            #addButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #34d399);
            }
            #updateButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #60a5fa);
            }
            #deleteButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef4444, stop:1 #f87171);
            }
            #searchButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f59e0b, stop:1 #fbbf24);
            }
            #exportButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #a78bfa);
            }
            #clearButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #64748b, stop:1 #94a3b8);
            }
            QTableWidget {
                background-color: rgba(15, 23, 42, 0.9);
                border: 1px solid #475569;
                border-radius: 12px;
                gridline-color: #334155;
                selection-background-color: #7c3aed;
                selection-color: #f8fafc;
            }
            QHeaderView::section {
                background-color: #1f2937;
                color: #f8fafc;
                border: 1px solid #374151;
                padding: 8px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #334155;
            }
            QTableWidget::item:selected {
                background-color: rgba(124, 58, 237, 0.8);
                color: #ffffff;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(12)

        self.product_name_input = QLineEdit()
        self.product_price_input = QLineEdit()
        self.search_input = QLineEdit()

        self.product_name_input.setPlaceholderText("상품명을 입력하세요")
        self.product_price_input.setPlaceholderText("상품가격을 입력하세요")
        self.search_input.setPlaceholderText("상품명을 입력해 검색하세요")

        form_layout.addRow("상품명", self.product_name_input)
        form_layout.addRow("상품가격", self.product_price_input)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("추가")
        self.update_button = QPushButton("수정")
        self.delete_button = QPushButton("삭제")
        self.search_button = QPushButton("검색")
        self.export_button = QPushButton("엑셀 저장")
        self.clear_button = QPushButton("초기화")

        self.add_button.setObjectName("addButton")
        self.update_button.setObjectName("updateButton")
        self.delete_button.setObjectName("deleteButton")
        self.search_button.setObjectName("searchButton")
        self.export_button.setObjectName("exportButton")
        self.clear_button.setObjectName("clearButton")

        self.add_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.update_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.delete_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.search_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.export_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.clear_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))

        for button in (
            self.add_button,
            self.update_button,
            self.delete_button,
            self.search_button,
            self.export_button,
            self.clear_button,
        ):
            button.setIconSize(QSize(18, 18))

        self.add_button.clicked.connect(self.add_product)
        self.update_button.clicked.connect(self.update_product)
        self.delete_button.clicked.connect(self.delete_product)
        self.search_button.clicked.connect(self.search_products)
        self.export_button.clicked.connect(self.export_to_excel)
        self.clear_button.clicked.connect(self.clear_inputs)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.clear_button)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("검색:"))
        search_layout.addWidget(self.search_input)

        self.status_label = QLabel("상품을 추가해 주세요.")
        self.status_label.setStyleSheet("color: #facc15; font-weight: bold;")

        self.table_widget = QTableWidget(0, 3)
        self.table_widget.setHorizontalHeaderLabels(["productID", "productName", "productPrice"])
        self.table_widget.setEditTriggers(self.table_widget.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(self.table_widget.SelectionBehavior.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.cellClicked.connect(self.on_table_clicked)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.table_widget)

    def connect_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def create_table(self):
        conn = self.connect_db()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS Products (
                        productID INTEGER PRIMARY KEY AUTOINCREMENT,
                        productName TEXT NOT NULL,
                        productPrice INTEGER NOT NULL CHECK(productPrice >= 0)
                    )
                    """
                )
        finally:
            conn.close()

    def fetch_products(self, keyword=""):
        query = "SELECT productID, productName, productPrice FROM Products"
        params = []

        if keyword:
            query += " WHERE productName LIKE ?"
            params.append(f"%{keyword}%")

        query += " ORDER BY productID"

        conn = self.connect_db()
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def load_products(self, keyword=""):
        rows = self.fetch_products(keyword)

        self.table_widget.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.table_widget.setItem(row_index, 0, QTableWidgetItem(str(row["productID"])))
            self.table_widget.setItem(row_index, 1, QTableWidgetItem(row["productName"]))
            self.table_widget.setItem(row_index, 2, QTableWidgetItem(str(row["productPrice"])))

        self.table_widget.resizeColumnsToContents()
        self.status_label.setText(f"총 {len(rows)}개의 상품이 있습니다.")

    def clear_inputs(self):
        self.product_name_input.clear()
        self.product_price_input.clear()
        self.search_input.clear()
        self.selected_product_id = None
        self.table_widget.clearSelection()
        self.status_label.setText("입력을 초기화했습니다.")

    def on_table_clicked(self, row, column):
        item = self.table_widget.item(row, 0)
        if item is None:
            return

        self.selected_product_id = int(item.text())
        self.product_name_input.setText(self.table_widget.item(row, 1).text())
        self.product_price_input.setText(self.table_widget.item(row, 2).text())
        self.status_label.setText(f"선택된 상품 ID: {self.selected_product_id}")

    def add_product(self):
        product_name = self.product_name_input.text().strip()
        product_price_text = self.product_price_input.text().strip()

        if not product_name or not product_price_text:
            QMessageBox.warning(self, "입력 오류", "상품명과 상품가격을 모두 입력하세요.")
            return

        try:
            product_price = int(product_price_text)
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "상품가격은 숫자로 입력하세요.")
            return

        if product_price < 0:
            QMessageBox.warning(self, "입력 오류", "상품가격은 0 이상이어야 합니다.")
            return

        conn = self.connect_db()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO Products (productName, productPrice) VALUES (?, ?)",
                    (product_name, product_price),
                )
        except sqlite3.Error as e:
            QMessageBox.critical(self, "DB 오류", f"상품 추가 중 오류가 발생했습니다.\n{e}")
            return
        finally:
            conn.close()

        self.clear_inputs()
        self.load_products()
        self.status_label.setText("상품이 추가되었습니다.")

    def update_product(self):
        if self.selected_product_id is None:
            QMessageBox.warning(self, "선택 오류", "수정할 상품을 테이블에서 선택하세요.")
            return

        product_name = self.product_name_input.text().strip()
        product_price_text = self.product_price_input.text().strip()

        if not product_name or not product_price_text:
            QMessageBox.warning(self, "입력 오류", "상품명과 상품가격을 모두 입력하세요.")
            return

        try:
            product_price = int(product_price_text)
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "상품가격은 숫자로 입력하세요.")
            return

        if product_price < 0:
            QMessageBox.warning(self, "입력 오류", "상품가격은 0 이상이어야 합니다.")
            return

        conn = self.connect_db()
        try:
            with conn:
                cursor = conn.execute(
                    "UPDATE Products SET productName = ?, productPrice = ? WHERE productID = ?",
                    (product_name, product_price, self.selected_product_id),
                )
                if cursor.rowcount == 0:
                    QMessageBox.warning(self, "수정 오류", "수정할 상품이 존재하지 않습니다.")
                    return
        except sqlite3.Error as e:
            QMessageBox.critical(self, "DB 오류", f"상품 수정 중 오류가 발생했습니다.\n{e}")
            return
        finally:
            conn.close()

        self.clear_inputs()
        self.load_products()
        self.status_label.setText("상품이 수정되었습니다.")

    def delete_product(self):
        if self.selected_product_id is None:
            QMessageBox.warning(self, "선택 오류", "삭제할 상품을 테이블에서 선택하세요.")
            return

        reply = QMessageBox.question(
            self,
            "삭제 확인",
            f"productID {self.selected_product_id}번 상품을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        conn = self.connect_db()
        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM Products WHERE productID = ?",
                    (self.selected_product_id,),
                )
                if cursor.rowcount == 0:
                    QMessageBox.warning(self, "삭제 오류", "삭제할 상품이 존재하지 않습니다.")
                    return
        except sqlite3.Error as e:
            QMessageBox.critical(self, "DB 오류", f"상품 삭제 중 오류가 발생했습니다.\n{e}")
            return
        finally:
            conn.close()

        self.clear_inputs()
        self.load_products()
        self.status_label.setText("상품이 삭제되었습니다.")

    def search_products(self):
        keyword = self.search_input.text().strip()
        self.load_products(keyword)
        self.status_label.setText(f"'{keyword}'로 검색한 결과입니다.")

    def export_to_excel(self):
        rows = self.fetch_products(self.search_input.text().strip())

        if not rows:
            QMessageBox.information(self, "엑셀 저장", "저장할 데이터가 없습니다.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "엑셀 파일 저장",
            "products.xlsx",
            "Excel Files (*.xlsx)",
        )

        if not save_path:
            return

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Products"
        sheet.append(["productID", "productName", "productPrice"])

        for row in rows:
            sheet.append([row["productID"], row["productName"], row["productPrice"]])

        workbook.save(save_path)
        QMessageBox.information(self, "엑셀 저장", f"엑셀 파일이 저장되었습니다.\n{save_path}")


def main():
    app = QApplication(sys.argv)
    window = ProductManagerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
