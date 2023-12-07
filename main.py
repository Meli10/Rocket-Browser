import sys
import os
from PyQt6.QtCore import QSize, QRectF, QUrl, Qt, QEvent
from PyQt6.QtGui import QIcon, QPainter, QPainterPath, QColor, QPen, QPixmap, QLinearGradient, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QTabBar, QLabel, QLineEdit, QToolBar, QStatusBar, QWidget, QSizePolicy, QPushButton, QMenu, QListWidget, QListWidgetItem, QDialog, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

# Get absolute path to resource, works for development and for PyInstaller
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class HistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browsing History")
        self.layout = QVBoxLayout(self)

        # List widget for history
        self.history_list = QListWidget()
        for title, url in history:
            item = QListWidgetItem(f"{title}: {url}")
            item.setData(Qt.ItemDataRole.UserRole, url)
            self.history_list.addItem(item)
        self.layout.addWidget(self.history_list)

        # Clear history button
        self.clear_button = QPushButton("Clear History")
        self.clear_button.clicked.connect(self.accept)
        self.layout.addWidget(self.clear_button)

        # Connect item clicked signal
        self.history_list.itemClicked.connect(self.on_item_clicked)

        # Store the parent (main window) reference for later use
        self.parent = parent

    def on_item_clicked(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        self.parent.add_new_tab(QUrl(url))

    def clear_history(self):
        return self.exec() == QDialog.DialogCode.Accepted

class TruncatedTabBar(QTabBar):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for index in range(self.count()):
            tab_rect = QRectF(self.tabRect(index))
            tab_text = self.tabText(index)

            path = QPainterPath()
            path.addRoundedRect(tab_rect, 4, 4)
            painter.fillPath(path, QColor('white' if self.currentIndex() == index else '#f0f0f0'))

            if self.currentIndex() == index:
                shadow_gradient = QLinearGradient(tab_rect.topLeft(), tab_rect.bottomLeft())
                shadow_gradient.setColorAt(0.0, QColor(0, 0, 0, 30))
                shadow_gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(shadow_gradient)
    
                shadow_rect = QRectF(tab_rect.left(), tab_rect.bottom(), tab_rect.width(), 10)
                painter.drawRect(shadow_rect)

            painter.setPen(QPen(QColor('black')))
            alignment = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            painter.drawText(tab_rect, alignment, tab_text)


        # Call the base class to handle drawing the rest of the tab bar
        super().paintEvent(event)

# Main window
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.browserFullScreen = False
        self.previousWindowState = self.windowState()
        self.browserHistory = []
        
        # Adding resource paths. This is needed to locate images correctly for .EXE
        back_btn_icon_path = resource_path('pics/backward.png')
        next_btn_icon_path = resource_path('pics/Forward.png')
        home_btn_icon_path = resource_path('pics/home.png')
        reload_btn_icon_path = resource_path('pics/Refresh.png')
        self.no_ssl_icon_path = resource_path('pics/no_ssl_lock.png')
        self.ssl_icon_path = resource_path('pics/ssl_lock.png')
        title_bar_icon_path = resource_path('pics/rocket.png')
        settings_btn_icon_path = resource_path('pics/Settings.png')

        self.tabs = QTabWidget()
        self.tabs.setTabBar(TruncatedTabBar())
        self.setWindowIcon(QIcon(title_bar_icon_path))
        self.setIconSize(QSize(80, 80))
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        self.showMaximized()
        self.setWindowTitle("Rocket")
        self.setStyleSheet(".QIcon {font-size: 11px;}")
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        
        # Creating first tab
        self.add_new_tab(QUrl('http://www.google.com'), 'Homepage')
        self.show()

		# adding action when double clicked
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)

		# adding action when tab close is requested
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tabs)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        # adding tool bar to the main window
        self.navtb = QToolBar('Navigation')
        self.addToolBar(self.navtb)

        # Adding back button functionality
        back_btn = QAction('Back', self)
        back_btn.setIcon(QIcon(back_btn_icon_path))
        back_btn.setStatusTip('Back to previous page')
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        self.navtb.addAction(back_btn)

		# Adding next button functionality
        next_btn = QAction('Forward', self)
        
        next_btn.setIcon(QIcon(next_btn_icon_path))
        next_btn.setStatusTip('Forward to next page')
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        self.navtb.addAction(next_btn)

		# Adding reload button functionality
        reload_btn = QAction('Refresh', self)
        reload_btn.setIcon(QIcon(reload_btn_icon_path))
        reload_btn.setStatusTip('Refresh page')
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        self.navtb.addAction(reload_btn)

        # Adding home button functionality
        home_btn = QAction('Home', self)
        home_btn.setStatusTip('Go home')
        home_btn.setIcon(QIcon(home_btn_icon_path))
        home_btn.triggered.connect(self.navigate_home)
        self.navtb.addAction(home_btn)
        
        # Adding a separator
        self.navtb.addSeparator()
        
        self.httpsicon = QLabel()
        self.httpsicon.setPixmap(QPixmap(os.path.join(self.no_ssl_icon_path)))
        self.navtb.addWidget(self.httpsicon)

		# Creating a line edit widget for URL
        self.urlbar = QLineEdit()
        urlbar_style = '''
  			QLineEdit{
				border-radius: 10px;
           		font-size: 13px;
             	padding: 4px;
              	selection-background-color: lightgray;
                selection-color: black;
               	max-width: 800px
            }
            
            QLineEdit:hover{
                border: 1px solid grey;
            }
            '''
        self.urlbar.setStyleSheet(urlbar_style)

        # Adding action to line edit when return key is pressed
        self.urlbar.returnPressed.connect(self.navigate_to_url)

        # Adding line edit to tool bar
        self.navtb.addWidget(self.urlbar)

        # Stop action
        stop_btn = QAction('Stop', self)
        stop_btn.setStatusTip('Stop loading current page')
        stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
        self.navtb.addAction(stop_btn)

        # Search button
        search_btn = QAction('Search', self)
        search_btn.setStatusTip('Search the web')
        search_btn.triggered.connect(self.navigate_to_url)
        self.navtb.addAction(search_btn)
        
        spacer = QWidget()
        spacerPolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spacer.setSizePolicy(spacerPolicy)
        
        # Create the settings button
        settings_button = QPushButton()
        settings_button.setMenu(self.create_settings_menu())
        settings_button.setIcon(QIcon(settings_btn_icon_path))

        # Add the spacer and settings button to the toolbar
        self.navtb.addWidget(spacer)
        self.navtb.addWidget(settings_button)

    def set_tab_title(self, index, title):
        truncated_title = self.truncate_tab_text(title, max_length=20)
        self.tabs.setTabText(index, truncated_title)
        
    def on_fullScreenRequested(self, request):
        request.accept()
        if request.toggleOn():
            self.enterFullScreenMode()
        else:
            self.exitFullScreenMode()
    
    def enterFullScreenMode(self):
        self.browserFullScreen = True
        self.previousWindowState = self.windowState()

        # Hide all the unnecessary widgets
        self.navtb.setVisible(False)
        self.status.setVisible(False)
        self.urlbar.setVisible(False)
        self.tabs.tabBar().hide()

        self.tabs.currentWidget().setFocus()
        self.setFocus()
        self.showFullScreen()
        
    def exitFullScreenMode(self):
        self.browserFullScreen = False

        # Restore the original layout
        # First, ensure the window is in its normal state before applying the stored state
        self.showNormal() 

        # Apply the previous window state
        self.setWindowState(self.previousWindowState)
        current_web_engine_view = self.tabs.currentWidget()
        if isinstance(current_web_engine_view, QWebEngineView):
            current_web_engine_view.page().runJavaScript("document.exitFullscreen();")

        # If the previous state was maximized, explicitly call showMaximized()
        if self.previousWindowState == Qt.WindowState.WindowMaximized:
            self.showMaximized()

        # Make UI elements visible again
        self.navtb.setVisible(True)
        self.status.setVisible(True)
        self.urlbar.setVisible(True)
        self.tabs.setVisible(True)
        self.tabs.tabBar().show()
        if self.tabs.currentIndex() >= 0:
            self.tabs.currentWidget().setFocus()

    def keyPressEvent(self, event):
        print("Key Pressed:", event.key())  # Debugging line
        if event.key() == Qt.Key.Key_Escape:
            if self.browserFullScreen:
                self.exitFullScreenMode()
            else:
                super(MainWindow, self).keyPressEvent(event)

	# Method for adding new tab
	# If url is blank, create google url
    def add_new_tab(self, qurl=None, label='Blank'):
        if qurl is None:
            qurl = QUrl('http://www.google.com')
        browser = QWebEngineView()
        browser.setUrl(qurl)

        # Functionality to update search history in browser 
        browser.urlChanged.connect(self.update_history)

        # Connect the fullScreenRequested signal to the handler
        browser.page().fullScreenRequested.connect(self.on_fullScreenRequested)
        browser.page().settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.titleChanged.connect(lambda title, index=i: self.set_tab_title(index, title))
        
        # Truncate the tab text and set it
        truncated_label = self.truncate_tab_text(label, max_length=20)
        self.tabs.setTabText(i, truncated_label)

		# Adding action to update the browser when url is changed (update the url)
        browser.urlChanged.connect(lambda qurl, browser = browser:
								    self.update_urlbar(qurl, browser))

		# Adding action to browser when loading is finished
		# Set the tab title
        browser.loadFinished.connect(lambda _, i=i, browser=browser: 
                             self.tabs.setTabText(i, self.truncate_tab_text(browser.page().title(), max_length=20)))
        
    def update_history(self, qurl):
        title = self.tabs.currentWidget().page().title()
        self.browserHistory.append((title, qurl.toString()))
        
    def show_history(self):
        dialog = HistoryDialog(self.browserHistory, self)
        if dialog.clear_history():
            self.browserHistory.clear()
        
    def create_settings_menu(self):
        settings_menu = QMenu(self)
        
        # Existing theme actions...

        view_history_action = QAction("View History", self)
        view_history_action.triggered.connect(self.show_history)
        settings_menu.addAction(view_history_action)

        return settings_menu

    def truncate_tab_text(self, text, max_length):
        if len(text) > max_length:
            return text[:max_length - 3] + '...'
        return text

		# When double clicked is pressed on tabs
		# First, check the index i.e
  		# If there are no tabs under the click, create a new tab
    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab()

	# When tab is changed, get the curl, and update the url
    def current_tab_changed(self, i):

        # Check if the current widget is a QWebEngineView and not None
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, QWebEngineView):
            qurl = current_widget.url()
            self.update_urlbar(qurl, current_widget)
            self.update_title(current_widget)

	# When tab is closed
    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return

        # Get the widget (QWebEngineView) of the tab to be closed
        widget_to_close = self.tabs.widget(i)
        self.tabs.removeTab(i)

        # Explicitly delete the QWebEngineView widget
        if widget_to_close is not None:
            widget_to_close.deleteLater()

	# Method for updating the title
    # This method now ensures the tab text is updated with the page title correctly
    def update_title(self, browser):
        if browser != self.tabs.currentWidget():
            return
        title = self.tabs.currentWidget().page().title()
        index = self.tabs.currentIndex()
        self.tabs.setTabText(index, self.truncate_tab_text(title, max_length=20))
        self.setWindowTitle('% s - Rocket' % title)

	# Action for home to be set as google
    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QUrl('http://www.google.com'))

    def navigate_to_url(self):

		# Get the line edit text and convert it to QUrl object
		# If scheme is blank, set scheme
        q = QUrl(self.urlbar.text())
        if q.scheme() == "":
            q.setScheme('http')

        self.tabs.currentWidget().setUrl(q)

    def update_urlbar(self, q, browser = None):

		# If this signal is not from the current tab, ignore
        if browser != self.tabs.currentWidget():
            return
		
        if q.scheme() == 'https':
            self.httpsicon.setPixmap(QPixmap(self.ssl_icon_path))
            self.httpsicon.setToolTip('This site is secure')
		
        else:
            self.httpsicon.setPixmap(QPixmap(self.no_ssl_icon_path))
            self.httpsicon.setToolTip('This site is not secure')

        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    app.setApplicationName('Rocket')
    app.exec()

if __name__ == '__main__':
    main()
