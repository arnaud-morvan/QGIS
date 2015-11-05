# -*- coding: utf-8 -*-

import sys
import os
import atexit
from mock import Mock
from qgis.core import QgsApplication
from qgis.gui import QgisInterface
from PyQt4 import QtCore


QGISAPP = None  # Static used to hold hand to running QGis application
IFACE = None


def getQgisTestApp(locale=''):
    """ Start one QGis application to test against

    Input
        NIL

    Output
        handle to qgis app


    If QGis is already running the handle to that app will be returned
    """

    global QGISAPP
    if QGISAPP is None:
        myGuiFlag = True  # All test will run qgis in gui mode
        QGISAPP = QgsApplication(sys.argv, myGuiFlag)
        if 'QGIS_PREFIX_PATH' in os.environ:
            myPath = os.environ['QGIS_PREFIX_PATH']
            print 'QGIS_PREFIX_PATH=', myPath
            myUseDefaultPathFlag = True
            QGISAPP.setPrefixPath(myPath, myUseDefaultPathFlag)
        else:
            print 'Warning: QGIS_PREFIX_PATH is not set'

        QtCore.QCoreApplication.setOrganizationName('QGIS')
        QtCore.QCoreApplication.setOrganizationDomain('qgis.org')
        QtCore.QCoreApplication.setApplicationName('QGIS2')

        QGISAPP.initQgis()
        atexit.register(QgsApplication.exitQgis)

        # Initialize locale
        mySettings = QtCore.QSettings()
        myUserLocale = mySettings.value('locale/userLocale', '')
        myLocaleOverrideFlag = mySettings.value('locale/overrideFlag', False)

        if (locale):
            mySettings.setValue("locale/userLocale", locale)
        else:
            if (myLocaleOverrideFlag == False or myUserLocale == ''):
                locale = QtCore.QLocale.system().name()

                # Set system locale in QSettings for plugins
                mySettings.setValue("locale/userLocale", locale)
            else:
                locale = myUserLocale
    return QGISAPP


def getQgisTestIface():
    ''' Create an QgisInterface mock

    Tests authors can customize the iface mock to fit their needs.

    Example:
        iface = getQgisTestIface()

        iface.mainWindow.return_value = QtGui.QMainWindow()
        iface.mapCanvas.return_value = QgsMapCanvas(iface.mainWindow)
        iface.mapCanvas.resize(QtCore.QSize(400, 400))

        iface.activeComposers.return_value = []

        iface.firstRightStandardMenu.return_value = QtGui.QMenu()
    '''

    global IFACE
    if IFACE is None:
        IFACE = Mock(spec=QgisInterface)

        from qgis import utils
        utils.iface = IFACE

    return IFACE
