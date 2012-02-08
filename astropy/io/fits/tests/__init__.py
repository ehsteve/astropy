# Licensed under a 3-clause BSD style license - see PYFITS.rst

import os
import shutil
import tempfile


class FitsTestCase(object):
    def setup(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.temp_dir = tempfile.mkdtemp(prefix='fits-test-')

    def teardown(self):
        shutil.rmtree(self.temp_dir)

    def data(self, filename):
        return os.path.join(self.data_dir, filename)

    def temp(self, filename):
        return os.path.join(self.temp_dir, filename)