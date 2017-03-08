# -*- coding: utf-8 -*-

"""
***************************************************************************
    FieldsMapper.py
    ---------------------
    Date                 : October 2014
    Copyright            : (C) 2014 by Arnaud Morvan
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
from __future__ import print_function
from builtins import str
from builtins import range

__author__ = 'Arnaud Morvan'
__date__ = 'October 2014'
__copyright__ = '(C) 2014, Arnaud Morvan'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import (QgsField,
                       QgsExpression,
                       QgsDistanceArea,
                       QgsProject,
                       QgsFeature,
                       QgsApplication)

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import (
    Parameter,
    ParameterTable,
)
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector


class FieldsMapper(GeoAlgorithm):

    INPUT_LAYER = 'INPUT_LAYER'
    FIELDS_MAPPING = 'FIELDS_MAPPING'
    OUTPUT_LAYER = 'OUTPUT_LAYER'

    def icon(self):
        return QgsApplication.getThemeIcon("/providerQgis.svg")

    def svgIconPath(self):
        return QgsApplication.iconPath("providerQgis.svg")

    def group(self):
        return self.tr('Vector table tools')

    def name(self):
        return 'refactorfields'

    def displayName(self):
        return self.tr('Refactor fields')

    def defineCharacteristics(self):
        self.addParameter(ParameterTable(self.INPUT_LAYER,
                                         self.tr('Input layer'),
                                         False))

        class ParameterFieldsMapping(Parameter):

            default_metadata = {
                'widget_wrapper': 'processing.algs.qgis.ui.FieldsMappingPanel.FieldsMappingWidgetWrapper'
            }

            def __init__(self, name='', description='', parent=None):
                Parameter.__init__(self, name, description)
                self.parent = parent
                self.value = []

            def getValueAsCommandLineParameter(self):
                return '"' + str(self.value) + '"'

            def setValue(self, value):
                if value is None:
                    return False
                if isinstance(value, list):
                    self.value = value
                    return True
                if isinstance(value, str):
                    try:
                        self.value = eval(value)
                        return True
                    except Exception as e:
                        # fix_print_with_import
                        print(str(e))  # display error in console
                        return False
                return False

        self.addParameter(ParameterFieldsMapping(self.FIELDS_MAPPING,
                                                 self.tr('Fields mapping'),
                                                 self.INPUT_LAYER))
        self.addOutput(OutputVector(self.OUTPUT_LAYER,
                                    self.tr('Refactored'),
                                    base_input=self.INPUT_LAYER))

    def processAlgorithm(self, feedback):
        layer = self.getParameterValue(self.INPUT_LAYER)
        mapping = self.getParameterValue(self.FIELDS_MAPPING)
        output = self.getOutputFromName(self.OUTPUT_LAYER)

        layer = dataobjects.getLayerFromString(layer)

        self.da = QgsDistanceArea()
        self.da.setSourceCrs(layer.crs())
        self.da.setEllipsoidalMode(True)
        self.da.setEllipsoid(QgsProject.instance().ellipsoid())

        self.exp_context = layer.createExpressionContext()

        fields = []
        fields_expr = []
        for field_def in mapping:
            fields.append(QgsField(name=field_def['name'],
                                   type=field_def['type'],
                                   len=field_def['length'],
                                   prec=field_def['precision']))
            expression = field_def['expression']
            expr = self.createExpression(expression)
            fields_expr.append(expr)

        writer = output.getVectorWriter(fields,
                                        layer.wkbType(),
                                        layer.crs())

        feature = QgsFeature()
        features = vector.features(layer)

        if len(features):
            progress_step = 100.0 / len(features)
        for current, feature in enumerate(features):
            self.exp_context.setFeature(feature)
            self.exp_context.lastScope().setVariable("row_number", current + 1)

            geometry = feature.geometry()

            attrs = []
            for i in range(0, len(mapping)):
                field_def = mapping[i]
                expr = fields_expr[i]
                value = self.evaluateExpression(expr)
                attrs.append(value)

            outFeat = QgsFeature()
            outFeat.setGeometry(geometry)
            outFeat.setAttributes(attrs)
            writer.addFeature(outFeat)

            feedback.setProgress(int(current * progress_step))

        del writer

    def createExpression(self, text):
        expr = QgsExpression(text)
        expr.setGeomCalculator(self.da)
        expr.setDistanceUnits(QgsProject.instance().distanceUnits())
        expr.setAreaUnits(QgsProject.instance().areaUnits())
        expr.prepare(self.exp_context)
        if expr.hasParserError():
            raise GeoAlgorithmExecutionException(
                self.tr(u'Parser error in expression "{}": {}')
                .format(expr.expression(),
                        expr.parserErrorString()))
        return expr

    def evaluateExpression(self, expr):
        value = expr.evaluate(self.exp_context)
        if expr.hasEvalError():
            raise GeoAlgorithmExecutionException(
                self.tr(u'Evaluation error in expression "{}": {}')
                    .format(expr.expression(),
                            expr.parserErrorString()))
        return value
