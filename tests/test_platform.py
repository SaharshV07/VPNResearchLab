"""
Unit tests for cross-platform utilities.
"""

import sys
from unittest.mock import patch
from framework.utils.platform import is_linux, is_windows, is_admin, check_linux_dependency

def test_is_linux() -> None:
    with patch.object(sys, "platform", "linux"):
        assert is_linux() is True
    with patch.object(sys, "platform", "win32"):
        assert is_linux() is False

def test_is_windows() -> None:
    with patch.object(sys, "platform", "win32"):
        assert is_windows() is True
    with patch.object(sys, "platform", "darwin"):
        assert is_windows() is False

@patch("framework.utils.platform.is_windows")
@patch("framework.utils.platform.is_linux")
@patch("os.geteuid", create=True)
def test_is_admin_linux(mock_geteuid, mock_linux, mock_windows) -> None:
    mock_windows.return_value = False
    mock_linux.return_value = True
    
    mock_geteuid.return_value = 0
    assert is_admin() is True
    
    mock_geteuid.return_value = 1000
    assert is_admin() is False

@patch("framework.utils.platform.is_linux")
@patch("shutil.which")
def test_check_linux_dependency(mock_which, mock_linux) -> None:
    # Test on Linux with present binary
    mock_linux.return_value = True
    mock_which.return_value = "/usr/bin/wg"
    assert check_linux_dependency("wg") is True

    # Test on Linux with missing binary
    mock_which.return_value = None
    assert check_linux_dependency("missing_bin") is False

    # Test on Windows (should short-circuit to False)
    mock_linux.return_value = False
    assert check_linux_dependency("wg") is False