import sys
import socket

from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QApplication,
    QMainWindow,
    QMessageBox,
    QTableView,
    QHeaderView,
)

#class Contacts(QMainWindow):
class Contacts(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OCL Contacts")
        self.resize(415, 200)
        # Set up the model
        self.model = QSqlTableModel(self)
        self.model.setTable("contacts")
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.model.setHeaderData(0, Qt.Horizontal, "Name")
        self.model.setHeaderData(1, Qt.Horizontal, "Phone Number")
        self.model.setHeaderData(2, Qt.Horizontal, "Email Address")
        self.model.setHeaderData(3, Qt.Horizontal, "Group")
        self.model.select()
        # Set up the view
        self.view = QTableView()
        self.view.setAlternatingRowColors(True)
        self.view.setShowGrid(False)
        self.view.setModel(self.model)
        #self.view.resizeColumnsToContents()
        #self.setCentralWidget(self.view)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        self.lay = QVBoxLayout() 
        self.lay.addWidget(self.view)
        self.lfor = QFormLayout()
        self.ename = QLineEdit()
        self.ephone = QLineEdit()
        self.eemail = QLineEdit()
        self.lfor.addRow('Name', self.ename)
        self.lfor.addRow('Phone number', self.ephone)
        self.lfor.addRow('Email address', self.eemail)
        self.lay.addLayout(self.lfor)
        self.bsave = QPushButton('Save')
        self.bsave.clicked.connect(self.addcontact)
        self.bload = QPushButton('Load')
        self.bload.clicked.connect(self.getcontact)
        self.bdel = QPushButton('Delete')
        self.bdel.clicked.connect(self.deletecontact)
        self.buttons = QHBoxLayout()
        self.buttons.addWidget(self.bsave)
        self.buttons.addWidget(self.bload)
        self.buttons.addWidget(self.bdel)
        self.lay.addLayout(self.buttons)
        self.setLayout(self.lay)
        self.emergency_phones = set()

        self.model.dataChanged.connect(self.groupchanged)
        self.updateEmergencyPhoneList(False)
        self.UDP_IP = "192.168.1.56"
        self.UDP_PORT = 8888


    def updateEmergencyPhoneList(self, parse=False):
        phonelist = set()
        for row in range(self.model.rowCount()):
            gr = self.view.model().index(row, 3).data()
            if gr & 0b1:  # group in first 
                phonelist.add(self.view.model().index(row, 1).data())
        changed = phonelist != self.emergency_phones
        self.emergency_phones = phonelist
        return changed & parse

    def groupchanged(self, a, b):
        print(f'Data has changed: database with {self.model.rowCount()}')
        if self.updateEmergencyPhoneList(True):
            fona = ','.join(self.emergency_phones)
            numphones = '{:02d}'.format(len(self.emergency_phones))
            fona = f'!{fona},N{numphones}'
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(bytes(fona, "ascii"), (self.UDP_IP, self.UDP_PORT))
            sock.close()

    def addcontact(self):
        query = QSqlQuery() ## instead of exec sql raw queries, can use QsqlRecord
        name = self.ename.text()
        phone = self.ephone.text()
        email = self.eemail.text()
        nonempty = name and phone and email
        if nonempty and query.exec(f"""INSERT INTO contacts (name, phone, email, groupINT) VALUES ('{name}', '{phone}', '{email}', '0')"""):
            self.ename.clear()
            self.ephone.clear()
            self.eemail.clear()
        else:
            print('Query not commited')
        query.finish()
        self.model.select()
    def getcontact(self):
        idx = self.view.selectionModel().selectedIndexes()
        rows = [ii.row() for ii in idx]
        if len(rows):
            row = rows[-1]
            name  = self.view.model().index(row, 0).data()
            phone = self.view.model().index(row, 1).data()
            email = self.view.model().index(row, 2).data()
            print(name, phone, email)
        else:
            print('No row selected')
    def deletecontact(self):
        idx = self.view.selectionModel().selectedIndexes()
        rows = [ii.row() for ii in idx]
        if len(rows):
            self.view.model().removeRow(rows[-1])
        else:
            print('No row selected')
        self.model.select()



def createConnection():
    con = QSqlDatabase.addDatabase('QMARIADB')
    con.setDatabaseName("OCL_INFO")
    con.setHostName("192.168.0.25")
    #con.setHostName("localhost")
    con.setPort(3307)
    con.setUserName("ocl")
    con.setPassword("DB@clo280220")

    if not con.open():
        QMessageBox.critical(
            None,
            "QTableView Example - Error!",
            "Database Error: %s" % con.lastError().databaseText(),
        )
        return False
    return True

app = QApplication(sys.argv)
app.setStyleSheet("QTableView::item:alternate {background-color: #dadada;} QTableView::item {background-color: #ececec;}")
if not createConnection():
    sys.exit(1)
win = Contacts()
win.show()
sys.exit(app.exec())
