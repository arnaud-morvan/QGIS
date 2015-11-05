# -*- coding: utf-8 -*-

import sys
import os
import unittest

algs_tests_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(algs_tests_path)

# Take care to initialize sip before some PyQt4 imports
from qgis_init import getQgisTestApp
QGISAPP = getQgisTestApp()
'''
Here we have to execute getQgisTestApp before importing processing package
This qgis_init module should be moved outside of the processing package,
in qgis core python utils for example.

For most algorithm testing cases, we don't need an iface.
'''

core_plugins_path = os.path.join(algs_tests_path, '..', '..','..')
sys.path.append(core_plugins_path)
from processing.core.Processing import Processing
from processing.tools.general import runalg
Processing.initialize()


data_path = os.path.abspath(
    os.path.join(algs_tests_path, 'data'))


class ExtractByAttributeTest(unittest.TestCase):
    """Test suite for ExtractByLocation algorithm."""

    def test_extract(self):
        '''Extract feature from layer by attribute'''

        from qgis.core import QgsVectorLayer
        layer = os.path.join(data_path, 'DEPARTEMENT.SHP')
        result = runalg('qgis:extractbyattribute', layer, 'CODE_DEPT', 0, '22', None)

        result_layer = QgsVectorLayer(result['OUTPUT'], 'output', 'ogr')
        if not result_layer.isValid():
            self.fail('Impossible to load output layer')
        else:
            self.assertEqual(result_layer.featureCount(), 1, 'Result should contain 1 feature')


if __name__ == "__main__":
    unittest.main()
