from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QScrollArea, QProgressBar
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
import sys
import requests
from googlesearch import search
from duckduckgo_search import DDGS
from urllib.parse import urlparse
import time

def search_images(query, max_results=3):
    """البحث عن الصور باستخدام DuckDuckGo"""
    with DDGS() as ddgs:
        return [r for r in ddgs.images(query, max_results=max_results)]

class LoadingThread(QThread):
    """Thread للتحميل مع محاكاة تقدم التحميل"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    
    def run(self):
        # مراحل التحميل
        steps = [
            ("جاري تحميل المكتبات...", 20),
            ("جاري تهيئة Google Search...", 40),
            ("جاري تهيئة DuckDuckGo...", 60),
            ("جاري تحضير الواجهة...", 80),
            ("جاري الانتهاء...", 100)
        ]
        
        for status_text, progress_value in steps:
            self.status.emit(status_text)
            
            # محاكاة وقت التحميل
            for i in range(progress_value - (progress_value - 20 if progress_value > 20 else 0), progress_value + 1):
                time.sleep(0.02)
                self.progress.emit(i)
            
            time.sleep(0.3)  # توقف قصير بين المراحل
        
        self.finished.emit()

class LoadingWindow(QWidget):
    """نافذة التحميل"""
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('S1lent Search')
        self.setFixedSize(450, 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # تطبيق ستايل جميل
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 #2C3E50, stop:1 #3498DB);
                border-radius: 15px;
                color: white;
            }
            QLabel {
                background: transparent;
                color: white;
            }
            QProgressBar {
                border: 2px solid #34495E;
                border-radius: 10px;
                text-align: center;
                background-color: #2C3E50;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 #E74C3C, stop:1 #F39C12);
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # عنوان البرنامج
        title = QLabel("S1lent Search")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        layout.addWidget(title)
        
        # وصف
        subtitle = QLabel("Smart Search Engine")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #BDC3C7; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # نص حالة التحميل
        self.status_label = QLabel("جاري البدء...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 11))
        layout.addWidget(self.status_label)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # نص الإصدار
        version_label = QLabel("v1.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setFont(QFont("Arial", 9))
        version_label.setStyleSheet("color: #95A5A6; margin-top: 5px;")
        layout.addWidget(version_label)
        
        self.setLayout(layout)
        self.center()
        
        # بدء التحميل
        self.loading_thread = LoadingThread()
        self.loading_thread.progress.connect(self.update_progress)
        self.loading_thread.status.connect(self.update_status)
        self.loading_thread.finished.connect(self.loading_finished)
        self.loading_thread.start()
        
    def center(self):
        """وسط النافذة في الشاشة"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2),
                  int((screen.height() - size.height()) / 2))
    
    def update_progress(self, value):
        """تحديث شريط التقدم"""
        self.progress_bar.setValue(value)
    
    def update_status(self, status):
        """تحديث نص الحالة"""
        self.status_label.setText(status)
    
    def loading_finished(self):
        """عند انتهاء التحميل"""
        self.close()
        # بدء البرنامج الرئيسي
        self.main_window = SmartSearchApp()
        self.main_window.show()

