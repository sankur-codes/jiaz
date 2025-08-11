"""Tests for core config_utils module."""

import pytest
import tempfile
import configparser
from pathlib import Path
from unittest.mock import patch, mock_open, Mock, MagicMock
import base64
import typer

from jiaz.core.config_utils import (
    prepend_warning_to_config,
    validate_config,
    prompt_with_fallback,
    prompt_required_with_retries,
    prompt_api_key_with_retries,
    load_config,
    save_config,
    get_active_config,
    set_active_config,
    get_specific_config,
    encode_secure_value,
    decode_secure_value,
    validate_gemini_api_key,
    get_gemini_api_key,
    should_use_gemini,
    collect_required_fields,
    collect_optional_fields,
    handle_gemini_api_key_input
)


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as f:
        yield Path(f.name)
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    config = configparser.ConfigParser()
    config['default'] = {
        'server_url': 'https://test.jira.com',
        'user_token': encode_secure_value('test_token'),
        'jira_project': 'TEST'
    }
    config['meta'] = {
        'active_config': 'default'
    }
    return config


class TestConfigFileOperations:
    """Test suite for config file operations."""
    
    @patch('jiaz.core.config_utils.CONFIG_FILE')
    @patch('os.path.exists')
    def test_prepend_warning_to_config_file_exists(self, mock_exists, mock_config_file):
        """Test prepending warning to existing config file."""
        mock_exists.return_value = True
        mock_file_content = "existing content"
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)) as mock_file:
            prepend_warning_to_config()
            
            # Check that file was opened for read+write
            mock_file.assert_called_once()
            
            # Check that warning was written
            written_content = ''.join(call.args[0] for call in mock_file().write.call_args_list)
            assert "WARNING: Do not edit this config file manually" in written_content
            assert "existing content" in written_content
    
    @patch('jiaz.core.config_utils.CONFIG_FILE')
    @patch('os.path.exists')
    def test_prepend_warning_to_config_file_not_exists(self, mock_exists, mock_config_file):
        """Test prepending warning when config file doesn't exist."""
        mock_exists.return_value = False
        
        with patch('builtins.open', mock_open()) as mock_file:
            prepend_warning_to_config()
            
            # Should not try to open file if it doesn't exist
            mock_file.assert_not_called()
    
    def test_validate_config_removes_empty_values(self, mock_config):
        """Test that validate_config removes empty values."""
        # Add empty values to config
        mock_config['default']['empty_key'] = ''
        mock_config['default']['whitespace_key'] = '   '
        
        with patch('jiaz.core.config_utils.save_config') as mock_save:
            validate_config(mock_config)
            
            # Empty values should be removed
            assert 'empty_key' not in mock_config['default']
            assert 'whitespace_key' not in mock_config['default']
            
            # save_config should be called since changes were made
            mock_save.assert_called_once_with(mock_config)
    
    def test_validate_config_no_changes(self, mock_config):
        """Test validate_config when no changes are needed."""
        with patch('jiaz.core.config_utils.save_config') as mock_save:
            validate_config(mock_config)
            
            # save_config should not be called if no changes
            mock_save.assert_not_called()
    
    @patch('jiaz.core.config_utils.CONFIG_FILE')
    @patch('jiaz.core.config_utils.CONFIG_DIR')
    def test_load_config_file_exists(self, mock_config_dir, mock_config_file, temp_config_file):
        """Test loading existing config file."""
        mock_config_file.exists.return_value = True
        mock_config_file.__str__ = lambda x: str(temp_config_file)
        
        # Create a real config file
        config = configparser.ConfigParser()
        config['default'] = {'server_url': 'test.com'}
        with open(temp_config_file, 'w') as f:
            config.write(f)
        
        with patch('jiaz.core.config_utils.validate_config'):
            with patch('configparser.ConfigParser.read') as mock_read:
                mock_read.return_value = None
                result = load_config()
                
                assert result is not None
                mock_read.assert_called_once()
    
    @patch('jiaz.core.config_utils.CONFIG_FILE')
    def test_load_config_file_not_exists(self, mock_config_file):
        """Test loading config when file doesn't exist."""
        mock_config_file.exists.return_value = False
        
        with patch('jiaz.core.config_utils.validate_config'):
            result = load_config()
            
            assert result is not None
            assert isinstance(result, configparser.ConfigParser)
    
    @patch('jiaz.core.config_utils.CONFIG_DIR')
    @patch('jiaz.core.config_utils.CONFIG_FILE')
    def test_save_config(self, mock_config_file, mock_config_dir, mock_config):
        """Test saving config to file."""
        mock_config_dir.mkdir = Mock()
        
        with patch('builtins.open', mock_open()) as mock_file:
            save_config(mock_config)
            
            # Check that directory is created
            mock_config_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Check that file is opened for writing
            mock_file.assert_called_once()


