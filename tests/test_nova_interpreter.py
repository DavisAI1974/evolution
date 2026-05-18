import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from nova_interpreter import NovaInterpreter


class NovaInterpreterTests(unittest.TestCase):
    def run_script(self, script: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "script.nv"
            path.write_text(script, encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                NovaInterpreter().run_file(str(path))
            return output.getvalue()

    def test_assignment_loop_and_if(self):
        output = self.run_script(
            """
let name = "evolution"
let stages = ["observe", "verify"]
print(name)
for stage in stages {
    print(stage)
}
if len(stages) == 2 {
    print("ready")
}
"""
        )

        self.assertIn("evolution", output)
        self.assertIn("observe", output)
        self.assertIn("verify", output)
        self.assertIn("ready", output)

    def test_multiline_expression(self):
        output = self.run_script(
            """
let total = sum([
    1,
    2,
    3
])
print(str(total))
"""
        )

        self.assertEqual(output.strip(), "6")

    def test_stdlib_namespace(self):
        output = self.run_script(
            """
let raw = "  Nova  "
print(stdlib.lower(stdlib.trim(raw)))
"""
        )

        self.assertEqual(output.strip(), "nova")


if __name__ == "__main__":
    unittest.main()
