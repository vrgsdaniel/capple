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

    async def get_user(self, _token):
        if self._side_effect:
            raise self._side_effect
        return SimpleNamespace(user=self._user)


async def test_get_current_user_returns_user():
    fake_user = SimpleNamespace(id="user-1")
    auth = Auth(FakeClient(user=fake_user), "token")

    user = await auth.get_current_user()

    assert user == fake_user


async def test_get_current_user_raises_not_found_when_user_missing():
    auth = Auth(FakeClient(user=None), "token")

    with pytest.raises(NotFoundException, match="No user found"):
        await auth.get_current_user()


async def test_get_current_user_raises_not_found_for_invalid_or_expired_token(monkeypatch):
    monkeypatch.setattr(auth_module, "AuthApiError", FakeAuthApiError)

    auth = Auth(FakeClient(side_effect=FakeAuthApiError("token is expired")), "expired-token")

    with pytest.raises(NotFoundException, match="Invalid token"):
        await auth.get_current_user()


async def test_get_current_user_raises_internal_server_for_unexpected_errors():
    auth = Auth(FakeClient(side_effect=RuntimeError("boom")), "token")

    with pytest.raises(InternalServerException, match="Failed to fetch user information"):
        await auth.get_current_user()
