print("Disclaimer: the console window is mandatory for internet speed test to work, it will be hidden afterwards")
from PyQt5.QtWidgets import QMainWindow,QApplication,QMessageBox ,QPushButton
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
#from PyQt5.QtGui import QMovie
import sys
import PyQt5
import os
from os import path, environ
import time, math
import requests
import speedtest
from win32 import win32api
from win32 import win32process
from win32 import win32gui

FORM_CLASS,_=loadUiType(path.join(path.dirname(__file__), "main.ui"))


def callback(hwnd, pid):
  if win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
    # hide window
    win32gui.ShowWindow(hwnd, 0)

# find hwnd of parent process, which is the cmd.exe window
win32gui.EnumWindows(callback, os.getppid())

#Supress Warning
def suppress_qt_warnings():
    environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    environ["QT_SCALE_FACTOR"] = "1"


class MainWindow(QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.HandleUI_Time()
        self.HandleButtons()
        self.HandleEvents()
    
    def HandleUI_Time(self):
        self.setWindowTitle("Time Estimator")

    def HandleButtons(self):
        self.Start_PB.clicked.connect(self.StartFunc)
        self.cls_PB.clicked.connect(self.closeApp)
        self.go_to_Data_PB.clicked.connect(self.go_to_Data)
        self.SpeedTest_PB.clicked.connect(self.SpeedTest)
    
    def HandleEvents(self):
        #on text change reset color to black
        self.input_AvSp.textChanged.connect(self.resetAV_L)
        self.input_Si.textChanged.connect(self.resetSi_L)
        self.input_Comp.textChanged.connect(self.resetComp_L)

        #on enter key while on any input, start calculation
        self.input_AvSp.returnPressed.connect(self.StartFunc)
        self.input_Comp.returnPressed.connect(self.StartFunc)
        self.input_Si.returnPressed.connect(self.StartFunc)

    #exit app on escape key
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            sys.exit()
        
    #reset colors on event

    def resetAV_L(self):
        self.label_AvSp.setStyleSheet("color: black")
        self.resetGlobal()

    def resetSi_L(self):
        self.label_Si.setStyleSheet("color: black")
        self.resetGlobal()
        
    def resetComp_L(self):
        self.label_Comp.setStyleSheet("color: black")
        self.label_Perc.setStyleSheet("color: black")
        self.resetGlobal()
    
    #reset size and hide error
    def resetGlobal(self):
        self.label_Er.hide()
        self.setFixedHeight(187)
        self.border_bottom.move(0,184)
    


    def error_AvSP(self):
        self.input_AvSp.setFocus()
        self.input_AvSp.setSelection(0,100)
        self.label_AvSp.setStyleSheet("color: red")
    def error_Si(self):
        self.input_Si.setFocus()
        self.input_Si.setSelection(0,100)
        self.label_Si.setStyleSheet("color: red")
    def error_Comp(self):
        self.label_Comp.setStyleSheet("color: red")
        self.label_Perc.setStyleSheet("color: red")
        self.input_Comp.setFocus()
        self.input_Comp.setSelection(0,100)

    def StartFunc(self):
        #Error Checking:

        er = 0 #define error count

        #take inputs
        iAvSp = self.input_AvSp.text()
        iSi = self.input_Si.text()
        iComp = self.input_Comp.text()

        try:
            iAvSp = eval(iAvSp)
            iSi = eval(iSi)
        except:
            pass


        #collect errors

        #check AvSp
        chk1 = iAvSp
        if chk1 =='' or chk1 == '0':
            self.error_AvSP()
            er = er + 1
        else:
            try:
                chk1= float(chk1)
                if chk1 == 0 or chk1 < 0:
                    self.error_AvSP()
                    er = er + 1
            except:
                chk1 = 0
                self.error_AvSP()
                er = er + 1
        
        #check Si

        chk2 = iSi
        if chk2 =='' or chk2 == '0':
            self.error_Si()
            er = er + 1
        else:
            try:
                chk2= float(chk2)
                if chk2 == 0 or chk2 < 0:
                    self.error_Si()
                    er = er + 1
            except:
                chk2 = 0
                self.error_Si()
                er = er + 1
        
        #check Comp

        chk3 = iComp
        if chk3 == "":
            self.input_Comp.setText("0")
            iComp = 0
            chk3 = 0
        try:
            chk3= float(chk3)
            if chk3 < 0 or chk3 > 100:
                self.error_Comp()
                er = er + 1
        except:
            chk3 = 0
            self.error_Comp()
            er = er + 1
        
        #Check Now
        if er != 0:
            #QMessageBox.critical(self, "Error", "Please provide correct values") #Display message 
            self.label_Er.show()
            return
        
        #percentage
        oPrc = float(iComp)
        Prc = 100 - oPrc
        Prc = Prc * 0.01

        #Speed calc
        Speed = float(iAvSp)
        Sdiag = Speed #for history dialog that to be added later
        #get selected unit
        RB1 = self.RB_KBs.isChecked()
        RB2 = self.RB_MBs.isChecked()
        RB3 = self.RB_Mbs.isChecked()


        #convert any to Megabytes per second
        if RB1 == 1:
            Speed = Speed / 1024
            SdiagU = "KB/s" #for history dialog that to be added later
        if RB2 == 1:
            SdiagU = "MB/s" #for history dialog that to be added later
        if RB3 == 1:
            Speed = Speed / 8
            SdiagU = "Mb/s" #for history dialog that to be added later
        
        #convert speed to bytes per second
        Speed = Speed * 1024 * 1024

        #Size calc
        Size = float(iSi)
        SizeDiag = Size #for history dialog that to be added later

        #get selected unit
        RB4 = self.RB_GB.isChecked()
        RB5 = self.RB_MB.isChecked()
        RB6 = self.RB_TB.isChecked()


        #convert any to bytes
        if RB4 == 1:
            Size = Size * 1024 * 1024 * 1024
            SizeDiagU = "GB" #for history dialog that to be added later
        if RB5 == 1:
            Size = Size * 1024 * 1024
            SizeDiagU = "MB" #for history dialog that to be added later
        if RB6 == 1:
            Size = Size * 1024 * 1024 * 1024 * 1024
            SizeDiagU = "TB" #for history dialog that to be added later
        
        #Calculate Total Time in seconds
        T = Size / Speed
        T = T * Prc
        Days = 0 #initiate Days
        Month = 0 #initiate Month
        ##calculate Days, Month and Years
        #####################################################
        Days = T / 86399
        T = T % 86399
        Month = Days / 30
        Days = Days % 30
        Days = math.floor(Days)
        Month = math.floor(Month)
        Years = Month / 12
        Month = Month % 12
        Month = math.floor(Month)
        Years = math.floor(Years)

        #convert remains to readable format
        T = str(time.strftime('%H:%M:%S', time.gmtime(T)))
        

        #string numbers for message
        Tmsg = str(T)
        Dmsg = str(Days)
        Mmsg = str(Month)
        Ymsg = str(Years)

        ##define messages
        Fmsg_ho = (Tmsg) #hours only
        Fmsg_ho = "".join(Fmsg_ho)
        Fmsg_hd = (Dmsg," Day(s) and ", Tmsg) #hours and days
        Fmsg_hd = "".join(Fmsg_hd)
        Fmsg_mh = (Mmsg," Month(s) and ", Tmsg) #month and hours
        Fmsg_mh = "".join(Fmsg_mh)
        Fmsg_all = (Mmsg," Month(s), ", Dmsg," Day(s) and ", Tmsg) #Month, Days and hours
        Fmsg_all = "".join(Fmsg_all)

        #Switch messages
        if Mmsg == "0" and Dmsg == "0":
            Fmsg = Fmsg_ho
        if Dmsg == "0" and Mmsg != "0":
            Fmsg = Fmsg_mh
        if Mmsg == "0" and Dmsg != "0":
            Fmsg = Fmsg_hd
        if Mmsg != "0" and Dmsg != "0":
            Fmsg = Fmsg_all
        if Tmsg == "00:00:00":
            Fmsg = "Less than a second, or already done"
        
        #add years
        if Years != 0:
            Fmsg = (Ymsg, " Year(s), ",Fmsg)
            Fmsg = "".join(Fmsg)


        #setup message box
        ################

        Txttemp = ("Time is: ", Fmsg)
        Fmsg = "".join(Txttemp)
        res = QMessageBox(self)
        res.setText(Fmsg)
        res.setWindowTitle("Time")
        res.setIcon(QMessageBox.Information)
        resIcon = QPixmap(":/go_to_Time/Files/Buttons/go_to_Time/Normal.png")
        resIcon = QPixmap.transformed(resIcon, QTransform().scale(0.25, 0.25), Qt.SmoothTransformation)
        #res.setIconPixmap(resIcon) #set large icon
        #res.exec_() #display message
        #######################
        #expand and view result (instead of messagebox)
        self.setFixedHeight(230)
        self.border_bottom.move(0,227)
        self.label_Result.setText(Fmsg)
    


    def SpeedTest(self):
        #initiate messagebox
        testWhat = QMessageBox(self)
        testWhat.setText("What do you want to Test?")
        testWhat.setWindowTitle("Speed Benchmark")
        testWhat.setIcon(QMessageBox.Question)
        testWhat.addButton(QPushButton('Internet Download Speed'), QMessageBox.YesRole)
        testWhat.addButton(QPushButton('Disk Write Speed'), QMessageBox.NoRole)
        testWhat.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)
        testWhatIcon = QPixmap(":/go_to_Time/Files/Buttons/go_to_Time/Normal.png")
        testWhatIcon = QPixmap.transformed(testWhatIcon, QTransform().scale(0.25, 0.25), Qt.SmoothTransformation)
        #Display messagebox
        reply = testWhat.exec_()
        #process replys:
        if reply == 0: #internet:
            #check for connection:
            test_url = "http://www.google.com"
            test_timeout = 5
            try:
	            request = requests.get(test_url, timeout=test_timeout)
            except (requests.ConnectionError, requests.Timeout) as exception:
                QMessageBox.critical(self, "Error", "Seems there's no internet connection.\n It's either that or google is down. Oops!")
                return

            #initiate test:
            self.StartLoading_internet()
            self.worker = WorkerThread()
            self.worker.start()
            #When finished stop loading and reset text
            self.worker.finished.connect(self.evntworker_finished)
            #capture download speed value and set it in gui
            self.worker.return_val.connect(self.setInternet_Value)
            
        elif reply == 1:
            QMessageBox.information(self, "Still in dev", "Still in dev")

            pass
        elif reply == 2:

            pass


    #set Internet speed value to GUi:
    def setInternet_Value(self,return_Val):
        return_Val = str(round(return_Val,3)) #round then convert to string
        self.input_AvSp.setText(return_Val) #set value
        self.RB_KBs.setChecked(1) #check KB/s Unit
    
    #when thread ends, stop the loading animation and text:
    def evntworker_finished(self):
        self.EndLoading_Internet()
    
    def HandleUI_Time(self):
        self.setWindowTitle('test')


    def history_diag(self):
            pass

    def labelEr_reset(self):
        self.label_Er.hide()
        self.label_Er.setText("Provide correct values!")
        self.label_Er.setToolTip("Please recheck the highlighted values (red)")


    def StartLoading_internet(self):
        self.label_Er.setToolTip("Please wait, Internet speed test in progress")
        self.label_Er.setText("Testing Internet Speed")
        self.label_Er.show()
        self.startAnimation()

    def EndLoading_Internet(self):
        self.stopAnimation()
        self.labelEr_reset()
        

    def startAnimation(self):
        self.loading.show()
        self.movie.start()
        
    def stopAnimation(self):
        self.movie.stop()
        self.loading.hide()




    def closeApp(self):
        sys.exit()
    

    #allow window drag
    def mousePressEvent(self, event):
        
        if event.buttons() == Qt.LeftButton:
            self.dragPos = event.globalPos()
            event.accept()
    def mouseMoveEvent(self, event):
    
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()

    #Go to data estimator
    def go_to_Data(self):
        QMessageBox.information(self, "Data Estimator is still in dev", "Still in development")

