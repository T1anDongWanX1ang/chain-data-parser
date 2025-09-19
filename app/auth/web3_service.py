"""Web3 signature verification service"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Tuple
from eth_account.messages import encode_defunct
from eth_account import Account
from fastapi import HTTPException, status


class Web3Service:
    """Web3 signature verification service class"""

    @staticmethod
    def generate_challenge(wallet_address: str) -> Tuple[str, datetime]:
        """
        Generate signature challenge

        Args:
            wallet_address: Wallet address

        Returns:
            (Challenge message, Expiration time)
        """
        # Generate random number
        nonce = secrets.token_hex(16)
        timestamp = int(datetime.utcnow().timestamp())

        # Challenge expiration time (5 minutes)
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        # Construct challenge message
        challenge = f"Please sign this message to verify your wallet ownership.\n\n" \
                   f"Wallet address: {wallet_address}\n" \
                   f"Nonce: {nonce}\n" \
                   f"Timestamp: {timestamp}\n\n" \
                   f"This signature will not incur any fees."

        return challenge, expires_at

    @staticmethod
    def verify_signature(wallet_address: str, signature: str, challenge: str) -> bool:
        """
        Verify wallet signature

        Args:
            wallet_address: Wallet address
            signature: Signature
            challenge: Challenge message

        Returns:
            Verification result

        Raises:
            HTTPException: When verification fails
        """
        try:
            # Encode message
            message = encode_defunct(text=challenge)

            # Recover signature address
            recovered_address = Account.recover_message(message, signature=signature)

            # Compare addresses (case insensitive)
            return recovered_address.lower() == wallet_address.lower()

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signature verification failed: {str(e)}"
            )

    @staticmethod
    def is_challenge_expired(challenge: str, max_age_minutes: int = 5) -> bool:
        """
        Check if challenge is expired

        Args:
            challenge: Challenge message
            max_age_minutes: Maximum validity period (minutes)

        Returns:
            Whether expired
        """
        try:
            # Extract timestamp from challenge message
            lines = challenge.split('\n')
            timestamp_line = None

            for line in lines:
                if line.startswith('Timestamp:'):
                    timestamp_line = line
                    break

            if not timestamp_line:
                return True

            # Extract timestamp
            timestamp_str = timestamp_line.split(':')[1].strip()
            timestamp = int(timestamp_str)

            # Check if expired
            challenge_time = datetime.fromtimestamp(timestamp)
            expire_time = challenge_time + timedelta(minutes=max_age_minutes)

            return datetime.utcnow() > expire_time

        except (ValueError, IndexError):
            # If timestamp cannot be parsed, consider expired
            return True

    @staticmethod
    def extract_wallet_from_challenge(challenge: str) -> str:
        """
        Extract wallet address from challenge message

        Args:
            challenge: Challenge message

        Returns:
            Wallet address

        Raises:
            HTTPException: When extraction fails
        """
        try:
            lines = challenge.split('\n')

            for line in lines:
                if line.startswith('Wallet address:'):
                    wallet_address = line.split(':')[1].strip()
                    return wallet_address.lower()

            raise ValueError("Unable to find wallet address in challenge message")

        except (ValueError, IndexError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid challenge message format: {str(e)}"
            )

    @staticmethod
    def validate_ethereum_address(address: str) -> bool:
        """
        Validate Ethereum address format

        Args:
            address: Address string

        Returns:
            Whether valid
        """
        if not address:
            return False

        # Check format
        if not address.startswith('0x'):
            return False

        if len(address) != 42:
            return False

        # Check if valid hexadecimal
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False