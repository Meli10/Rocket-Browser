# importing required libraries
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtPrintSupport import *
import sys


# main window
class MainWindow(QMainWindow):

	# constructor
	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)

		self.setWindowIcon(QIcon("pics/rocket.png"))
		self.setIconSize(QSize(80, 80))
		self.showMaximized()
		self.setWindowTitle("Rocket")
		self.setStyleSheet(".QIcon:: {font-size: 11px;}")
		self.tabs = QTabWidget()
		self.tabs.setDocumentMode(True)
		self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick) # adding action when double clicked
		self.tabs.currentChanged.connect(self.current_tab_changed) 		 # adding action when tab is changed
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.close_current_tab) 	 # adding action when tab close is requested
		self.setCentralWidget(self.tabs)
		self.tabs.setStyleSheet(".QTabBar::tab {font-size: 11px; width: 100px; height: 25px; margin-left: 1px; border-radius: 2px; background: 'lightgrey'}")
  
		self.status = QStatusBar()
		self.setStatusBar(self.status) 									 # setting status bar to the main window

		navtb = QToolBar('Navigation')

		self.addToolBar(navtb)											 # adding tool bar to the main window

		back_btn = QAction('Back', self)

		back_btn.setIcon(QIcon('pics/backward.png'))
		back_btn.setStatusTip('Back to previous page')
		# adding action to back button
		# making current tab to go back
		back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
		# adding this to the navigation tool bar
		navtb.addAction(back_btn)

		# Adding next button
		next_btn = QAction('Forward', self)
		next_btn.setIcon(QIcon('pics/Forward.png'))
		next_btn.setStatusTip('Forward to next page')
		next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
		navtb.addAction(next_btn)

		# Adding reload button
		reload_btn = QAction('Refresh', self)
		reload_btn.setIcon(QIcon('pics/Refresh.png'))
		reload_btn.setStatusTip('Refresh page')
		reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
		navtb.addAction(reload_btn)

		# Creating home action
		home_btn = QAction('Home', self)
		home_btn.setStatusTip('Go home')
		home_btn.setIcon(QIcon('pics/home.png'))

		# Adding action to home button
		home_btn.triggered.connect(self.navigate_home)
		navtb.addAction(home_btn)

		# Adding a separator
		navtb.addSeparator()

		# Creating a line edit widget for URL
		self.urlbar = QLineEdit()
		urlbar_style = '''
  			QLineEdit{
				border-radius: 4px;
           		font-size: 13px;
             	padding: 4px;
              	selection-background-color: red;
               	max-width: 500px
            }
            
            QLineEdit:hover{
                color: blue;
                
            }
            '''
            
		
		self.urlbar.setStyleSheet(urlbar_style)
		# adding action to line edit when return key is pressed
		self.urlbar.returnPressed.connect(self.navigate_to_url)

		# adding line edit to tool bar
		navtb.addWidget(self.urlbar)

		# Adding stop action
		stop_btn = QAction('Stop', self)
		stop_btn.setStatusTip('Stop loading current page')
		stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
		navtb.addAction(stop_btn)

		# Adding search button
		search_btn = QAction('Search', self)
		search_btn.setStatusTip('Search for the web')
		search_btn.triggered.connect(self.navigate_to_url)
		navtb.addAction(search_btn)
  
		# creating first tab
		self.add_new_tab(QUrl('http://www.google.com'), 'Homepage')
		# showing all the components
		self.show()
  
	# method for adding new tab
	def add_new_tab(self, qurl = None, label ="Blank"):
		# if url is blank
		if qurl is None:
			# creating a google url
			qurl = QUrl('http://www.google.com')
			


		# creating a QWebEngineView object
		browser = QWebEngineView()
		# setting url to browser
		browser.setUrl(qurl)
		
		# setting tab index
		i = self.tabs.addTab(browser, label)
		self.tabs.setCurrentIndex(i)
		
		# adding action to the browser when url is changed
		# update the url
		browser.urlChanged.connect(lambda qurl, browser = browser:
								self.update_urlbar(qurl, browser))

		# adding action to the browser when loading is finished
		# set the tab title
		browser.loadFinished.connect(lambda _, i = i, browser = browser:self.tabs.setTabText(i, browser.page().title()))
  
		# when double clicked is pressed on tabs
		# Check the index i.e
  		# if there are no tabs under the click, create a new tab
	def tab_open_doubleclick(self, i):
		if i == -1:
			# creating a new tab
			self.add_new_tab()

	# when tab is changed
	def current_tab_changed(self, i):
		# get the curl
		qurl = self.tabs.currentWidget().url()
		# update the url
		self.update_urlbar(qurl, self.tabs.currentWidget())

		# update the title
		self.update_title(self.tabs.currentWidget())

	# when tab is closed
	def close_current_tab(self, i):

		# if there is only one tab
		if self.tabs.count() < 2:
			# do nothing
			return
		# else remove the tab
		self.tabs.removeTab(i)

	# method for updating the title
	def update_title(self, browser):

		# if signal is not from the current tab
		if browser != self.tabs.currentWidget():
			# do nothing
			return

		# get the page title
		title = self.tabs.currentWidget().page().title()
	
		# set the window title
		self.setWindowTitle("% s - Rocket" % title)

		
		
	# action to go to home
	def navigate_home(self):

		# go to google
		self.tabs.currentWidget().setUrl(QUrl("http://www.google.com"))

	# method for navigate to url
	def navigate_to_url(self):

		# get the line edit text
		# convert it to QUrl object
		q = QUrl(self.urlbar.text())
		# if scheme is blank
		if q.scheme() == "":
			# set scheme
			q.setScheme('http')
   

		# set the url
		self.tabs.currentWidget().setUrl(q)

	# method to update the url
	def update_urlbar(self, q, browser = None):

		# If this signal is not from the current tab, ignore
		if browser != self.tabs.currentWidget():
			return

		# set text to the url bar
		self.urlbar.setText(q.toString())

		# set cursor position
		self.urlbar.setCursorPosition(0)


if __name__ == '__main__':
# creating a PyQt5 application
	app = QApplication(sys.argv)
	style = '''
		QTabWidget{
     		color: blue;
			Background: green;
    	}'''

	app.setStyleSheet(style)
	# setting name to the application
	app.setApplicationName('Rocket')

	# creating MainWindow object
	window = MainWindow()
	# loop
	app.exec_()