class WorkerThread (QThread):
    return_val = pyqtSignal(float)
    def run(self):
        isp = speedtest.Speedtest()
        isp.get_servers()
        isp.get_best_server()
        DSP = isp.download()
        #convert speed to KB/s
        DownloadSP = DSP / 1024 / 8
        #emit speed value
        self.return_val.emit(DownloadSP)


def main():
    
    app = QApplication(sys.argv)
    window = MainWindow()
    app.setApplicationDisplayName('ES Time')
    window.setWindowTitle('Estimator')

    #set size
    window.setFixedHeight(187)
    window.border_bottom.move(0,184)

    #load fonts
    font_status = PyQt5.QtGui.QFontDatabase.addApplicationFont(':/Font/Files/Fonts/ArcaMajora3-Bold.otf') #set font (returns -1 if failed)
    font_status_2 = PyQt5.QtGui.QFontDatabase.addApplicationFont(':/Font/Files/Fonts/ArcaMajora3-Heavy.otf')

    window.label_Er.hide() #Hide Error label

    window.SizeBrowse_PB.hide() #Hide Browse Button (still in dev)

    #Get App location path for no reason (yet):
    if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
    elif __file__:
            application_path = os.path.dirname(__file__)
    
    #initiate loading animation
    window.movie = QMovie(":/Animation/Files/Animation/loader.gif")
    window.loading.setMovie(window.movie)

    window.show()

    #Warning for failed font loading:
    if font_status == -1 or font_status_2 == -1:
        QMessageBox.Warning(window, "Font failed to load", "Font failed to load, using default system font")
    app.exec_()
if __name__ == '__main__':
    suppress_qt_warnings()
    main()