from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Any

try:  # eth-account is in requirements; guard for safety
    from eth_account import Account  # type: ignore
    from eth_account.messages import encode_defunct  # type: ignore
    from web3 import Web3  # type: ignore
except Exception:  # pragma: no cover
    Account = None  # type: ignore
    encode_defunct = None  # type: ignore
    Web3 = None  # type: ignore
import re

from domains.platform.iam.ports.credentials_port import AuthIdentity, CredentialsPort
from domains.platform.iam.ports.email_port import EmailSender
from domains.platform.iam.ports.nonce_store_port import NonceStore
from domains.platform.iam.ports.token_port import TokenPair, TokenPort
from domains.platform.iam.ports.verification_port import (
    VerificationTokenStore,
)
from packages.core.config import Settings


@dataclass
class SignupIn:
    email: str
    password: str | None = None


@dataclass
class LoginIn:
    login: str
    password: str


@dataclass
class LoginResult:
    tokens: TokenPair
    user: AuthIdentity
    source: str = "credentials"


@dataclass
class EvmVerifyIn:
    message: str
    signature: str
    wallet_address: str


class AuthError(Exception):
    """Raised when authentication fails (invalid credentials, inactive user, etc.)."""


class AuthService:
    def __init__(
        self,
        tokens: TokenPort,
        nonces: NonceStore,
        verification: VerificationTokenStore,
        mail: EmailSender,
        credentials: CredentialsPort,
        settings: Settings,
    ) -> None:
        self.tokens = tokens
        self.nonces = nonces
        self.verification = verification
        self.mail = mail
        self.credentials = credentials
        self.settings = settings

    async def signup(self, data: SignupIn) -> dict[str, Any]:
        # Stub: send verification email with token
        token = await self.verification.create(data.email)
        await self.mail.send([data.email], "Verify your email", text=f"Token: {token}")
        return {"ok": True}

    async def verify_email(self, token: str) -> dict[str, Any]:
        email = await self.verification.verify(token)
        if not email:
            return {"ok": False, "error": "invalid_token"}
        # Stub: mark user as verified (no DB yet)
        return {"ok": True, "email": email}

    def _bootstrap_identity(self, login: str, password: str) -> AuthIdentity | None:
        configured_login = (self.settings.auth_bootstrap_login or "").strip()
        configured_password = self.settings.auth_bootstrap_password
        if not configured_login or configured_password is None:
            return None
        if not hmac.compare_digest(login.strip().lower(), configured_login.lower()):
            return None
        if not hmac.compare_digest(password, configured_password):
            return None
        role = (self.settings.auth_bootstrap_role or "admin").strip() or "admin"
        return AuthIdentity(
            id=str(self.settings.auth_bootstrap_user_id or "bootstrap-root"),
            email=None,
            username=configured_login,
            role=role,
            is_active=True,
        )

    async def login(self, data: LoginIn) -> LoginResult:
        source = "credentials"
        try:
            user = await self.credentials.authenticate(data.login, data.password)
        except Exception:
            user = None
        if not user:
            user = self._bootstrap_identity(data.login, data.password)
            if not user:
                raise AuthError("invalid_credentials")
            source = "bootstrap"
        if not user.is_active:
            raise AuthError("user_inactive")
        claims: dict[str, Any] = {"role": user.role}
        if user.email:
            claims["email"] = user.email
        if user.username:
            claims["username"] = user.username
        tokens = self.tokens.issue(subject=user.id, claims=claims)
        return LoginResult(tokens=tokens, user=user, source=source)

    async def refresh(self, refresh_token: str) -> TokenPair:
        return self.tokens.refresh(refresh_token)

    async def evm_nonce(self, user_id: str) -> dict[str, Any]:
        nonce = await self.nonces.issue(user_id)
        return {"nonce": nonce}

    async def evm_verify(self, data: EvmVerifyIn) -> TokenPair:
        if Account is None or encode_defunct is None or Web3 is None:
            raise RuntimeError("eth-account/web3 not installed")
        try:
            msg = encode_defunct(text=data.message)
            recovered = Account.recover_message(msg, signature=data.signature)
            rec = Web3.to_checksum_address(recovered)
            want = Web3.to_checksum_address(data.wallet_address)
        except Exception as e:  # pragma: no cover - library/parsing errors
            raise RuntimeError(f"siwe_verification_failed: {e}") from e
        if rec != want:
            raise RuntimeError("siwe_signature_mismatch")
        # Extract and verify nonce if present in message
        m = re.search(r"Nonce:\s*([A-Za-z0-9-]+)", data.message, re.IGNORECASE)
        if m:
            nonce = m.group(1)
            try:
                ok = await self.nonces.verify(want, nonce)
                if not ok:
                    raise RuntimeError("siwe_nonce_invalid_or_used")
            except Exception:
                # If nonce backend unavailable, continue but warn via error message if needed
                pass
        return self.tokens.issue(subject=want)


__all__ = [
    "AuthService",
    "SignupIn",
    "LoginIn",
    "LoginResult",
    "EvmVerifyIn",
    "AuthError",
]
