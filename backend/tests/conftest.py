import asyncio
import inspect


def pytest_pyfunc_call(pyfuncitem):
    """Run async tests even when pytest-asyncio is unavailable in the environment."""
    test_fn = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_fn):
        return None

    funcargs = {name: pyfuncitem.funcargs[name] for name in pyfuncitem._fixtureinfo.argnames}
    asyncio.run(test_fn(**funcargs))
    return True
