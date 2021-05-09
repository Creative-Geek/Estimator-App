#print("Disclaimer: the console window is mandatory for internet speed test to work, it will be hidden afterwards")
from PyQt5.QtWidgets import QMainWindow,QApplication,QMessageBox ,QPushButton
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
from PyQt5 import QtCore
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
import pickle

if getattr(sys, 'frozen', False):
        app_path = os.path.dirname(sys.executable)
elif __file__:
        app_path = os.path.dirname(__file__)


import qtmodern.styles
import qtmodern.windows

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
    environ["QT_SCALE_FACTOR"] = str(ScaleFact)

testinginprogress = 0
#load settings goes here
#default settings:
global Stayontop
global darkmode
global resetfields
global viewResMsgBox
global ScaleFact
global configpath
darkmode = 0
ScaleFact = 1
Stayontop = 1
viewResMsgBox = 1
resetfields = 0

configpath = "".join((app_path,'/','config.ini'))
try:
    configFile = pickle.load(open(configpath,"rb"))
    #print(configFile)
    darkmode = configFile[0]
    ScaleFact = configFile[1]
    Stayontop = configFile[2]
    viewResMsgBox = configFile[3]
    resetfields = configFile[4]
    #print (darkmode)
except:
    pass



class MainWindow(QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        QMainWindow.__init__(self)
        self.setupUi(self)
        if Stayontop == 1:
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        else: self.setWindowFlags(Qt.FramelessWindowHint)
        self.HandleUI_Time()
        self.HandleButtons()
        self.HandleEvents()
        self.tabWidget.setCurrentIndex(0) #go to data estimator regardless
        self.setSettings()
    


    def setSettings(self):
        if darkmode == 1:
            self.DM_check.setChecked(1)
        if Stayontop == 1:
            self.SoT_check.setChecked(1)
        if viewResMsgBox == 1:
            self.resMsgBox_check.setChecked(1)
        if resetfields == 1:
            self.resetFields_check.setChecked(1)
        self.scaleSpin.setValue(ScaleFact)
        
    def HandleUI_Time(self):
        self.setWindowTitle("Time Estimator")

    def HandleButtons(self):
        self.Start_PB.clicked.connect(self.StartFunc)
        self.cls_PB.clicked.connect(self.closeApp)
        self.mini_PB.clicked.connect(self.minimizeApp)
        self.SpeedTest_PB.clicked.connect(self.SpeedTest)
        self.StartD_PB.clicked.connect(self.StartFuncD)
        self.ResetD_PB.clicked.connect(self.resetDataSpins)
        self.Save_PB.clicked.connect(self.SaveSettings)

    
    def HandleEvents(self):
        #on text change reset color to black
        self.input_AvSp.textChanged.connect(self.resetAV_L)
        self.input_Si.textChanged.connect(self.resetSi_L)
        self.input_Comp.textChanged.connect(self.resetComp_L)
        self.input_AvSpD.textChanged.connect(self.resetAvSp_LD)
        #reset tabs when changed
        self.tabWidget.currentChanged.connect(self.reset_TimeES)
        self.tabWidget.currentChanged.connect(self.resetDall)

        #on enter key while on any input, start calculation
        self.input_AvSp.returnPressed.connect(self.StartFunc)
        self.input_Comp.returnPressed.connect(self.StartFunc)
        self.input_Si.returnPressed.connect(self.StartFunc)
        self.input_AvSpD.returnPressed.connect(self.StartFunc) #in data estimator

        #resave settings vars
        self.SoT_check.stateChanged.connect(self.OnSettingChange)
        self.DM_check.stateChanged.connect(self.OnSettingChange)
        self.resetFields_check.stateChanged.connect(self.OnSettingChange)
        self.resMsgBox_check.stateChanged.connect(self.OnSettingChange)
        self.scaleSpin.valueChanged.connect(self.OnSettingChange)


    #exit app on escape key
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            sys.exit()
    
    def ToggleOnTop(self):
        if Stayontop == 1:
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.show()
        else:
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.show()

    def reset_TimeES(self):
        if resetfields == 0:
            self.setFixedHeight(190)
            self.border_bottom.move(0,187)
            return
        self.resetAV_L()
        self.resetSi_L()
        self.resetComp_L()
        self.resetGlobal
        self.input_AvSp.setText("")
        self.input_Si.setText("")
        self.input_Comp.setText("")
        self.RB_MBs.setChecked(1)
        self.RB_MB.setChecked(1)
    #reset colors on event

    def resetAV_L(self):
        if darkmode == 1:
            self.label_AvSp.setStyleSheet("color: white;")
        else:
            self.label_AvSp.setStyleSheet("color: black;")
        self.resetGlobal()

    def resetSi_L(self):
        if darkmode == 1:
            self.label_Si.setStyleSheet("color: white;")
        else:
            self.label_Si.setStyleSheet("color: black;")
        self.resetGlobal()
        
    def resetComp_L(self):
        if darkmode == 1:
            self.label_Comp.setStyleSheet("color: white;")
            self.label_Perc.setStyleSheet("color: white;")
        else:
            self.label_Comp.setStyleSheet("color: black;")
            self.label_Perc.setStyleSheet("color: black;")
        self.resetGlobal()
    
    #reset size and hide error
    def resetGlobal(self):
        self.label_Er.hide()
        self.setFixedHeight(190)
        self.border_bottom.move(0,187)
    


    def error_AvSP(self):
        self.input_AvSp.setFocus()
        self.input_AvSp.setSelection(0,100)
        if darkmode == 1:
            self.label_AvSp.setStyleSheet("color: #F1304D")
        else:
            self.label_AvSp.setStyleSheet("color: red")
    def error_Si(self):
        self.input_Si.setFocus()
        self.input_Si.setSelection(0,100)
        if darkmode == 1:
            self.label_Si.setStyleSheet("color: #F1304D")
        else:
            self.label_Si.setStyleSheet("color: red")
    def error_Comp(self):
        if darkmode == 1:
            self.label_Comp.setStyleSheet("color: #F1304D")
            self.label_Perc.setStyleSheet("color: #F1304D")
        else:
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
        if viewResMsgBox == 1:
            res.exec_() #display message
        #######################
        #expand and view result (instead of messagebox)
        else:
            self.setFixedHeight(233)
            self.border_bottom.move(0,230)
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
        #testWhatIcon = QPixmap(":/go_to_Time/Files/Buttons/go_to_Time/Normal.png")
        #testWhatIcon = QPixmap.transformed(testWhatIcon, QTransform().scale(0.25, 0.25), Qt.SmoothTransformation)
        #Display messagebox
        if testinginprogress == 0:
            reply = testWhat.exec_()
        else:
            QMessageBox.critical(self, "Error", "A test in already in progress, please wait")
            return
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
        global testinginprogress
        testinginprogress = 1
        self.label_Er.show()
        self.startAnimation()

    def EndLoading_Internet(self):
        self.stopAnimation()
        global testinginprogress
        testinginprogress = 0
        self.labelEr_reset()
        

    def startAnimation(self):
        self.loading.show()
        self.movie.start()
        
    def stopAnimation(self):
        self.movie.stop()
        self.loading.hide()




    def closeApp(self):
        sys.exit()
    










    ## Data Estimator
    def error_AvSPD(self):
        self.input_AvSpD.setFocus()
        self.input_AvSpD.setSelection(0,100)
        if darkmode == 1:
            self.label_AvSpD.setStyleSheet("color: #F1304D")
        else:
            self.label_AvSpD.setStyleSheet("color: red")
    
    def resetAvSp_LD(self):
        if darkmode == 1:
            self.label_AvSpD.setStyleSheet("color:white;")
        else:
            self.label_AvSpD.setStyleSheet("color: black;")
        self.resetGlobalD()

    def resetGlobalD(self):
        self.setFixedHeight(190)
        self.border_bottom.move(0,187)
        self.label_ResultD.setStyleSheet("color: rgb(19, 125, 37);")

    def StartFuncD(self):
        #get values
        iAvSpD = self.input_AvSpD.text()

        Tcents = self.spinCenturies.value()
        Tdecs = self.spinDecades.value()
        Tyers = self.spinYears.value()
        Tmth = self.spinMonths.value()
        Tday = self.spinDays.value()
        Tuhr = self.spinHours.value()
        Tmin = self.spinMinutes.value()
        Tsec = self.spinSeconds.value()


        #calculate total time in seconds
        TotalTimeD = Tcents * 100 * 12 * 30 * 24 * 60 * 60 + Tdecs * 10 * 12 * 30 * 24 * 60 * 60 + Tyers * 12 * 30 * 24 * 60 * 60 + Tmth * 30 * 24 * 60 * 60 + Tday * 24 * 60 * 60 + Tuhr* 60 * 60 + Tmin * 60 + Tsec
        erD = 0 #error count 
        erDl = 0
        try:
            iAvSpD = eval(iAvSpD)
        except:
            pass
        #collect errors
        #check AvSp
        chk1D = iAvSpD
        if chk1D =='' or chk1D == '0':
            self.error_AvSPD()
            erD = erD + 1
        else:
            try:
                chk1D= float(chk1D)
                if chk1D == 0 or chk1D < 0:
                    self.error_AvSPD()
                    erD = erD + 1
            except:
                chk1D = 0
                self.error_AvSPD()
                erD = erD + 1
        #Check Now
        if erD != 0:
            QMessageBox.critical(self, "Error", "Please provide correct values") #Display message 
            return
        
        SpeedD = float(iAvSpD)

        #get speed unit
        SpUD = self.SPcomboBox.currentIndex()
        if SpUD == 0:
            SpeedD = SpeedD / 1024

        if SpUD == 2:
            SpeedD = SpeedD / 8
        
        #convert speed to bytes per second
        SpeedD = SpeedD * 1024 * 1024

        Size_Bytes = TotalTimeD * SpeedD

        if Size_Bytes >= 1125899906842624: #peta
            resD = round(Size_Bytes / 1125899906842624 , 2)
            resD = str(resD)
            msgD = "".join(("You can download ", resD, " Petabytes (PB) in that time"))

        elif Size_Bytes >= 1099511627776: #tera
            resD = round(Size_Bytes/1099511627776, 2)
            resD = str(resD)
            msgD = "".join(("You can download ", resD, " Terabytes (TB) in that time"))

        elif Size_Bytes >= 1073741824: # giga
            resD = round(Size_Bytes/1073741824, 2)
            resD = str(resD)
            msgD = "".join(("You can download ", resD, " Gigabytes (GB) in that time"))

        elif Size_Bytes >= 1048576: #mega
            resD = round(Size_Bytes/1048576,3)
            resD = str(resD)
            msgD = "".join(("You can download ", resD, " Megabytes (MB) in that time"))
        elif Size_Bytes >= 1024: #kilo
            resD = round(Size_Bytes/1024,3)
            resD = str(resD)
            msgD = "".join(("You can only download ", resD, " Kilobytes (KB) in that time"))
        else:
            if Size_Bytes ==0:
                msgD = "ohy! Einstein! Specify a correct time window."
                erDl = erDl + 1
            else:
                resD = Size_Bytes #byte
                resD = str(round(resD,3))
                if resD == "0.0":
                    msgD = 'You must have a "We" internet connection!'
                    erDl = erDl + 1
                else: msgD = "".join(("You can't download anything but ", resD, " bytes in that time"))
        if viewResMsgBox == 0:
            self.setFixedHeight(230)
            self.border_bottom.move(0,227)
            self.label_ResultD.setText(msgD)
            self.label_ResultD.setStyleSheet("color: rgb(19, 125, 37);")
            if erDl == 1:
                if darkmode == 1:
                    self.label_ResultD.setStyleSheet("color:#F1304D;")
                else:
                    self.label_ResultD.setStyleSheet("color:red;")
        elif viewResMsgBox == 1:
            Txttemp = (msgD)
            resD = QMessageBox(self)
            resD.setText(msgD)
            resD.setWindowTitle("Data")
            resD.setIcon(QMessageBox.Information)
            if erDl == 1:
                resD.setIcon(QMessageBox.Critical)
            resD.exec_() #display message

    def resetDall(self):
        if resetfields == 0:
            return
        self.resetDataSpins()
        self.resetSi_inputD()
        self.SPcomboBox.setCurrentIndex(0)


    def resetDataSpins(self):
        self.spinCenturies.setValue(0)
        self.spinDecades.setValue(0)
        self.spinYears.setValue(0)
        self.spinMonths.setValue(0)
        self.spinDays.setValue(0)
        self.spinHours.setValue(0)
        self.spinMinutes.setValue(0)
        self.spinSeconds.setValue(0)

    def resetSi_inputD(self):
        self.input_AvSpD.setText("")




    def minimizeApp(self):
        self.showMinimized()

    #allow window drag
    def mousePressEvent(self, event):
        
        if event.buttons() == Qt.LeftButton:
            self.dragPos = event.globalPos()
            event.accept()
    def mouseMoveEvent(self, event):
    
        if event.buttons() == Qt.LeftButton:
            try:
                self.move(self.pos() + event.globalPos() - self.dragPos)
                self.dragPos = event.globalPos()
                event.accept()
            except: pass


    def OnSettingChange(self):
        pass

    def SaveSettings(self):
        Stayontop = int(self.SoT_check.checkState()/2)
        darkmode = int(self.DM_check.checkState()/2)
        resetfields = int(self.resetFields_check.checkState()/2)
        viewResMsgBox = int(self.resMsgBox_check.checkState()/2)
        ScaleFact = self.scaleSpin.value()
        conlist = (darkmode,ScaleFact,Stayontop,viewResMsgBox,resetfields)
        #print("conlist: ",conlist)
        pickle.dump(conlist, open(configpath,"wb"))
        QMessageBox.information(self, "Saved", "Settings saved!")
        #print(pickle.load(open(configpath,"rb")))

        #reset_restart = QMessageBox(self)
        #reset_restart.setText("Do you want to restart the application?")
        #reset_restart.setWindowTitle("Restart and apply settings now")
        #reset_restart.setIcon(QMessageBox.Question)
        #reset_restart.addButton(QPushButton('Yes'), QMessageBox.YesRole)
        #reset_restart.addButton(QPushButton('No'), QMessageBox.NoRole)
        #restart_reply = reset_restart.exec_()

    #for save button
    def saveSoT(self):
        Stayontop = int(self.SoT_check.checkState()/2)
    def saveDM(self):
        darkmode = int(self.DM_check.checkState()/2)
        #print("darkmode: ",darkmode)
    def saveResetFields(self):
        resetfields = int(self.resetFields_check.checkState()/2)
    def saveMsgBox(self):
        viewResMsgBox = int(self.resMsgBox_check.checkState()/2)
    def saveScale(self):
        ScaleFact = self.scaleSpin.value()
    


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

    configFile = pickle.load(open(configpath,"rb"))
    #print(configFile)
    darkmode = configFile[0]
    ScaleFact = configFile[1]
    Stayontop = configFile[2]
    viewResMsgBox = configFile[3]
    resetfields = configFile[4]
    #print (darkmode)

    

    #setup for Dark mode wrapping
    if darkmode == 1:
        #Tabs
        window.tabWidget.setStyleSheet("QTabBar::tab:selected {border-bottom: 2px solid #00BFF3;} QTabBar::tab:hover {border-bottom: 2px solid #00BFF3;}")
        #TimeES labels
        window.label_AvSp.setStyleSheet("color:white;")
        window.label_Si.setStyleSheet("color:white;")
        window.label_Comp.setStyleSheet("color:white;")
        window.label_Perc.setStyleSheet("color:white;")
        window.label_Result.setStyleSheet("color:#27C499;")
        window.label_Er.setStyleSheet("color:#F1304D;")
        #TimeES inputs
        window.input_AvSp.setStyleSheet("color:white;")
        window.input_Si.setStyleSheet("color:white;")
        window.input_Comp.setStyleSheet("color:white;")
        #TimeES buttons
        window.SpeedTest_PB.setStyleSheet("#SpeedTest_PB { font: 87 8pt 'Arca Majora 3 Heavy'; background: #656565; border-radius: 5.3px; border: 1px solid #FFFFFF; color:white; } #SpeedTest_PB:hover { border: 1.25px solid #FFFFFF; background: #00bff3; } #SpeedTest_PB:pressed { background: #007392; color:lightgray; }")
        window.Start_PB.setStyleSheet("#Start_PB { background: #656565; border-radius: 8px; border: 2px solid #FFFFFF; color:white; } #Start_PB:hover { border: 3px solid #FFFFFF; background: #00bff3; } #Start_PB:pressed {background: #007392; color:lightgray;}")

        #TimeES radios
        window.RB_KBs.setStyleSheet("color:white;")
        window.RB_MBs.setStyleSheet("color:white;")
        window.RB_Mbs.setStyleSheet("color:white;")
        window.RB_MB.setStyleSheet("color:white;")
        window.RB_GB.setStyleSheet("color:white;")
        window.RB_TB.setStyleSheet("color:white;")

        #DataES labels
        window.label_AvSpD.setStyleSheet("color: white;")
        window.label_Time_head.setStyleSheet("color: white;")
        window.label_seconds.setStyleSheet("color:white;")
        window.label_minutes.setStyleSheet("color:white;")
        window.label_hours.setStyleSheet("color:white;")
        window.label_days.setStyleSheet("color:white;")
        window.label_months.setStyleSheet("color:white;")
        window.label_years.setStyleSheet("color:white;")
        window.label_decades.setStyleSheet("color:white;")
        window.label_centuries.setStyleSheet("color:white;")
        window.label_ResultD.setStyleSheet("color:#27C499;")

        #DataES inputs
        window.input_AvSpD.setStyleSheet("color:white;")
        window.SPcomboBox.setStyleSheet("color:white;")
        #DataES spinners
        window.spinSeconds.setStyleSheet("color:white;")
        window.spinMinutes.setStyleSheet("color:white;")
        window.spinHours.setStyleSheet("color:white;")
        window.spinDays.setStyleSheet("color:white;")
        window.spinMonths.setStyleSheet("color:white;")
        window.spinYears.setStyleSheet("color:white;")
        window.spinDecades.setStyleSheet("color:white;")
        window.spinCenturies.setStyleSheet("color:white;")
        #DataES PB
        window.StartD_PB.setStyleSheet("#StartD_PB { background: #656565; border-radius: 8px; border: 2px solid #FFFFFF; color:white; } #StartD_PB:hover { border: 3px solid #FFFFFF; /*color:#00bff3;*/ background: #00bff3; } #StartD_PB:pressed { /*border: 3px solid lightgray;*/ background: #007392; color:lightgray; }")
        window.ResetD_PB.setStyleSheet("#ResetD_PB { font: 87 8pt 'Arca Majora 3 Heavy'; background: #656565; border-radius: 5.3px; border: 1px solid #FFFFFF; color:white; } #ResetD_PB:hover { border: 1.25px solid #FFFFFF; background: #00bff3; } #ResetD_PB:pressed { background: #007392; color:lightgray; }")
        #savePB
        window.Save_PB.setStyleSheet("#Save_PB { font: 87 8pt 'Arca Majora 3 Heavy'; background: #656565; border-radius: 5.3px; border: 1px solid #FFFFFF; color:white; } #Save_PB:hover { border: 1.25px solid #FFFFFF; background: #00bff3; } #Save_PB:pressed { background: #007392; color:lightgray; }")
        #UpdatePB
        window.Update_PB.setStyleSheet("#Update_PB { font: 87 8pt 'Arca Majora 3 Heavy'; background: #656565; border-radius: 5.3px; border: 1px solid #FFFFFF; color:white; } #Update_PB:hover { border: 1.25px solid #FFFFFF; background: #00bff3; } #Update_PB:pressed { background: #007392; color:lightgray; }")
        #scalesettingSpinner
        window.scaleSpin.setStyleSheet("color:white;")
        #Restart_label
        window.Restart_label.setStyleSheet("color:#F1304D;")

    #set size
    window.setFixedHeight(190)
    window.border_bottom.move(0,187)

    #load fonts
    font_status = PyQt5.QtGui.QFontDatabase.addApplicationFont(':/Font/Files/Fonts/ArcaMajora3-Bold.otf') #set font (returns -1 if failed)
    font_status_2 = PyQt5.QtGui.QFontDatabase.addApplicationFont(':/Font/Files/Fonts/ArcaMajora3-Heavy.otf')

    window.label_Er.hide() #Hide Error label
    window.DMW_label.hide()
    window.SizeBrowse_PB.hide() #Hide Browse Button (still in dev)

    #Get App location path for no reason (yet)
    #print(application_path)
    #initiate loading animation
    window.movie = QMovie(":/Animation/Files/Animation/loader.gif")
    window.loading.setMovie(window.movie)
    window.show()

    #load theme
    #fd = QtCore.QFile(":/Themes/Files/Theme/light-blue.qss")
    #if fd.open(QtCore.QIODevice.ReadOnly | QtCore.QFile.Text):
        #qss = QtCore.QTextStream(fd).readAll()
    #fd.close()
    #app.setStyleSheet(qss)
        
    if darkmode == 1:
        qtmodern.styles.dark(app)
        mw = qtmodern.windows.ModernWindow(window.DMW_label)
        #mw.show()
    #Warning for failed font loading:
    if font_status == -1 or font_status_2 == -1:
        QMessageBox.Warning(window, "Font failed to load", "Font failed to load, using default system font")
    ############
    
    app.exec_()
if __name__ == '__main__':
    suppress_qt_warnings()
    main()