class TestConfigSectionOperations:
    """Test suite for config section operations."""
    
    def test_get_active_config_exists(self, mock_config):
        """Test getting active config when it exists."""
        result = get_active_config(mock_config)
        assert result == 'default'
    
    def test_get_active_config_not_exists(self):
        """Test getting active config when meta section doesn't exist."""
        config = configparser.ConfigParser()
        result = get_active_config(config)
        assert result == 'default'
    
    def test_get_active_config_load_from_file(self):
        """Test getting active config loads from file when no config provided."""
        with patch('jiaz.core.config_utils.load_config') as mock_load:
            mock_config = Mock()
            mock_config.has_section.return_value = False
            mock_load.return_value = mock_config
            
            result = get_active_config()
            
            mock_load.assert_called_once()
            assert result == 'default'
    
    def test_set_active_config_new_meta(self):
        """Test setting active config when meta section doesn't exist."""
        config = configparser.ConfigParser()
        set_active_config(config, 'test_config')
        
        assert 'meta' in config
        assert config['meta']['active_config'] == 'test_config'
    
    def test_set_active_config_existing_meta(self, mock_config):
        """Test setting active config when meta section exists."""
        set_active_config(mock_config, 'new_config')
        
        assert mock_config['meta']['active_config'] == 'new_config'
    
    def test_get_specific_config_exists(self, mock_config):
        """Test getting specific config that exists."""
        result = get_specific_config('default', mock_config)
        assert result['server_url'] == 'https://test.jira.com'
    
    def test_get_specific_config_not_exists(self, mock_config):
        """Test getting specific config that doesn't exist."""
        with pytest.raises(typer.Exit):
            get_specific_config('nonexistent', mock_config)


class TestSecureValueOperations:
    """Test suite for secure value encoding/decoding."""
    
    def test_encode_secure_value(self):
        """Test encoding secure values."""
        test_value = "test_token_123"
        encoded = encode_secure_value(test_value)
        
        # Should be base64 encoded
        assert encoded != test_value
        assert isinstance(encoded, str)
        
        # Should be decodable
        decoded = base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
        assert decoded == test_value
    
    def test_decode_secure_value(self):
        """Test decoding secure values."""
        test_value = "test_token_123"
        encoded = base64.b64encode(test_value.encode('utf-8')).decode('utf-8')
        
        decoded = decode_secure_value(encoded)
        assert decoded == test_value
    
    def test_encode_decode_roundtrip(self):
        """Test encode/decode roundtrip."""
        original = "complex_token_!@#$%^&*()"
        encoded = encode_secure_value(original)
        decoded = decode_secure_value(encoded)
        
        assert decoded == original


class TestGeminiAPIOperations:
    """Test suite for Gemini API operations."""
    
    @patch('langchain_google_genai.ChatGoogleGenerativeAI')
    def test_validate_gemini_api_key_valid(self, mock_gemini):
        """Test validating valid Gemini API key."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock()
        mock_gemini.return_value = mock_llm
        
        result = validate_gemini_api_key("valid_key")
        
        assert result is True
        mock_gemini.assert_called_once_with(
            model="gemini-2.5-pro",
            google_api_key="valid_key",
            max_retries=1
        )
    
    @patch('jiaz.core.config_utils.typer')
    @patch('langchain_google_genai.ChatGoogleGenerativeAI')
    def test_validate_gemini_api_key_invalid(self, mock_gemini, mock_typer):
        """Test validating invalid Gemini API key."""
        mock_gemini.side_effect = Exception("API key invalid")
        
        result = validate_gemini_api_key("invalid_key")
        
        assert result is False
        mock_typer.echo.assert_called_once()
    
    def test_get_gemini_api_key_from_meta(self):
        """Test getting Gemini API key from meta section."""
        config = configparser.ConfigParser()
        config['meta'] = {
            'gemini_api_key': encode_secure_value('test_api_key'),
            'active_config': 'default'
        }
        
        result = get_gemini_api_key(config)
        assert result == 'test_api_key'
    
    def test_get_gemini_api_key_from_active_config(self):
        """Test getting Gemini API key from active config section."""
        config = configparser.ConfigParser()
        config['meta'] = {'active_config': 'default'}
        config['default'] = {
            'gemini_api_key': encode_secure_value('test_api_key')
        }
        
        result = get_gemini_api_key(config)
        assert result == 'test_api_key'
    
    def test_get_gemini_api_key_not_found(self):
        """Test getting Gemini API key when not found."""
        config = configparser.ConfigParser()
        config['meta'] = {'active_config': 'default'}
        config['default'] = {}
        
        result = get_gemini_api_key(config)
        assert result is None
    
    def test_should_use_gemini_with_key(self):
        """Test should_use_gemini when API key exists."""
        with patch('jiaz.core.config_utils.get_gemini_api_key', return_value='test_key'):
            result = should_use_gemini()
            assert result is True
    
    def test_should_use_gemini_without_key(self):
        """Test should_use_gemini when API key doesn't exist."""
        with patch('jiaz.core.config_utils.get_gemini_api_key', return_value=None):
            result = should_use_gemini()
            assert result is False


