from types import SimpleNamespace

import pytest

from src.auth import auth as auth_module
from src.auth.auth import Auth
from src.errors import InternalServerException, NotFoundException


class FakeAuthApiError(Exception):
    pass


class FakeClient:
    def __init__(self, *, user=None, side_effect=None):
        self.auth = self
        self._user = user
        self._side_effect = side_effect

    def get_user(self, _token):
        if self._side_effect:
            raise self._side_effect
        return SimpleNamespace(user=self._user)


@pytest.mark.asyncio
async def test_get_current_user_returns_user(monkeypatch):
    fake_user = SimpleNamespace(id="user-1")
    monkeypatch.setattr(auth_module, "get_auth_client", lambda: FakeClient(user=fake_user))

    auth = Auth("token")

    user = await auth.get_current_user()

    assert user == fake_user


@pytest.mark.asyncio
async def test_get_current_user_raises_not_found_when_user_missing(monkeypatch):
    monkeypatch.setattr(auth_module, "get_auth_client", lambda: FakeClient(user=None))

    auth = Auth("token")

    with pytest.raises(NotFoundException, match="No user found"):
        await auth.get_current_user()


@pytest.mark.asyncio
async def test_get_current_user_raises_not_found_for_invalid_or_expired_token(monkeypatch):
    monkeypatch.setattr(auth_module, "AuthApiError", FakeAuthApiError)
    monkeypatch.setattr(
        auth_module,
        "get_auth_client",
        lambda: FakeClient(side_effect=FakeAuthApiError("token is expired")),
    )

    auth = Auth("expired-token")

    with pytest.raises(NotFoundException, match="Invalid token"):
        await auth.get_current_user()


@pytest.mark.asyncio
async def test_get_current_user_raises_internal_server_for_unexpected_errors(monkeypatch):
    monkeypatch.setattr(auth_module, "get_auth_client", lambda: FakeClient(side_effect=RuntimeError("boom")))

    auth = Auth("token")

    with pytest.raises(InternalServerException, match="Failed to fetch user information"):
        await auth.get_current_user()
