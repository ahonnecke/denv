"""Tests for the CLI module."""

import io
import sys
from denv.cli import main
from denv.redactor import process_stream


class TestCLI:
    """Tests for CLI functionality."""

    def test_process_stream_basic(self):
        """Test basic stream processing."""
        input_data = "API_KEY=secret123\nDEBUG=true\n"
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "values", "REDACTED", False, False)

        result = out.getvalue()
        assert "API_KEY=REDACTED" in result
        assert "DEBUG=REDACTED" in result

    def test_process_stream_with_comments(self):
        """Test stream processing with comments."""
        input_data = "# Configuration\nAPI_KEY=secret\n# End\n"
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "values", "REDACTED", False, False)

        result = out.getvalue()
        assert "# Configuration" in result
        assert "API_KEY=REDACTED" in result
        assert "# End" in result

    def test_process_stream_keep_length(self):
        """Test stream processing with length preservation."""
        input_data = "PASSWORD=secret123\n"
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "values", "REDACTED", True, False)

        result = out.getvalue()
        assert "PASSWORD=**********" in result

    def test_process_stream_strip_secrets(self):
        """Test stream processing with secret stripping."""
        input_data = "API_KEY=secret\nDEBUG=true\nPASSWORD=pass\n"
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "values", "REDACTED", False, True)

        result = out.getvalue()
        assert "API_KEY" not in result
        assert "PASSWORD" not in result
        assert "DEBUG=REDACTED" in result

    def test_process_stream_redact_keys(self):
        """Test stream processing with key redaction."""
        input_data = "DATABASE_URL=postgresql://localhost/db\n"
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "keys", "REDACTED", False, False)

        result = out.getvalue()
        assert "VAR_" in result
        assert "postgresql://localhost/db" in result

    def test_process_stream_redact_both(self):
        """Test stream processing with both key and value redaction."""
        input_data = "API_KEY=secret123\n"
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "both", "REDACTED", False, False)

        result = out.getvalue()
        assert "VAR_" in result
        assert "REDACTED" in result
        assert "API_KEY" not in result
        assert "secret123" not in result

    def test_process_stream_quoted_values(self):
        """Test stream processing with quoted values."""
        input_data = 'API_KEY="secret123"\nTOKEN=\'token456\'\n'
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "values", "REDACTED", False, False)

        result = out.getvalue()
        assert 'API_KEY="REDACTED"' in result
        assert "TOKEN='REDACTED'" in result

    def test_process_stream_export_statements(self):
        """Test stream processing with export statements."""
        input_data = "export API_KEY=secret\nexport DEBUG=true\n"
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "values", "REDACTED", False, False)

        result = out.getvalue()
        assert "export API_KEY=REDACTED" in result
        assert "export DEBUG=REDACTED" in result

    def test_process_stream_inline_comments(self):
        """Test stream processing with inline comments."""
        input_data = "API_KEY=secret # Production key\nDEBUG=true # Enable debug\n"
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "values", "REDACTED", False, False)

        result = out.getvalue()
        assert "API_KEY=REDACTED # Production key" in result
        assert "DEBUG=REDACTED # Enable debug" in result

    def test_process_stream_custom_placeholder(self):
        """Test stream processing with custom placeholder."""
        input_data = "API_KEY=secret\n"
        inp = io.StringIO(input_data)
        out = io.StringIO()

        process_stream(inp, out, "values", "***HIDDEN***", False, False)

        result = out.getvalue()
        assert "API_KEY=***HIDDEN***" in result