class ImageLoader(QThread):
    """Thread منفصل لتحميل الصور لتجنب تجميد الواجهة"""
    image_loaded = pyqtSignal(QPixmap, str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, image_url):
        super().__init__()
        self.image_url = image_url
        
    def run(self):
        try:
            # إضافة headers لتجنب الحجب
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # تحميل الصورة مع timeout
            response = requests.get(self.image_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # التحقق من نوع المحتوى
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                self.error_occurred.emit(f"Not an image: {content_type}")
                return
            
            # تحميل الصورة
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                self.image_loaded.emit(pixmap, self.image_url)
            else:
                self.error_occurred.emit("Failed to load image data")
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Request error: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")

class SmartSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("S1lent Search")
        self.setGeometry(100, 100, 700, 800)
        
        # تطبيق ستايل جميل للبرنامج الرئيسي
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2C3E50;
            }
            QLineEdit {
                border: 2px solid #3498DB;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #E74C3C;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 #3498DB, stop:1 #2980B9);
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 #2980B9, stop:1 #1ABC9C);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 #1ABC9C, stop:1 #16A085);
            }
            QScrollArea {
                border: none;
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        # إعداد الواجهة الرئيسية
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        main_widget.setLayout(layout)
        
        # مربع البحث
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search anything...")
        self.search_input.setFixedHeight(40)
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input)
        
        # زر البحث
        self.search_button = QPushButton("🔍 Search")
        self.search_button.setFixedHeight(40)
        self.search_button.clicked.connect(self.perform_search)
        layout.addWidget(self.search_button)
        
        # منطقة النتائج مع إمكانية التمرير
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_widget.setLayout(self.results_layout)
        self.scroll_area.setWidget(self.results_widget)
        layout.addWidget(self.scroll_area)
        
        # قائمة لتتبع threads التحميل
        self.image_loaders = []
        
        # التركيز على مربع البحث
        self.search_input.setFocus()
        
    def clear_results(self):
        """مسح النتائج القديمة"""
        # إيقاف جميع threads التحميل النشطة
        for loader in self.image_loaders:
            if loader.isRunning():
                loader.terminate()
                loader.wait()
        self.image_loaders.clear()
        
        # مسح الواجهة
        for i in reversed(range(self.results_layout.count())):
            child = self.results_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
                
    def perform_search(self):
        """تنفيذ البحث"""
        self.clear_results()
        
        query = self.search_input.text().strip()
        if not query:
            error_label = QLabel("⚠️ Please enter something to search.")
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 10px;")
            self.results_layout.addWidget(error_label)
            return
        
        # إضافة مؤشر التحميل
        loading_label = QLabel("🔄 Searching...")
        loading_label.setStyleSheet("color: blue; font-size: 14px; padding: 10px;")
        self.results_layout.addWidget(loading_label)
        
        # تحديث الواجهة
        QApplication.processEvents()
        
        # البحث في Google
        self.search_google(query)
        
        # البحث في DuckDuckGo للصور
        self.search_images_ddg(query)
        
        # إزالة مؤشر التحميل
        loading_label.deleteLater()
        
    def search_google(self, query):
        """البحث في Google"""
        google_title = QLabel("🔗 Web results from Google:")
        google_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #1a73e8; margin: 10px 0;")
        self.results_layout.addWidget(google_title)
        
        try:
            results_found = False
            for i, url in enumerate(search(query, num_results=5)):
                if i >= 5:  # تحديد عدد النتائج
                    break
                    
                # تنسيق الرابط
                parsed_url = urlparse(url)
                display_text = f"{parsed_url.netloc}{parsed_url.path}"
                if len(display_text) > 60:
                    display_text = display_text[:60] + "..."
                
                link_label = QLabel(f"<a href='{url}' style='color: #1a73e8; text-decoration: none;'>{display_text}</a>")
                link_label.setOpenExternalLinks(True)
                link_label.setStyleSheet("padding: 5px; margin: 2px;")
                link_label.setWordWrap(True)
                self.results_layout.addWidget(link_label)
                results_found = True
                
            if not results_found:
                no_results_label = QLabel("No web results found")
                no_results_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
                self.results_layout.addWidget(no_results_label)
                
        except Exception as e:
            error_label = QLabel(f"❌ Google search error: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            self.results_layout.addWidget(error_label)
            
    def search_images_ddg(self, query):
        """البحث عن الصور في DuckDuckGo"""
        images_title = QLabel("🖼️ Image results from DuckDuckGo:")
        images_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #de5833; margin: 15px 0 10px 0;")
        self.results_layout.addWidget(images_title)
        
        try:
            images = search_images(query, max_results=10)
            if not images:
                no_images_label = QLabel("No images found")
                no_images_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
                self.results_layout.addWidget(no_images_label)
                return
                
            for i, img in enumerate(images):
                img_url = img.get("image", "")
                if not img_url:
                    continue
                    
                # إنشاء container للصورة
                img_container = QWidget()
                img_layout = QVBoxLayout()
                img_container.setLayout(img_layout)
                
                # إضافة placeholder للصورة
                img_label = QLabel("🔄 Loading image...")
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setStyleSheet("border: 1px solid #ddd; padding: 20px; margin: 5px;")
                img_label.setMinimumHeight(200)
                img_layout.addWidget(img_label)
                
                # إضافة رابط الصورة
                url_label = QLabel(f"<a href='{img_url}' style='color: #666; font-size: 12px;'>Download</a>")
                url_label.setOpenExternalLinks(True)
                url_label.setAlignment(Qt.AlignCenter)
                img_layout.addWidget(url_label)
                
                self.results_layout.addWidget(img_container)
                
                # بدء تحميل الصورة في thread منفصل
                loader = ImageLoader(img_url)
                loader.image_loaded.connect(lambda pixmap, url, label=img_label: self.on_image_loaded(pixmap, url, label))
                loader.error_occurred.connect(lambda error, label=img_label: self.on_image_error(error, label))
                loader.start()
                
                self.image_loaders.append(loader)
                
        except Exception as e:
            error_label = QLabel(f"❌ Image search error: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            self.results_layout.addWidget(error_label)
            
    def on_image_loaded(self, pixmap, url, label):
        """عند تحميل الصورة بنجاح"""
        # تحديد حجم الصورة
        scaled_pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
        label.setText("")
        label.setAlignment(Qt.AlignCenter)
        
    def on_image_error(self, error, label):
        """عند فشل تحميل الصورة"""
        label.setText(f"❌ Failed to load image\n{error}")
        label.setStyleSheet("color: red; border: 1px solid #ff6b6b; padding: 20px; margin: 5px;")
        
    def closeEvent(self, event):
        """عند إغلاق التطبيق"""
        # إيقاف جميع threads النشطة
        for loader in self.image_loaders:
            if loader.isRunning():
                loader.terminate()
                loader.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # بدء شاشة التحميل
    loading_window = LoadingWindow()
    loading_window.show()
    
    sys.exit(app.exec_())