class TestPromptOperations:
    """Test suite for prompt operations."""
    
    @patch('typer.prompt')
    def test_prompt_with_fallback_value_provided(self, mock_prompt):
        """Test prompt with fallback when value is provided."""
        mock_prompt.return_value = "user_input"
        
        config = configparser.ConfigParser()
        result = prompt_with_fallback("Enter value", "Fallback prompt", config, "key")
        
        assert result == "user_input"
        mock_prompt.assert_called_once()
    
    @patch('typer.prompt')
    def test_prompt_with_fallback_use_existing(self, mock_prompt):
        """Test prompt with fallback using existing config value."""
        mock_prompt.return_value = ""
        
        config = configparser.ConfigParser()
        config['default'] = {'key': 'existing_value'}
        
        result = prompt_with_fallback("Enter value", "Fallback prompt", config, "key")
        assert result == "existing_value"
    
    @patch('typer.prompt')
    def test_prompt_with_fallback_no_existing(self, mock_prompt):
        """Test prompt with fallback when no existing value."""
        mock_prompt.side_effect = ["", "fallback_value"]
        
        config = configparser.ConfigParser()
        config['default'] = {}
        
        result = prompt_with_fallback("Enter value", "Fallback prompt", config, "key")
        assert result == "fallback_value"
    
    @patch('typer.prompt')
    def test_prompt_required_with_retries_success(self, mock_prompt):
        """Test required prompt succeeding on first try."""
        mock_prompt.return_value = "valid_value"
        
        result = prompt_required_with_retries(["Enter value"])
        assert result == "valid_value"
        mock_prompt.assert_called_once()
    
    @patch('typer.prompt')
    def test_prompt_required_with_retries_multiple_attempts(self, mock_prompt):
        """Test required prompt succeeding after multiple attempts."""
        mock_prompt.side_effect = ["", "", "valid_value"]
        
        result = prompt_required_with_retries(["Prompt 1", "Prompt 2", "Prompt 3"])
        assert result == "valid_value"
        assert mock_prompt.call_count == 3
    
    @patch('typer.prompt')
    def test_prompt_required_with_retries_failure(self, mock_prompt):
        """Test required prompt failing after max attempts."""
        mock_prompt.return_value = ""
        
        with pytest.raises(typer.Exit):
            prompt_required_with_retries(["Prompt"], max_attempts=2)
        
        assert mock_prompt.call_count == 2
    
    @patch('jiaz.core.config_utils.validate_gemini_api_key')
    @patch('typer.prompt')
    def test_prompt_api_key_with_retries_success(self, mock_prompt, mock_validate):
        """Test API key prompt succeeding."""
        mock_prompt.return_value = "valid_key"
        mock_validate.return_value = True
        
        result = prompt_api_key_with_retries()
        assert result == "valid_key"
        mock_validate.assert_called_once_with("valid_key")
    
    @patch('jiaz.core.config_utils.validate_gemini_api_key')
    @patch('typer.prompt')
    def test_prompt_api_key_with_retries_skip(self, mock_prompt, mock_validate):
        """Test API key prompt when user skips."""
        mock_prompt.return_value = ""
        
        result = prompt_api_key_with_retries()
        assert result is None
        mock_validate.assert_not_called()
    
    @patch('jiaz.core.config_utils.validate_gemini_api_key')
    @patch('typer.prompt')
    @patch('typer.echo')
    def test_prompt_api_key_with_retries_max_attempts(self, mock_echo, mock_prompt, mock_validate):
        """Test API key prompt reaching max attempts."""
        mock_prompt.return_value = "invalid_key"
        mock_validate.return_value = False
        
        result = prompt_api_key_with_retries(max_attempts=2)
        assert result is None
        assert mock_prompt.call_count == 2
        mock_echo.assert_called()


