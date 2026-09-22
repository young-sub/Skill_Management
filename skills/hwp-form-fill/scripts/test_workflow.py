"""Run with the same Python used for doctor.py; never starts Hancom."""
import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import convert_and_validate as cv
from hwpx import HwpxDocument


class WorkflowTest(unittest.TestCase):
    def test_optional_failure_and_required_preserve_hwpx(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.hwpx"
            with HwpxDocument.new() as doc:
                doc.add_paragraph("검증용 값")
                doc.save_to_path(source)
            before = cv.sha256(source)
            for available, reason in [(False, "Windows unavailable"), (True, "")]:
                with patch.object(cv, "hwp_environment", return_value=(available, reason)), \
                     patch.object(cv, "run_conversion", return_value={"status": "SKIP", "reason": "SaveAs failed"}):
                    for mode, code in [("auto", 0), ("off", 0), ("required", 1)]:
                        with contextlib.redirect_stdout(io.StringIO()) as output:
                            actual = cv.main([str(source), "--hwp", mode, "--expect", "검증용 값"])
                        self.assertEqual(actual, code)
                        self.assertIn("SKIP", output.getvalue())
            self.assertEqual(before, cv.sha256(source))
            self.assertFalse(list(Path(tmp).glob("*.hwp")))
            with patch.object(cv.sys, "platform", "linux"), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(cv.main([str(source), "--format", "json"]), 0)
                self.assertEqual(json.loads(output.getvalue())["hwp"]["reason"], "Windows가 아님")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cv.main([str(source), "--hwp", "off", "--expect", "absent"]), 1)
                self.assertEqual(cv.main([str(source), "--hwp", "off", "--forbid", "검증용 값"]), 1)

    def test_fake_hwp_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.hwpx"
            with HwpxDocument.new() as doc:
                doc.add_paragraph("검사")
                doc.save_to_path(source)
            app = Mock()

            def save_as(path, *_):
                Path(path).write_bytes(source.read_bytes())  # Deliberately fake HWP ZIP.
                return True

            app.SaveAs.side_effect = save_as
            win32 = types.ModuleType("win32com")
            client = types.ModuleType("win32com.client")
            client.DispatchEx = Mock(return_value=app)
            win32.client = client
            pythoncom = Mock()

            def worker(command, **_):
                cv._worker(Path(command[3]), Path(command[4]), False)

            with patch.dict(sys.modules, {"win32com": win32, "win32com.client": client, "pythoncom": pythoncom}), \
                 patch.object(cv.subprocess, "run", side_effect=worker):
                result = cv.run_conversion(source, root / "out")
            self.assertEqual(result["status"], "SKIP")
            self.assertIn("OLE", result["reason"])
            self.assertFalse(list((root / "out").iterdir()))
            app.Quit.assert_called_once()
            client.DispatchEx.assert_called_once_with("HWPFrame.HwpObject")


if __name__ == "__main__":
    unittest.main()
