from django.test import TestCase
import tempfile
import os
from .utils import extract_text_from_file


class UtilsTests(TestCase):
    def test_extract_text_from_plain_text_file(self):
        # create a temporary text file and ensure extraction returns content
        fd, path = tempfile.mkstemp(suffix='.txt')
        try:
            os.write(fd, b'Hello Engauge')
            os.close(fd)
            txt = extract_text_from_file(path)
            self.assertIn('Hello Engauge', txt)
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass
