from PySide.QtCore import QFile
def loadStyleSheet(sheetName):
    file = QFile(sheetName)
    file.open(QFile.ReadOnly)
    styleSheet = file.readAll()
    return styleSheet

# data dir
# custom user settings
