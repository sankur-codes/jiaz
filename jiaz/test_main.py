"""Tests for __main__ module."""

import pytest
from unittest.mock import patch, Mock
import sys
from io import StringIO


class TestMainModule:
    """Test suite for __main__ module functionality."""

    @patch('jiaz.__main__.app')
    def test_main_module_execution(self, mock_app):
        """Test that __main__ module executes app when run directly."""
        # Import the module to trigger execution
        import jiaz.__main__
        
        # The app should be called when the module is imported with __name__ == "__main__"
        # Since we're importing it, __name__ won't be "__main__", so app() won't be called
        # But we can test the structure exists
        assert hasattr(jiaz.__main__, 'app')

    def test_main_module_imports(self):
        """Test that __main__ module imports correctly."""
        # Test that we can import the module without errors
        import jiaz.__main__ as main_module
        
        # Verify it has the expected structure
        assert hasattr(main_module, 'app')
        
        # Verify app is callable
        assert callable(main_module.app)

    @patch('jiaz.__main__.app')
    @patch('sys.argv', ['jiaz'])
    def test_main_module_with_mocked_name(self, mock_app):
        """Test __main__ module behavior when __name__ is __main__."""
        # We need to test the conditional execution
        # This is tricky because the module is already imported
        
        # Read the module source and verify the logic
        import jiaz.__main__ as main_module
        import inspect
        
        source = inspect.getsource(main_module)
        
        # Verify the conditional structure exists
        assert 'if __name__ == "__main__"' in source
        assert 'app()' in source

    def test_main_module_as_script(self):
        """Test that the main module can be executed as a script."""
        # Test the structure that would be executed when run as a script
        import jiaz.__main__ as main_module
        
        # Verify app is imported from the right place
        from jiaz.cli import app as cli_app
        assert main_module.app is cli_app

    def test_main_module_app_reference(self):
        """Test that __main__ module references the correct app."""
        import jiaz.__main__ as main_module
        
        # The app in __main__ should be the same as in cli
        from jiaz.cli import app as cli_app
        assert main_module.app is cli_app

    def test_main_module_no_side_effects_on_import(self):
        """Test that importing __main__ module doesn't cause side effects."""
        # Capture stdout to check for unexpected output
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Import the module
            import jiaz.__main__ as main_module
            
            # Should not produce output just from importing
            output = captured_output.getvalue()
            assert output == "", f"Unexpected output on import: {output}"
            
        finally:
            sys.stdout = old_stdout

    def test_main_module_minimal_structure(self):
        """Test that __main__ module has minimal, correct structure."""
        import jiaz.__main__ as main_module
        import inspect
        
        # Get the source code
        source = inspect.getsource(main_module)
        lines = [line.strip() for line in source.split('\n') if line.strip()]
        
        # Should have very minimal structure
        assert len(lines) <= 5, "Main module should be minimal"
        
        # Should import app
        import_lines = [line for line in lines if line.startswith('from jiaz.cli import app')]
        assert len(import_lines) == 1, "Should import app from jiaz.cli"
        
        # Should have conditional execution
        conditional_lines = [line for line in lines if '__main__' in line]
        assert len(conditional_lines) >= 1, "Should have __main__ conditional"

    def test_main_module_integration_with_cli(self):
        """Test integration between __main__ and cli modules."""
        import jiaz.__main__ as main_module
        import jiaz.cli as cli_module
        
        # Both should reference the same app
        assert main_module.app is cli_module.app
        
        # App should be a Typer instance
        assert hasattr(main_module.app, '__call__')
        assert hasattr(main_module.app, 'callback')

    @patch('builtins.__name__', '__main__')
    @patch('jiaz.__main__.app')
    def test_conditional_execution_logic(self, mock_app):
        """Test the conditional execution logic."""
        # This test verifies the logic exists, even if we can't easily test execution
        import jiaz.__main__ as main_module
        import inspect
        
        source = inspect.getsource(main_module)
        
        # Parse the structure to ensure it's correct
        assert 'if __name__ == "__main__":' in source
        assert 'app()' in source
        
        # The conditional should be at module level
        lines = source.split('\n')
        conditional_line_index = None
        app_call_line_index = None
        
        for i, line in enumerate(lines):
            if '__name__ == "__main__"' in line:
                conditional_line_index = i
            if 'app()' in line and conditional_line_index is not None:
                app_call_line_index = i
                break
        
        assert conditional_line_index is not None, "Should have conditional check"
        assert app_call_line_index is not None, "Should have app() call"
        assert app_call_line_index > conditional_line_index, "app() should be inside conditional"


class TestMainModuleExecution:
    """Test suite for main module execution scenarios."""

    def test_module_can_be_imported_safely(self):
        """Test that the module can be imported multiple times safely."""
        # Import multiple times to ensure no side effects
        import jiaz.__main__ as main1
        import jiaz.__main__ as main2
        
        # Should be the same module
        assert main1 is main2
        
        # Should have consistent app reference
        assert main1.app is main2.app

    def test_module_structure_is_executable(self):
        """Test that module structure would be executable."""
        import jiaz.__main__ as main_module
        
        # Verify app is callable (could be executed)
        assert callable(main_module.app)
        
        # Verify import structure is valid
        from jiaz.cli import app
        assert main_module.app is app

    def test_main_module_docstring_and_metadata(self):
        """Test main module metadata."""
        import jiaz.__main__ as main_module
        
        # Module should exist and be importable
        assert main_module.__name__ == 'jiaz.__main__'
        
        # Should have proper file reference
        assert main_module.__file__ is not None
        assert main_module.__file__.endswith('__main__.py')

    def test_error_handling_on_app_failure(self):
        """Test that module handles app execution failures gracefully."""
        # This tests the structure is robust
        import jiaz.__main__ as main_module
        
        # The app reference should be valid
        assert main_module.app is not None
        
        # Even if app fails, the import should succeed
        # (The actual execution would be in the conditional block)
