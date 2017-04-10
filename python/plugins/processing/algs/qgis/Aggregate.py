# -*- coding: utf-8 -*-

"""
***************************************************************************
    Aggregate.py
    ---------------------
    Date                 : February 2017
    Copyright            : (C) 2017 by Arnaud Morvan
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

__author__ = 'Arnaud Morvan'
__date__ = 'February 2017'
__copyright__ = '(C) 2017, Arnaud Morvan'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import (
    QgsApplication,
    QgsDistanceArea,
    QgsExpression,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsProject,
    QgsWkbTypes,
)

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import (
    Parameter,
    ParameterBoolean,
    ParameterExpression,
    ParameterTable,
)
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter


class Aggregate(GeoAlgorithm):

    INPUT = 'INPUT'
    GROUP_BY = 'GROUP_BY'
    AGGREGATES = 'AGGREGATES'
    DISSOLVE = 'DISSOLVE'
    OUTPUT = 'OUTPUT'

    def icon(self):
        return QgsApplication.getThemeIcon("/providerQgis.svg")

    def svgIconPath(self):
        return QgsApplication.iconPath("providerQgis.svg")

    def group(self):
        return self.tr('Vector geometry tools')

    def name(self):
        return 'aggregate'

    def displayName(self):
        return self.tr('Aggregate')

    def defineCharacteristics(self):
        self.addParameter(ParameterTable(self.INPUT,
                                         self.tr('Input layer')))
        self.addParameter(ParameterExpression(self.GROUP_BY,
                                              self.tr('Group by expression (NULL to group all features)'),
                                              default='NULL',
                                              optional=False,
                                              parent_layer=self.INPUT))

        class ParameterAggregates(Parameter):

            default_metadata = {
                'widget_wrapper': 'processing.algs.qgis.ui.AggregatesPanel.AggregatesWidgetWrapper'
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

        self.addParameter(ParameterAggregates(self.AGGREGATES,
                                              self.tr('Aggregates'),
                                              self.INPUT))
        self.addOutput(OutputVector(self.OUTPUT,
                                    self.tr('Aggregated'),
                                    base_input=self.INPUT))

    def processAlgorithm(self, feedback):
        layer = self.getParameterValue(self.INPUT)
        group_by = self.getParameterValue(self.GROUP_BY)
        aggregates = self.getParameterValue(self.AGGREGATES)
        dissolve = self.getParameterValue(self.DISSOLVE)
        output = self.getOutputFromName(self.OUTPUT)

        layer = dataobjects.getLayerFromString(layer)

        self.da = QgsDistanceArea()
        self.da.setSourceCrs(layer.crs())
        self.da.setEllipsoidalMode(True)
        self.da.setEllipsoid(QgsProject.instance().ellipsoid())
        self.exp_context = layer.createExpressionContext()

        group_by_expr = self.createExpression(group_by)

        geometry_expr = self.createExpression('collect($geometry, {})'
                                              .format(group_by))

        fields = []
        fields_expr = []
        for field_def in aggregates:
            fields.append(QgsField(name=field_def['name'],
                                   type=field_def['type'],
                                   len=field_def['length'],
                                   prec=field_def['precision']))
            aggregate = field_def['aggregate']
            if aggregate == 'first_value':
                expression = field_def['input']
            elif aggregate == 'concatenate':
                expression = ('{}({}, {}, {}, \'{}\')'
                              .format(field_def['aggregate'],
                                      field_def['input'],
                                      group_by,
                                      'TRUE',
                                      field_def['delimiter']))
            else:
                expression = '{}({}, {})'.format(field_def['aggregate'],
                                                 field_def['input'],
                                                 group_by)
            expr = self.createExpression(expression)
            fields_expr.append(expr)

        writer = output.getVectorWriter(
            fields,
            QgsWkbTypes.multiType(layer.wkbType()),
            layer.crs())

        # Group features in memory layers
        feature = QgsFeature()
        features = vector.features(layer)
        if len(features):
            progress_step = 50.0 / len(features)
        current = 0
        groups = {}
        keys = []  # We need deterministic order for the tests
        for feature in features:
            self.exp_context.setFeature(feature)
            group_by_value = self.evaluateExpression(group_by_expr)

            # Get an hashable key for the dict
            key = group_by_value
            if isinstance(key, list):
                key = tuple(key)

            group = groups.get(key, None)
            if group is None:
                keys.append(key)
                group = VectorWriter('memory:',
                                     None,
                                     layer.fields(),
                                     layer.wkbType(),
                                     layer.crs(),
                                     options=None)
                group.feature = feature
                groups[key] = group

            group.addFeature(feature)

            current += 1
            feedback.setProgress(int(current * progress_step))

        # Calculate aggregates on memory layers
        if len(keys):
            progress_step = 50.0 / len(keys)
        for current, key in enumerate(keys):
            group = groups[key]
            self.exp_context = group.layer.createExpressionContext()
            self.exp_context.setFeature(group.feature)

            geometry = self.evaluateExpression(geometry_expr)
            if geometry is not None and not geometry.isEmpty():
                geometry = QgsGeometry.unaryUnion(geometry.asGeometryCollection())
                if geometry.isEmpty():
                    raise GeoAlgorithmExecutionException(
                        'Impossible to combine geometries for {} = {}'
                        .format(group_by, group_by_value))

            attrs = []
            for i in range(0, len(aggregates)):
                field_def = aggregates[i]
                expr = fields_expr[i]
                value = self.evaluateExpression(expr)
                attrs.append(value)

            # Write output feature
            outFeat = QgsFeature()
            if geometry is not None:
                outFeat.setGeometry(geometry)
            outFeat.setAttributes(attrs)
            writer.addFeature(outFeat)

            feedback.setProgress(50 + int(current * progress_step))

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
                .format(text, expr.parserErrorString()))
        return expr

    def evaluateExpression(self, expr):
        value = expr.evaluate(self.exp_context)
        if expr.hasEvalError():
            raise GeoAlgorithmExecutionException(
                self.tr(u'Evaluation error in expression "{}": {}')
                .format(expr.expression(), expr.evalErrorString()))
        return value
