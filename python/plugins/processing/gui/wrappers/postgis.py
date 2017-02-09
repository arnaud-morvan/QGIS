# -*- coding: utf-8 -*-

"""
***************************************************************************
    postgis.py - Postgis widget wrappers
    ---------------------
    Date                 : December 2016
    Copyright            : (C) 2016 by Arnaud Morvan
    Email                : arnaud dot morvan at camptocamp dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""


from qgis.PyQt.QtCore import QSettings, QAbstractListModel
from qgis.PyQt.QtWidgets import QComboBox

from processing.core.parameters import (
    ParameterString,
    ParameterNumber,
    ParameterFile,
    ParameterTableField,
    ParameterExpression
    )
from processing.core.outputs import OutputString
from processing.gui.wrappers import WidgetWrapper, DIALOG_MODELER
from processing.tools.postgis import GeoDB


from qgis.core import QgsMessageLog


class ConnectionWidgetWrapper(WidgetWrapper):
    """
    WidgetWrapper for ParameterString that create and manage a combobox widget
    with existing postgis connections.
    """

    def createWidget(self):
        widget = QComboBox()
        for group in self.items():
            widget.addItem(*group)
        widget.currentIndexChanged.connect(lambda: self.widgetValueHasChanged.emit(self))
        return widget

    def items(self):
        settings = QSettings()
        settings.beginGroup('/PostgreSQL/connections/')
        items = [(group, group) for group in settings.childGroups()]

        if self.dialogType == DIALOG_MODELER:
            strings = self.dialog.getAvailableValuesOfType(
                [ParameterString, ParameterNumber, ParameterFile,
                 ParameterTableField, ParameterExpression], OutputString)
            items = items + [(self.dialog.resolveValueDescription(s), s) for s in strings]

        return items

    def setValue(self, value):
        self.setComboValue(value)

    def value(self):
        return self.comboValue()


class SchemaWidgetWrapper(WidgetWrapper):
    """
    WidgetWrapper for ParameterString that create and manage a combobox widget
    with existing schemas from a parent connection parameter.
    """

    def createWidget(self, connection_param=None):
        self._connection_param = connection_param
        self._connection = None
        self._database = None

        widget = QComboBox()
        widget.setEditable(True)
        self.widget = widget
        self.refreshItems()
        widget.currentIndexChanged.connect(lambda: self.widgetValueHasChanged.emit(self))
        widget.lineEdit().editingFinished.connect(lambda: self.widgetValueHasChanged.emit(self))
        return widget

    def postInitialize(self, wrappers):
        for wrapper in wrappers:
            if wrapper.param.name == self._connection_param:
                self.connection_wrapper = wrapper
                self.setConnection(wrapper.value())
                wrapper.widgetValueHasChanged.connect(self.connectionChanged)
                break

    def connectionChanged(self, wrapper):
        connection = wrapper.value()
        if connection == self._connection:
            return
        self.setConnection(connection)

    def setConnection(self, connection):
        self._connection = connection
        if isinstance(connection, str):
            self._database = GeoDB.from_name(connection)
        else:
            self._database = None
        self.refreshItems()
        self.widgetValueHasChanged.emit(self)

    def refreshItems(self):
        value = self.comboValue()

        self.widget.clear()

        if self._database is not None:
            for schema in [s[1] for s in self._database.list_schemas()]:
                self.widget.addItem(schema, schema)

        if self.dialogType == DIALOG_MODELER:
            strings = self.dialog.getAvailableValuesOfType(
                [ParameterString, ParameterNumber, ParameterFile,
                 ParameterTableField, ParameterExpression], OutputString)
            for text, data in [(self.dialog.resolveValueDescription(s), s) for s in strings]:
                self.widget.addItem(text, data)

        self.setComboValue(value)

    def setValue(self, value):
        self.setComboValue(value)
        #self.widget.setCurrentText(value)
        self.widgetValueHasChanged.emit(self)

    def value(self):
        return self.comboValue()

    def database(self):
        return self._database


class TableWidgetWrapper(WidgetWrapper):
    """
    WidgetWrapper for ParameterString that create and manage a combobox widget
    with existing tables from a parent schema parameter.
    """

    def createWidget(self, schema_param=None):
        self._schema_param = schema_param
        self._database = None
        self._schema = None

        widget = QComboBox()
        widget.setEditable(True)
        self.widget = widget
        self.refreshItems()
        widget.currentIndexChanged.connect(lambda: self.widgetValueHasChanged.emit(self))
        widget.lineEdit().editingFinished.connect(lambda: self.widgetValueHasChanged.emit(self))
        return widget

    def postInitialize(self, wrappers):
        for wrapper in wrappers:
            if wrapper.param.name == self._schema_param:
                self.schema_wrapper = wrapper
                self.setSchema(wrapper.database(), wrapper.value())
                wrapper.widgetValueHasChanged.connect(self.schemaChanged)
                break

    def schemaChanged(self, wrapper):
        database = wrapper.database()
        schema = wrapper.value()
        if database == self._database and schema == self._schema:
            return
        self.setSchema(database, schema)

    def setSchema(self, database, schema):
        self._database = database
        self._schema = schema
        self.refreshItems()
        self.widgetValueHasChanged.emit(self)

    def refreshItems(self):
        value = self.comboValue()

        self.widget.clear()

        if (self._database is not None
            and isinstance(self._schema, str)):
            for table in self._database.list_geotables(self._schema):
                self.widget.addItem(table[0])

        if self.dialogType == DIALOG_MODELER:
            strings = self.dialog.getAvailableValuesOfType(
                [ParameterString, ParameterNumber, ParameterFile,
                 ParameterTableField, ParameterExpression], OutputString)
            for text, data in [(self.dialog.resolveValueDescription(s), s) for s in strings]:
                self.widget.addItem(text, data)

        self.setComboValue(value)

    def setValue(self, value):
        self.setComboValue(value)
        self.widgetValueHasChanged.emit(self)

    def value(self):
        return self.comboValue()
