"""Mini Redis 핵심 로직.

사용 자료구조:
  - HashMap      : key → Node (O(1) 조회)
  - DoublyLinkedList : LRU 순서 유지
  - MinHeap      : TTL 만료 순서 관리 (lazy-deletion)
"""

import time

from hash_map import HashMap
from linked_list import DoublyLinkedList, Node
from min_heap import MinHeap


class MiniRedis:
    """명령어 파싱·실행·자료구조 조율 담당"""

    def __init__(self):
        self._store = HashMap()          # key → Node
        self._lru_list = DoublyLinkedList()
        self._ttl_heap = MinHeap()       # (expire_at, key)
        self._maxmemory = 0              # 0 = 무제한
        self._used_memory = 0
        self._evicted_keys = 0

    # ── 공개 진입점 ───────────────────────────────────────

    def execute(self, line):
        """입력 줄을 파싱해 명령어 실행 후 결과 문자열 반환"""
        tokens = self._tokenize(line)
        if not tokens:
            return None
        cmd = tokens[0].upper()
        args = tokens[1:]

        dispatch = {
            'SET':    self._cmd_set,
            'GET':    self._cmd_get,
            'DEL':    self._cmd_del,
            'EXISTS': self._cmd_exists,
            'DBSIZE': self._cmd_dbsize,
            'KEYS':   self._cmd_keys,
            'CONFIG': self._cmd_config,
            'INFO':   self._cmd_info,
            'EXPIRE': self._cmd_expire,
            'TTL':    self._cmd_ttl,
        }
        if cmd in dispatch:
            return dispatch[cmd](args)
        return f"(error) ERR unknown command '{cmd}'"

    # ── 토크나이저 ────────────────────────────────────────

    @staticmethod
    def _tokenize(line):
        """공백 분리, 큰따옴표 문자열 지원"""
        tokens = []
        current = []
        in_quote = False
        for ch in line:
            if ch == '"':
                in_quote = not in_quote
            elif ch == ' ' and not in_quote:
                if current:
                    tokens.append(''.join(current))
                    current = []
            else:
                current.append(ch)
        if current:
            tokens.append(''.join(current))
        return tokens

    # ── 내부 헬퍼 ─────────────────────────────────────────

    def _evict_expired(self):
        """만료된 키 lazy-deletion: 명령 실행 전 호출"""
        now = time.time()
        while self._ttl_heap.size() > 0:
            entry = self._ttl_heap.peek()
            expire_at, key = entry
            if expire_at > now:
                break
            self._ttl_heap.pop()
            node = self._store.get(key)
            # 스탈 엔트리 체크: node의 expire_at과 일치할 때만 삭제
            if node is not None and node.expire_at == expire_at:
                self._delete_key(key)

    def _delete_key(self, key):
        """키 완전 삭제 (store + lru_list + 메모리 카운터)"""
        node = self._store.get(key)
        if node is None:
            return False
        self._lru_list.remove_node(node)
        self._store.remove(key)
        self._used_memory -= len(key.encode('utf-8')) + len(node.value.encode('utf-8'))
        return True

    @staticmethod
    def _byte_size(key, value):
        return len(key.encode('utf-8')) + len(value.encode('utf-8'))

    # ── 명령어 구현 ───────────────────────────────────────

    def _cmd_set(self, args):
        if len(args) != 2:
            return "(error) ERR wrong number of arguments for 'SET' command"
        key, value = args[0], args[1]
        self._evict_expired()

        new_size = self._byte_size(key, value)

        # 기존 키가 있으면 먼저 제거 (크기 차감, LRU에서 분리)
        if self._store.contains(key):
            old_node = self._store.get(key)
            old_size = self._byte_size(key, old_node.value)
            self._lru_list.remove_node(old_node)
            self._store.remove(key)
            self._used_memory -= old_size

        # maxmemory 초과 시 LRU 제거
        if self._maxmemory > 0:
            while self._used_memory + new_size > self._maxmemory:
                evicted = self._lru_list.remove_back()
                if evicted is None:
                    return "(error) OOM command not allowed when used_memory > 'maxmemory'"
                self._store.remove(evicted.key)
                self._used_memory -= self._byte_size(evicted.key, evicted.value)
                self._evicted_keys += 1

        node = Node(key, value)
        self._lru_list.insert_front(node)
        self._store.put(key, node)
        self._used_memory += new_size
        return "OK"

    def _cmd_get(self, args):
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'GET' command"
        key = args[0]
        self._evict_expired()
        node = self._store.get(key)
        if node is None:
            return "(nil)"
        self._lru_list.move_to_front(node)
        return f'"{node.value}"'

    def _cmd_del(self, args):
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'DEL' command"
        key = args[0]
        self._evict_expired()
        return "(integer) 1" if self._delete_key(key) else "(integer) 0"

    def _cmd_exists(self, args):
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'EXISTS' command"
        key = args[0]
        self._evict_expired()
        return "(integer) 1" if self._store.contains(key) else "(integer) 0"

    def _cmd_dbsize(self, args):
        if args:
            return "(error) ERR wrong number of arguments for 'DBSIZE' command"
        self._evict_expired()
        return f"(integer) {self._store.size()}"

    def _cmd_keys(self, args):
        if args:
            return "(error) ERR wrong number of arguments for 'KEYS' command"
        self._evict_expired()
        all_keys = self._store.keys()
        if not all_keys:
            return "(empty array)"
        return '\n'.join(f'{i + 1}. "{k}"' for i, k in enumerate(all_keys))

    def _cmd_config(self, args):
        if len(args) < 2:
            return "(error) ERR wrong number of arguments for 'CONFIG' command"
        sub = args[0].upper()
        if sub == 'SET':
            if len(args) != 3:
                return "(error) ERR wrong number of arguments for 'CONFIG' command"
            param = args[1].upper()
            if param == 'MAXMEMORY':
                try:
                    val = int(args[2])
                    if val < 0:
                        return "(error) ERR value is not an integer or out of range"
                    self._maxmemory = val
                    return "OK"
                except ValueError:
                    return "(error) ERR value is not an integer or out of range"
            return f"(error) ERR unknown config parameter '{args[1]}'"
        return f"(error) ERR unknown subcommand '{args[0]}'"

    def _cmd_info(self, args):
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'INFO' command"
        if args[0].lower() != 'memory':
            return f"(error) ERR unknown INFO section '{args[0]}'"
        return (
            f"used_memory:{self._used_memory}\n"
            f"maxmemory:{self._maxmemory}\n"
            f"evicted_keys:{self._evicted_keys}"
        )

    def _cmd_expire(self, args):
        if len(args) != 2:
            return "(error) ERR wrong number of arguments for 'EXPIRE' command"
        key = args[0]
        try:
            seconds = int(args[1])
        except ValueError:
            return "(error) ERR value is not an integer or out of range"
        self._evict_expired()
        if not self._store.contains(key):
            return "(integer) 0"
        if seconds <= 0:
            # 즉시 만료
            self._delete_key(key)
            return "(integer) 1"
        expire_at = time.time() + seconds
        node = self._store.get(key)
        node.expire_at = expire_at
        self._ttl_heap.push(expire_at, key)
        return "(integer) 1"

    def _cmd_ttl(self, args):
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'TTL' command"
        key = args[0]
        self._evict_expired()
        node = self._store.get(key)
        if node is None:
            return "(integer) -2"
        if node.expire_at is None:
            return "(integer) -1"
        remaining = node.expire_at - time.time()
        if remaining <= 0:
            self._delete_key(key)
            return "(integer) -2"
        return f"(integer) {int(remaining)}"
