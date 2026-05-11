import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open, PropertyMock
import pytest
from cognitum_autopoiesis.autopoiesis_engine import AutopoiesisEngine

class TestAutopoiesisEngine:
    def test_init(self):
        engine = AutopoiesisEngine()
        assert engine.self_healing_count == 0

    def test_send_to_mimo_success(self):
        engine = AutopoiesisEngine()
        code = "line1\nline2\nline3"
        result = engine._send_to_mimo(code, "error")
        assert result == "line1\nline3"

    def test_send_to_mimo_single_line(self):
        engine = AutopoiesisEngine()
        code = "single_line"
        result = engine._send_to_mimo(code, "error")
        assert result == code

    def test_send_to_mimo_exception(self):
        engine = AutopoiesisEngine()
        with patch.object(engine, '_send_to_mimo', side_effect=Exception('network error')):
            result = engine._send_to_mimo("code", "error")
            assert result is None

    def test_validate_syntax_valid(self):
        engine = AutopoiesisEngine()
        assert engine._validate_syntax("x = 1\ny = 2") is True
        assert engine._validate_syntax("def foo():\n    pass") is True

    def test_validate_syntax_invalid(self):
        engine = AutopoiesisEngine()
        assert engine._validate_syntax("def foo()\n    pass") is False
        assert engine._validate_syntax("if True") is False

    def test_heal_valid_repair(self):
        engine = AutopoiesisEngine()
        code = "line1\nline2\nline3"
        result = engine.heal(code, "error")
        assert result == "line1\nline3"
        assert engine.self_healing_count == 1

    def test_heal_send_returns_none(self):
        engine = AutopoiesisEngine()
        with patch.object(engine, '_send_to_mimo', return_value=None):
            code = "original_code"
            result = engine.heal(code, "error")
            assert result == code
            assert engine.self_healing_count == 0

    def test_heal_invalid_syntax_fixed(self):
        engine = AutopoiesisEngine()
        # Create a code that will be repaired to have syntax error
        code = "line1\nline2)\nline3"
        with patch.object(engine, '_send_to_mimo', return_value="line1\nline2)\nline3"):
            with patch.object(engine, '_validate_syntax', side_effect=[False, True]):
                with patch.object(engine, '_attempt_syntax_fix', return_value="fixed_code"):
                    result = engine.heal(code, "error")
                    assert result == "fixed_code"

    def test_heal_invalid_syntax_not_fixed(self):
        engine = AutopoiesisEngine()
        code = "original"
        with patch.object(engine, '_send_to_mimo', return_value="bad_code"):
            with patch.object(engine, '_validate_syntax', return_value=False):
                with patch.object(engine, '_attempt_syntax_fix', side_effect=Exception()):
                    result = engine.heal(code, "error")
                    assert result == code

    def test_attempt_syntax_fix_unbalanced(self):
        engine = AutopoiesisEngine()
        code = "print(1\nprint(2)"
        result = engine._attempt_syntax_fix(code)
        assert result == "print(1)\nprint(2)"

    def test_attempt_syntax_fix_missing_open(self):
        engine = AutopoiesisEngine()
        code = "1)\nprint(2)"
        result = engine._attempt_syntax_fix(code)
        assert result == "(1)\nprint(2)"

    def test_apply_patch_success(self):
        engine = AutopoiesisEngine()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            original_path = f.name
            f.write("original code")
        
        try:
            result = engine.apply_patch(original_path, "new code")
            assert result is True
            with open(original_path, 'r') as f:
                assert f.read() == "new code"
            assert os.path.exists(original_path + '.bak')
        finally:
            if os.path.exists(original_path):
                os.unlink(original_path)
            if os.path.exists(original_path + '.bak'):
                os.unlink(original_path + '.bak')

    def test_apply_patch_creates_backup(self):
        engine = AutopoiesisEngine()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            original_path = f.name
            f.write("original")
        
        try:
            engine.apply_patch(original_path, "patched")
            assert os.path.exists(original_path + '.bak')
            with open(original_path + '.bak', 'r') as f:
                assert f.read() == "original"
        finally:
            for path in [original_path, original_path + '.bak']:
                if os.path.exists(path):
                    os.unlink(path)

    def test_apply_patch_no_existing_file(self):
        engine = AutopoiesisEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nonexistent.py")
            result = engine.apply_patch(path, "code")
            assert result is True
            with open(path, 'r') as f:
                assert f.read() == "code"
            assert not os.path.exists(path + '.bak')

    def test_apply_patch_exception(self):
        engine = AutopoiesisEngine()
        result = engine.apply_patch("/nonexistent/dir/file.py", "code")
        assert result is False

    def test_restart_loop_with_valid_queue(self):
        engine = AutopoiesisEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, "queue.json")
            script_path = os.path.join(tmpdir, "script.py")
            
            # Create queue file
            queue_data = {"modules": {"mod1": {"status": "FAILED"}}}
            with open(queue_path, 'w') as f:
                json.dump(queue_data, f)
            
            # Create script file
            with open(script_path, 'w') as f:
                f.write("# script")
            
            with patch('subprocess.Popen') as mock_popen:
                engine.restart_loop(script_path, queue_path, "mod1")
                
                # Check queue was updated
                with open(queue_path, 'r') as f:
                    data = json.load(f)
                assert data["modules"]["mod1"]["status"] == "PENDING"
                assert data["modules"]["mod1"]["iterations"] == 0
                
                # Check subprocess was called
                mock_popen.assert_called_once()

    def test_restart_loop_empty_queue(self):
        engine = AutopoiesisEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, "queue.json")
            script_path = os.path.join(tmpdir, "script.py")
            
            # Create empty queue file
            with open(queue_path, 'w') as f:
                json.dump({}, f)
            
            # Create script file
            with open(script_path, 'w') as f:
                f.write("# script")
            
            with patch('subprocess.Popen') as mock_popen:
                engine.restart_loop(script_path, queue_path, "mod1")
                
                # Check queue was created correctly
                with open(queue_path, 'r') as f:
                    data = json.load(f)
                assert "modules" in data
                assert data["modules"]["mod1"]["status"] == "PENDING"

    def test_restart_loop_invalid_json(self):
        engine = AutopoiesisEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, "queue.json")
            script_path = os.path.join(tmpdir, "script.py")
            
            # Create invalid JSON file
            with open(queue_path, 'w') as f:
                f.write("invalid json")
            
            # Create script file
            with open(script_path, 'w') as f:
                f.write("# script")
            
            with patch('subprocess.Popen') as mock_popen:
                engine.restart_loop(script_path, queue_path, "mod1")
                
                # Check queue was recreated
                with open(queue_path, 'r') as f:
                    data = json.load(f)
                assert data["modules"]["mod1"]["status"] == "PENDING"

    def test_restart_loop_no_script_file(self):
        engine = AutopoiesisEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = os.path.join(tmpdir, "queue.json")
            script_path = os.path.join(tmpdir, "nonexistent.py")
            
            # Create queue file
            with open(queue_path, 'w') as f:
                json.dump({}, f)
            
            with patch('subprocess.Popen') as mock_popen:
                engine.restart_loop(script_path, queue_path, "mod1")
                
                # Subprocess should not be called
                mock_popen.assert_not_called()

    def test_restart_loop_exception(self):
        engine = AutopoiesisEngine()
        with patch('builtins.open', side_effect=Exception()):
            engine.restart_loop("script.py", "queue.json", "mod1")