class TestConfigCollectionOperations:
    """Test suite for config collection operations."""
    
    @patch('jiaz.core.config_utils.prompt_with_fallback')
    @patch('typer.prompt')
    def test_collect_required_fields_with_fallback(self, mock_prompt, mock_fallback):
        """Test collecting required fields with fallback config."""
        mock_fallback.return_value = "fallback_server"
        mock_prompt.return_value = "new_token"
        
        config = configparser.ConfigParser()
        config['default'] = {'server_url': 'old_server'}
        
        result = collect_required_fields(config)
        
        assert result['server_url'] == "fallback_server"
        assert result['user_token'] == encode_secure_value("new_token")
    
    @patch('jiaz.core.config_utils.prompt_required_with_retries')
    def test_collect_required_fields_no_fallback(self, mock_required):
        """Test collecting required fields without fallback config."""
        mock_required.side_effect = ["new_server", "new_token"]
        
        result = collect_required_fields()
        
        assert result['server_url'] == "new_server"
        assert result['user_token'] == encode_secure_value("new_token")
        assert mock_required.call_count == 2
    
    @patch('typer.prompt')
    def test_collect_optional_fields(self, mock_prompt):
        """Test collecting optional fields."""
        mock_prompt.side_effect = ["PROJECT", "", "Sprint Board", "", ""]
        
        result = collect_optional_fields()
        
        assert result['jira_project'] == "PROJECT"
        assert 'jira_backlog_name' not in result  # Empty value should not be included
        assert result['jira_sprintboard_name'] == "Sprint Board"
        assert 'jira_sprintboard_id' not in result
        assert 'jira_board_name' not in result
    
    @patch('jiaz.core.config_utils.prompt_api_key_with_retries')
    @patch('jiaz.core.config_utils.encode_secure_value')
    @patch('typer.echo')
    def test_handle_gemini_api_key_input_success(self, mock_echo, mock_encode, mock_prompt):
        """Test handling Gemini API key input successfully."""
        mock_prompt.return_value = "valid_key"
        mock_encode.return_value = "encoded_key"
        
        config = configparser.ConfigParser()
        result = handle_gemini_api_key_input(config)
        
        assert result['gemini_api_key'] == "encoded_key"
        assert config['meta']['gemini_api_key'] == "encoded_key"
        mock_echo.assert_called()
    
    @patch('jiaz.core.config_utils.prompt_api_key_with_retries')
    @patch('typer.echo')
    def test_handle_gemini_api_key_input_skip(self, mock_echo, mock_prompt):
        """Test handling Gemini API key input when user skips."""
        mock_prompt.return_value = None
        
        config = configparser.ConfigParser()
        result = handle_gemini_api_key_input(config)
        
        assert result == {}
        assert 'meta' not in config
        mock_echo.assert_called()


class TestIntegration:
    """Integration tests for config_utils module."""
    
    def test_full_config_workflow(self, temp_config_file):
        """Test complete config workflow."""
        # Test saving and loading config
        config = configparser.ConfigParser()
        config['default'] = {
            'server_url': 'https://test.com',
            'user_token': encode_secure_value('test_token')
        }
        config['meta'] = {'active_config': 'default'}
        
        # Mock the config file path
        with patch('jiaz.core.config_utils.CONFIG_FILE', temp_config_file):
            with patch('jiaz.core.config_utils.CONFIG_DIR', temp_config_file.parent):
                save_config(config)
                
                # Load and verify
                loaded_config = load_config()
                
                assert 'default' in loaded_config
                assert loaded_config['default']['server_url'] == 'https://test.com'
                assert decode_secure_value(loaded_config['default']['user_token']) == 'test_token'
    
    def test_config_validation_workflow(self):
        """Test config validation with empty values."""
        config = configparser.ConfigParser()
        config['default'] = {
            'server_url': 'https://test.com',
            'empty_field': '',
            'valid_field': 'value'
        }
        
        with patch('jiaz.core.config_utils.save_config') as mock_save:
            validate_config(config)
            
            # Empty field should be removed
            assert 'empty_field' not in config['default']
            assert 'valid_field' in config['default']
            mock_save.assert_called_once()