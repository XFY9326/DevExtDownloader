import asyncio


class TokenLockEntry:
    __slots__ = ("lock", "owner", "recursion", "waiters")

    def __init__(self) -> None:
        self.lock: asyncio.Lock = asyncio.Lock()
        self.owner: asyncio.Task | None = None
        self.recursion: int = 0
        self.waiters: int = 0


class TokenLockContext:
    def __init__(self, lock: 'TokenLock', token: str, timeout: float | None) -> None:
        self._lock = lock
        self._token = token
        self._timeout = timeout

    async def __aenter__(self) -> 'TokenLockContext':
        await self._lock.acquire(self._token, self._timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        await self._lock.release(self._token)
        return False


class TokenLock:
    def __init__(self) -> None:
        self._locks: dict[str, TokenLockEntry] = {}
        self._mgr_lock: asyncio.Lock = asyncio.Lock()

    def lock(self, token: str, timeout: float | None = None) -> TokenLockContext:
        return TokenLockContext(self, token, timeout)

    async def acquire(self, token: str, timeout: float | None = None) -> TokenLockEntry:
        return await self._acquire_internal(token, timeout)

    async def release(self, token: str) -> None:
        await self._release_internal(token)

    async def _acquire_internal(self, token: str, timeout: float | None) -> TokenLockEntry:
        async with self._mgr_lock:
            entry = self._locks.get(token)
            if entry is None:
                entry = TokenLockEntry()
                self._locks[token] = entry
            entry.waiters += 1

        got_it = False
        try:
            current = asyncio.current_task()
            if entry.owner is current:
                entry.recursion += 1
                got_it = True
                return entry

            if timeout is None:
                await entry.lock.acquire()
            else:
                await asyncio.wait_for(entry.lock.acquire(), timeout)

            entry.owner = current
            entry.recursion = 1
            got_it = True
            return entry

        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            raise
        finally:
            async with self._mgr_lock:
                entry.waiters -= 1
                if not got_it and entry.waiters == 0 and entry.owner is None and not entry.lock.locked():
                    existing = self._locks.get(token)
                    if existing is entry:
                        del self._locks[token]

    async def _release_internal(self, token: str) -> None:
        async with self._mgr_lock:
            entry = self._locks.get(token)
            if entry is None:
                raise RuntimeError("release on unknown token")

            current = asyncio.current_task()
            if entry.owner is not current:
                raise RuntimeError("current task does not own the lock for token")

            entry.recursion -= 1
            if entry.recursion > 0:
                return

            entry.owner = None
            try:
                entry.lock.release()
            except RuntimeError as exc:
                raise RuntimeError("internal lock release error") from exc

            if entry.waiters == 0 and not entry.lock.locked() and entry.owner is None:
                existing = self._locks.get(token)
                if existing is entry:
                    del self._locks[token]

    async def is_locked(self, token: str) -> bool:
        async with self._mgr_lock:
            entry = self._locks.get(token)
            if not entry:
                return False
            return entry.owner is not None or entry.lock.locked()

    async def known_token_count(self) -> int:
        async with self._mgr_lock:
            return len(self._locks)
