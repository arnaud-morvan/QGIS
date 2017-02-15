# -*- coding: utf-8 -*-

"""
***************************************************************************
    ModelerParametersDialog.py
    ---------------------
    Date                 : August 2012
    Copyright            : (C) 2012 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
from builtins import str
from builtins import range


__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import Qt, QUrl, QMetaObject
from qgis.PyQt.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QLineEdit,
                                 QFrame, QPushButton, QSizePolicy, QVBoxLayout,
                                 QHBoxLayout, QTabWidget, QWidget, QScrollArea,
                                 QComboBox, QTableWidgetItem, QMessageBox,
                                 QTextBrowser, QToolButton, QMenu, QAction)
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply

from qgis.core import QgsApplication, QgsNetworkAccessManager

from qgis.gui import QgsMessageBar

from processing.gui.wrappers import InvalidParameterValue
from processing.gui.MultipleInputPanel import MultipleInputPanel
from processing.core.outputs import (OutputRaster,
                                     OutputVector,
                                     OutputTable,
                                     OutputHTML,
                                     OutputFile,
                                     OutputDirectory,
                                     OutputNumber,
                                     OutputString,
                                     OutputExtent,
                                     OutputCrs)
from processing.core.parameters import ParameterPoint, ParameterExtent

from processing.modeler.ModelerAlgorithm import (ValueFromInput,
                                                 ValueFromOutput,
                                                 Algorithm,
                                                 ModelerOutput)

from processing.gui.wrappers import WidgetWrapper


class ModelerWidgetWrapperTest(WidgetWrapper):

    #def __init__(self, wrapper, model_values):
    #    super(ModelerWidgetWrapper, self).__init__()

    def createWidget(self, base_wrapper, model_values):
        self.base_wrapper = base_wrapper
        self.model_values = model_values

        self.model_values_combo = QComboBox()
        for text, value in model_values:
            self.model_values_combo.addItem(text, value)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.model_values_combo, 'Model inputs')
        self.tab_widget.addTab(self.base_wrapper.widget, 'Fixed value')

        self.base_wrapper.widgetValueHasChanged.connect(
            lambda: self.widgetValueHasChanged.emit(self))
        self.model_values_combo.currentIndexChanged.connect(
            lambda: self.widgetValueHasChanged.emit(self))
        self.tab_widget.currentChanged.connect(
            lambda: self.widgetValueHasChanged.emit(self))

        return self.tab_widget

    def setValue(self, value):
        if isinstance(value, ValueFromInput):
            self.setComboValue(value, self.model_values_combo)
            self.tab_widget.setCurrentWidget(self.model_values_combo)
        else:
            self.base_wrapper.setValue(value)
            self.tab_widget.setCurrentWidget(self.base_wrapper.widget)

    def value(self):
        if self.tab_widget.currentWidget() is self.model_values_combo:
            return self.comboValue(combobox = self.model_values_combo)
        if self.tab_widget.currentWidget() is self.base_wrapper.widget:
            return self.base_wrapper.value()


class ModelerWidgetWrapper(WidgetWrapper):

    def createWidget(self, base_wrapper, inputs, outputs):
        self.base_wrapper = base_wrapper
        self.model_values = inputs + outputs

        widget = QWidget()

        menu = QMenu()
        fixed_value_action = QAction(self.tr('Fixed value'), menu)
        fixed_value_action.triggered.connect(self.on_fixedValue)
        menu.addAction(fixed_value_action)

        menu.addSection(self.tr("Model inputs"))
        for text, value in inputs:
            model_value_action = QAction(text, menu)
            model_value_action.setData(value)
            model_value_action.triggered.connect(self.on_modelValue)
            menu.addAction(model_value_action)

        menu.addSection(self.tr("Algorithms outputs"))
        for text, value in outputs:
            model_value_action = QAction(text, menu)
            model_value_action.setData(value)
            model_value_action.triggered.connect(self.on_modelValue)
            menu.addAction(model_value_action)

        self.mIconDataDefine = QgsApplication.getThemeIcon("/mIconDataDefine.svg")
        self.mIconDataDefineOn = QgsApplication.getThemeIcon("/mIconDataDefineOn.svg")

        button = QToolButton()
        button.setIcon(self.mIconDataDefine)
        button.setPopupMode(QToolButton.InstantPopup)
        button.setMenu(menu)
        self.button = button

        label = QLabel()
        label.hide()
        self.label = label

        layout = QHBoxLayout()
        layout.addWidget(button, 0)
        layout.addWidget(label, 1)
        layout.addWidget(base_wrapper.widget, 1)
        widget.setLayout(layout)
        return widget

    def on_fixedValue(self):
        self.button.setIcon(self.mIconDataDefine)
        self.label.hide()
        self.base_wrapper.widget.show()

    def on_modelValue(self):
        action = self.sender()
        self.setValue(action.data())

    def setValue(self, value):
        for text, val in self.model_values:
            if val == value:
                self.model_value = value
                self.button.setIcon(self.mIconDataDefineOn)
                self.label.setText(text)
                self.label.show()
                self.base_wrapper.widget.hide()
                return
        self.base_wrapper.setValue(value)
        self.on_fixedValue()

    def value(self):
        if self.label.isVisible():
            return self.model_value
        else:
            return self.base_wrapper.value()


class ModelerParametersDialog(QDialog):

    ENTER_NAME = '[Enter name if this is a final result]'
    NOT_SELECTED = '[Not selected]'
    USE_MIN_COVERING_EXTENT = '[Use min covering extent]'

    def __init__(self, alg, model, algName=None):
        QDialog.__init__(self)
        self.setModal(True)
        # The algorithm to define in this dialog. It is an instance of GeoAlgorithm
        self._alg = alg
        # The resulting algorithm after the user clicks on OK. it is an instance of the container Algorithm class
        self.alg = None
        # The model this algorithm is going to be added to
        self.model = model
        # The name of the algorithm in the model, in case we are editing it and not defining it for the first time
        self._algName = algName
        self.setupUi()
        self.params = None

    def setupUi(self):
        self.labels = {}
        self.widgets = {}
        self.checkBoxes = {}
        self.showAdvanced = False
        self.wrappers = {}
        self.valueItems = {}
        self.dependentItems = {}
        self.resize(650, 450)
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel
                                          | QDialogButtonBox.Ok)
        tooltips = self._alg.getParameterDescriptions()
        self.setSizePolicy(QSizePolicy.Expanding,
                           QSizePolicy.Expanding)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setMargin(20)

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.verticalLayout.addWidget(self.bar)

        hLayout = QHBoxLayout()
        hLayout.setSpacing(5)
        hLayout.setMargin(0)
        descriptionLabel = QLabel(self.tr("Description"))
        self.descriptionBox = QLineEdit()
        self.descriptionBox.setText(self._alg.name)
        hLayout.addWidget(descriptionLabel)
        hLayout.addWidget(self.descriptionBox)
        self.verticalLayout.addLayout(hLayout)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(line)

        for param in self._alg.parameters:
            if param.isAdvanced:
                self.advancedButton = QPushButton()
                self.advancedButton.setText(self.tr('Show advanced parameters'))
                self.advancedButton.clicked.connect(
                    self.showAdvancedParametersClicked)
                advancedButtonHLayout = QHBoxLayout()
                advancedButtonHLayout.addWidget(self.advancedButton)
                advancedButtonHLayout.addStretch()
                self.verticalLayout.addLayout(advancedButtonHLayout)
                break
        for param in self._alg.parameters:
            if param.hidden:
                continue
            desc = param.description
            if isinstance(param, ParameterExtent):
                desc += self.tr('(xmin, xmax, ymin, ymax)')
            if isinstance(param, ParameterPoint):
                desc += self.tr('(x, y)')
            if param.optional:
                desc += self.tr(' [optional]')
            label = QLabel(desc)
            self.labels[param.name] = label

            base_wrapper = param.wrapper(self)
            compatibleInputs = [(self.resolveValueDescription(s), s) for s in
                                self.getAvailableInputs(base_wrapper)]
            compatibleOuputs = [(self.resolveValueDescription(s), s) for s in
                                self.getAvailableOutputs(base_wrapper)]
            wrapper = ModelerWidgetWrapper(param,
                                           self,
                                           base_wrapper=base_wrapper,
                                           inputs=compatibleInputs,
                                           outputs=compatibleOuputs)
            self.wrappers[param.name] = wrapper

            widget = wrapper.widget
            if widget is not None:
                self.valueItems[param.name] = widget
                if param.name in list(tooltips.keys()):
                    tooltip = tooltips[param.name]
                else:
                    tooltip = param.description
                label.setToolTip(tooltip)
                widget.setToolTip(tooltip)
                if param.isAdvanced:
                    label.setVisible(self.showAdvanced)
                    widget.setVisible(self.showAdvanced)
                    self.widgets[param.name] = widget

                self.verticalLayout.addWidget(label)
                self.verticalLayout.addWidget(widget)

        for output in self._alg.outputs:
            if output.hidden:
                continue
            if isinstance(output, (OutputRaster, OutputVector, OutputTable,
                                   OutputHTML, OutputFile, OutputDirectory)):
                label = QLabel(output.description + '<'
                               + output.__class__.__name__ + '>')
                item = QLineEdit()
                if hasattr(item, 'setPlaceholderText'):
                    item.setPlaceholderText(ModelerParametersDialog.ENTER_NAME)
                self.verticalLayout.addWidget(label)
                self.verticalLayout.addWidget(item)
                self.valueItems[output.name] = item

        label = QLabel(' ')
        self.verticalLayout.addWidget(label)
        label = QLabel(self.tr('Parent algorithms'))
        self.dependenciesPanel = self.getDependenciesPanel()
        self.verticalLayout.addWidget(label)
        self.verticalLayout.addWidget(self.dependenciesPanel)
        self.verticalLayout.addStretch(1000)

        self.setPreviousValues()
        self.setWindowTitle(self._alg.name)
        self.verticalLayout2 = QVBoxLayout()
        self.verticalLayout2.setSpacing(2)
        self.verticalLayout2.setMargin(0)
        self.tabWidget = QTabWidget()
        self.tabWidget.setMinimumWidth(300)
        self.paramPanel = QWidget()
        self.paramPanel.setLayout(self.verticalLayout)
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.paramPanel)
        self.scrollArea.setWidgetResizable(True)
        self.tabWidget.addTab(self.scrollArea, self.tr('Parameters'))

        self.txtHelp = QTextBrowser()

        html = None
        isText, algHelp = self._alg.help()
        if algHelp is not None:
            algHelp = algHelp if isText else QUrl(algHelp)
            try:
                if isText:
                    self.txtHelp.setHtml(algHelp)
                else:
                    html = self.tr('<p>Downloading algorithm help... Please wait.</p>')
                    self.txtHelp.setHtml(html)
                    self.tabWidget.addTab(self.txtHelp, 'Help')
                    self.reply = QgsNetworkAccessManager.instance().get(QNetworkRequest(algHelp))
                    self.reply.finished.connect(self.requestFinished)
            except:
                pass

        self.verticalLayout2.addWidget(self.tabWidget)
        self.verticalLayout2.addWidget(self.buttonBox)
        self.setLayout(self.verticalLayout2)
        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)
        QMetaObject.connectSlotsByName(self)

        for wrapper in list(self.wrappers.values()):
            wrapper.postInitialize(list(self.wrappers.values()))

    def requestFinished(self):
        """Change the webview HTML content"""
        reply = self.sender()
        if reply.error() != QNetworkReply.NoError:
            html = self.tr('<h2>No help available for this algorithm</h2><p>{}</p>'.format(reply.errorString()))
        else:
            html = str(reply.readAll())
        reply.deleteLater()
        self.txtHelp.setHtml(html)

    def getAvailableDependencies(self):  # spellok
        if self._algName is None:
            dependent = []
        else:
            dependent = self.model.getDependentAlgorithms(self._algName)
        opts = []
        for alg in list(self.model.algs.values()):
            if alg.name not in dependent:
                opts.append(alg)
        return opts

    def getDependenciesPanel(self):
        return MultipleInputPanel([alg.description for alg in self.getAvailableDependencies()])  # spellok

    def showAdvancedParametersClicked(self):
        self.showAdvanced = not self.showAdvanced
        if self.showAdvanced:
            self.advancedButton.setText(self.tr('Hide advanced parameters'))
        else:
            self.advancedButton.setText(self.tr('Show advanced parameters'))
        for param in self._alg.parameters:
            if param.isAdvanced:
                self.labels[param.name].setVisible(self.showAdvanced)
                self.widgets[param.name].setVisible(self.showAdvanced)

    def getAvailableInputs(self, base_wrapper):
        paramTypes = base_wrapper.compatibleParameterTypes()
        dataTypes = base_wrapper.compatibleDataTypes()

        values = []
        for i in self.model.inputs.values():
            param = i.param
            if not isinstance(param, tuple(paramTypes)):
                continue
            if dataTypes and not param.datatype in dataTypes:
                continue
            values.append(ValueFromInput(param.name))
        return values

    def getAvailableOutputs(self, base_wrapper):
        outTypes = base_wrapper.compatibleOutputTypes()
        dataTypes = base_wrapper.compatibleDataTypes()

        values = []
        if not outTypes:
            return values
        if self._algName is None:
            dependent = []
        else:
            dependent = self.model.getDependentAlgorithms(self._algName)
        for alg in list(self.model.algs.values()):
            if alg.name in dependent:
                continue
            for out in alg.algorithm.outputs:
                if not isinstance(out, tuple(outTypes)):
                    continue
                if dataTypes and not out.datatype in dataTypes:
                    continue
                values.append(ValueFromOutput(alg.name, out.name))
        return values

    def getAvailableValuesOfType(self, paramType, outType=None, dataType=None):
        return []

    def resolveValueDescription(self, value):
        if isinstance(value, ValueFromInput):
            return self.model.inputs[value.name].param.description
        else:
            alg = self.model.algs[value.alg]
            return self.tr("'%s' from algorithm '%s'") % (alg.algorithm.getOutputFromName(value.output).description, alg.description)

    def setPreviousValues(self):
        if self._algName is not None:
            alg = self.model.algs[self._algName]
            self.descriptionBox.setText(alg.description)
            for param in alg.algorithm.parameters:
                if param.hidden:
                    continue
                if param.name in alg.params:
                    value = alg.params[param.name]
                else:
                    value = param.default
                self.wrappers[param.name].setValue(value)
            for name, out in list(alg.outputs.items()):
                self.valueItems[name].setText(out.description)

            selected = []
            dependencies = self.getAvailableDependencies()  # spellok
            for idx, dependency in enumerate(dependencies):
                if dependency.name in alg.dependencies:
                    selected.append(idx)

            self.dependenciesPanel.setSelectedItems(selected)

    def createAlgorithm(self):
        alg = Algorithm(self._alg.commandLineName())
        alg.setName(self.model)
        alg.description = self.descriptionBox.text()
        params = self._alg.parameters
        outputs = self._alg.outputs
        for param in params:
            if param.hidden:
                continue
            if not self.setParamValue(alg, param, self.wrappers[param.name]):
                self.bar.pushMessage("Error", "Wrong or missing value for parameter '%s'" % param.description,
                                     level=QgsMessageBar.WARNING)
                return None
        for output in outputs:
            if not output.hidden:
                name = str(self.valueItems[output.name].text())
                if name.strip() != '' and name != ModelerParametersDialog.ENTER_NAME:
                    alg.outputs[output.name] = ModelerOutput(name)

        selectedOptions = self.dependenciesPanel.selectedoptions
        availableDependencies = self.getAvailableDependencies()  # spellok
        for selected in selectedOptions:
            alg.dependencies.append(availableDependencies[selected].name)  # spellok

        self._alg.processBeforeAddingToModeler(alg, self.model)
        return alg

    def setParamValue(self, alg, param, wrapper):
        try:
            if wrapper.widget:
                value = wrapper.value()
                alg.params[param.name] = value
            return True
        except InvalidParameterValue:
            return False

    def okPressed(self):
        self.alg = self.createAlgorithm()
        if self.alg is not None:
            self.close()

    def cancelPressed(self):
        self.alg = None
        self.close()
