class WalletError(Exception):
    """Base exception for wallet domain errors."""


class WalletNotFoundError(WalletError):
    pass


class InsufficientFundsError(WalletError):
    pass
