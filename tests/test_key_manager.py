"""
Unit tests for the WireGuard Key Management Layer.
"""

import os
import stat
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from lab.vpn.key_manager import (
    WireGuardKeyManager,
    WireGuardKeyPair,
    WireGuardKeyError
)

# Dummy Base64 Keys (44 characters, exact WireGuard length)
MOCK_PRIV_KEY = "a" * 43 + "="
MOCK_PUB_KEY = "b" * 43 + "="


@pytest.fixture
def key_manager() -> WireGuardKeyManager:
    return WireGuardKeyManager()


@patch("lab.vpn.key_manager.subprocess.run")
def test_generate_private_key(mock_run: MagicMock, key_manager: WireGuardKeyManager) -> None:
    """Verifies private key generation calls the correct subprocess."""
    mock_result = MagicMock()
    mock_result.stdout = f"{MOCK_PRIV_KEY}\n"
    mock_run.return_value = mock_result

    priv = key_manager.generate_private_key()
    
    assert priv == MOCK_PRIV_KEY
    mock_run.assert_called_once_with(
        ["wg", "genkey"],
        input=None,
        capture_output=True,
        text=True,
        check=True
    )


@patch("lab.vpn.key_manager.subprocess.run")
def test_generate_private_key_in_namespace(mock_run: MagicMock, key_manager: WireGuardKeyManager) -> None:
    """Verifies command prefixes correctly when targeting a namespace."""
    mock_result = MagicMock()
    mock_result.stdout = f"{MOCK_PRIV_KEY}\n"
    mock_run.return_value = mock_result

    key_manager.generate_private_key(namespace="client_ns")
    
    mock_run.assert_called_once_with(
        ["ip", "netns", "exec", "client_ns", "wg", "genkey"],
        input=None,
        capture_output=True,
        text=True,
        check=True
    )


@patch("lab.vpn.key_manager.subprocess.run")
def test_derive_public_key(mock_run: MagicMock, key_manager: WireGuardKeyManager) -> None:
    """Verifies public key derivation correctly pipes the private key to stdin."""
    mock_result = MagicMock()
    mock_result.stdout = f"{MOCK_PUB_KEY}\n"
    mock_run.return_value = mock_result

    pub = key_manager.derive_public_key(MOCK_PRIV_KEY)
    
    assert pub == MOCK_PUB_KEY
    mock_run.assert_called_once_with(
        ["wg", "pubkey"],
        input=MOCK_PRIV_KEY,
        capture_output=True,
        text=True,
        check=True
    )


@patch.object(WireGuardKeyManager, "derive_public_key")
@patch.object(WireGuardKeyManager, "generate_private_key")
def test_generate_keypair(mock_gen_priv: MagicMock, mock_derive_pub: MagicMock, key_manager: WireGuardKeyManager) -> None:
    """Verifies end-to-end keypair generation produces the correct dataclass."""
    mock_gen_priv.return_value = MOCK_PRIV_KEY
    mock_derive_pub.return_value = MOCK_PUB_KEY

    keypair = key_manager.generate_keypair()
    
    assert keypair.private_key == MOCK_PRIV_KEY
    assert keypair.public_key == MOCK_PUB_KEY


def test_save_and_load_keypair(key_manager: WireGuardKeyManager, tmp_path: Path) -> None:
    """Verifies keypairs serialize to disk properly with strict 0o600 permissions."""
    priv_path = tmp_path / "private.key"
    pub_path = tmp_path / "public.key"
    keypair = WireGuardKeyPair(MOCK_PRIV_KEY, MOCK_PUB_KEY)

    key_manager.save_keypair(keypair, priv_path, pub_path)

    # Validate Files Exist
    assert priv_path.exists()
    assert pub_path.exists()

    # Validate Permissions (User Read/Write only)
    file_stat = os.stat(priv_path)
    # Check if the permission bits match 0o600
    assert stat.S_IMODE(file_stat.st_mode) == 0o600

    # Validate Loading
    loaded_kp = key_manager.load_keypair(priv_path, pub_path)
    assert loaded_kp.private_key == MOCK_PRIV_KEY
    assert loaded_kp.public_key == MOCK_PUB_KEY


@patch.object(WireGuardKeyManager, "derive_public_key")
def test_validate_keypair(mock_derive: MagicMock, key_manager: WireGuardKeyManager) -> None:
    """Verifies the mathematical validation logic accurately checks pair integrity."""
    keypair = WireGuardKeyPair(MOCK_PRIV_KEY, MOCK_PUB_KEY)
    
    # Simulate valid derivation
    mock_derive.return_value = MOCK_PUB_KEY
    assert key_manager.validate_keypair(keypair) is True

    # Simulate corrupted/mismatched derivation
    mock_derive.return_value = "WRONG_KEY="
    assert key_manager.validate_keypair(keypair) is False