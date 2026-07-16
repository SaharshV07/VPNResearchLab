"""
Unit tests for the repository HealthChecker.
"""

import pytest
from unittest.mock import patch, MagicMock
from healthcheck import HealthChecker

@patch("healthcheck.sys.version_info")
def test_verify_python_version(mock_version) -> None:
    checker = HealthChecker()
    
    # Test success (3.12)
    mock_version.major = 3
    mock_version.minor = 12
    checker.verify_python()
    assert checker.results[-1].status == "PASS"
    
    # Test failure (3.10)
    mock_version.minor = 10
    checker.verify_python()
    assert checker.results[-1].status == "FAIL"

@patch("healthcheck.is_linux")
@patch("healthcheck.check_linux_dependency")
def test_linux_dependency_skip_on_windows(mock_check_dep, mock_is_linux) -> None:
    mock_is_linux.return_value = False
    checker = HealthChecker()
    
    checker.verify_linux_dependencies()
    
    # Ensure all linux-specific checks return SKIPPED on Windows
    linux_results = [r for r in checker.results if r.name in ["wg", "tcpdump", "iptables", "conntrack"]]
    assert all(r.status == "SKIPPED" for r in linux_results)
    mock_check_dep.assert_not_called()

@patch("healthcheck.import_module")
def test_verify_imports(mock_import) -> None:
    checker = HealthChecker()
    
    # Simulate valid imports
    checker.verify_imports()
    assert all(r.status == "PASS" for r in checker.results)
    
    # Simulate missing scapy
    checker.results.clear()
    mock_import.side_effect = ImportError("No module named scapy")
    checker.verify_imports()
    scapy_result = next(r for r in checker.results if r.name == "Scapy")
    assert scapy_result.status == "FAIL"