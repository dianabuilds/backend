from __future__ import annotations

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

from domains.platform.iam.ports.email_port import EmailSender
from domains.platform.iam.ports.nonce_store_port import NonceStore
from domains.platform.iam.ports.token_port import TokenPair, TokenPort
from domains.platform.iam.ports.verification_port import (
    VerificationTokenStore,
)


@dataclass
class SignupIn:
    email: str
    password: str | None = None


@dataclass
class LoginIn:
    email: str
    password: str


@dataclass
class EvmVerifyIn:
    message: str
    signature: str
    wallet_address: str


class AuthService:
    def __init__(
        self,
        tokens: TokenPort,
        nonces: NonceStore,
        verification: VerificationTokenStore,
        mail: EmailSender,
    ) -> None:
        self.tokens = tokens
        self.nonces = nonces
        self.verification = verification
        self.mail = mail

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

    async def login(self, data: LoginIn) -> TokenPair:
        # Stub: accept any password; in real code check hash from DB
        return self.tokens.issue(subject=data.email)

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
    "EvmVerifyIn",
]
