"""
Unit tests for the Linux Namespace Management Layer.

Validates robust error handling, state tracking, and accurate command execution 
via mocked subprocess calls, allowing tests to run without root privileges.
"""

import pytest
from unittest.mock import patch, MagicMock
from lab.topology.namespace_manager import (
    NamespaceManager,
    LabConfig,
    NamespaceAlreadyExists,
    NamespaceNotFound,
    CommandExecutionError,
)


@pytest.fixture
def mock_config() -> LabConfig:
    return LabConfig(namespaces=["client", "router"])


@pytest.fixture
def manager(mock_config: LabConfig) -> NamespaceManager:
    return NamespaceManager(mock_config)


@patch("lab.topology.namespace_manager.subprocess.run")
def test_list_namespaces(mock_run: MagicMock, manager: NamespaceManager) -> None:
    """Verifies that ip netns list output is parsed correctly."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "client (id: 0)\nrouter (id: 1)\n\n"
    mock_run.return_value = mock_result

    namespaces = manager.list_namespaces()
    
    assert namespaces == ["client", "router"]
    mock_run.assert_called_once_with(["ip", "netns", "list"], capture_output=True, text=True, check=False)


@patch("lab.topology.namespace_manager.NamespaceManager.list_namespaces")
def test_namespace_exists(mock_list: MagicMock, manager: NamespaceManager) -> None:
    """Verifies boolean logic for namespace existence."""
    mock_list.return_value = ["client", "gateway"]
    
    assert manager.namespace_exists("client") is True
    assert manager.namespace_exists("router") is False


@patch("lab.topology.namespace_manager.subprocess.run")
@patch("lab.topology.namespace_manager.NamespaceManager.namespace_exists")
def test_create_namespace_success(mock_exists: MagicMock, mock_run: MagicMock, manager: NamespaceManager) -> None:
    """Verifies successful namespace creation."""
    mock_exists.return_value = False
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    manager.create_namespace("client")
    mock_run.assert_called_once_with(["ip", "netns", "add", "client"], capture_output=True, text=True, check=False)


@patch("lab.topology.namespace_manager.NamespaceManager.namespace_exists")
def test_create_namespace_already_exists(mock_exists: MagicMock, manager: NamespaceManager) -> None:
    """Verifies creation raises an error if the namespace exists."""
    mock_exists.return_value = True

    with pytest.raises(NamespaceAlreadyExists):
        manager.create_namespace("client")


@patch("lab.topology.namespace_manager.subprocess.run")
@patch("lab.topology.namespace_manager.NamespaceManager.namespace_exists")
def test_delete_namespace_success(mock_exists: MagicMock, mock_run: MagicMock, manager: NamespaceManager) -> None:
    """Verifies successful namespace deletion."""
    mock_exists.return_value = True
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    manager.delete_namespace("client")
    mock_run.assert_called_once_with(["ip", "netns", "delete", "client"], capture_output=True, text=True, check=False)


@patch("lab.topology.namespace_manager.NamespaceManager.namespace_exists")
def test_delete_namespace_not_found(mock_exists: MagicMock, manager: NamespaceManager) -> None:
    """Verifies deletion raises an error if the namespace does not exist."""
    mock_exists.return_value = False

    with pytest.raises(NamespaceNotFound):
        manager.delete_namespace("client")


@patch("lab.topology.namespace_manager.subprocess.run")
@patch("lab.topology.namespace_manager.NamespaceManager.namespace_exists")
def test_execute_success(mock_exists: MagicMock, mock_run: MagicMock, manager: NamespaceManager) -> None:
    """Verifies command execution routing into a specific namespace."""
    mock_exists.return_value = True
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "64 bytes from 127.0.0.1"
    mock_run.return_value = mock_result

    output = manager.execute("client", ["ping", "-c", "1", "127.0.0.1"])
    
    assert output == "64 bytes from 127.0.0.1"
    mock_run.assert_called_once_with(
        ["ip", "netns", "exec", "client", "ping", "-c", "1", "127.0.0.1"], 
        capture_output=True, text=True, check=False
    )


@patch("lab.topology.namespace_manager.subprocess.run")
@patch("lab.topology.namespace_manager.NamespaceManager.namespace_exists")
def test_execute_failure(mock_exists: MagicMock, mock_run: MagicMock, manager: NamespaceManager) -> None:
    """Verifies underlying command failures are caught and wrapped correctly."""
    mock_exists.return_value = True
    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stderr = "ping: unknown host"
    mock_run.return_value = mock_result

    with pytest.raises(CommandExecutionError):
        manager.execute("client", ["ping", "invalid_host"])


@patch("lab.topology.namespace_manager.NamespaceManager.delete_namespace")
def test_cleanup(mock_delete: MagicMock, manager: NamespaceManager) -> None:
    """Verifies the cleanup routine correctly iterates through the configuration."""
    # Simulate first delete succeeding, second failing (already deleted)
    mock_delete.side_effect = [None, NamespaceNotFound("Not found")]
    
    manager.cleanup()
    
    # Should attempt to delete all items in mock_config.namespaces
    assert mock_delete.call_count == 2
    mock_delete.assert_any_call("client")
    mock_delete.assert_any_call("router")