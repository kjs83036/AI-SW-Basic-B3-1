from hash_map import Hash_map
from doubly_linked_list import Doubly_linked_list, Node
from min_heap import Min_heap
import time


HELP_TEXT = """Mini Redis 명령어 도움말:
  SET key value            : 키-값 저장 (maxmemory 초과 시 LRU 제거)
  GET key                  : 값 조회
  DEL key                  : 키 삭제
  EXISTS key               : 존재 여부 확인
  DBSIZE                   : 저장된 키 수
  KEYS                     : 전체 키 목록
  CONFIG SET maxmemory N   : 최대 메모리 설정 (0 = 무제한)
  INFO memory              : 메모리 사용량 조회
  EXPIRE key N             : TTL 설정 (초)
  TTL key                  : 남은 만료 시간 조회
  HELP                     : 도움말 출력
  exit / quit              : 종료"""

class MiniRedis:

    def __init__(self):
        self._store = Hash_map()          # key → Node
        self._lru_list = Doubly_linked_list()
        self._ttl_heap = Min_heap()       # (expire_at, key)
        self._maxmemory = 0              # 0 = 무제한
        self._used_memory = 0
        self._evicted_keys = 0

    def _evict_expired(self):
        """
        만료 시간이 지난 키들을 최소 힙에서 순차적으로 꺼내 데이터베이스에서 실시간 삭제(Lazy-deletion)합니다.
        모든 데이터 조회/수정 명령 실행 전에 가장 먼저 호출되어 데이터 정합성을 유지합니다.
        """
        now = time.time()
        while self._ttl_heap.size() > 0:
            entry = self._ttl_heap.peek()
            if entry:
                expire_at, key = entry[0], entry[1]
            if expire_at > now:
                break
            self._ttl_heap.pop()
            node = self._store.get(key)
            # 스탈 엔트리 체크: node의 expire_at과 일치할 때만 삭제
            if node is not None and node.expire_at == expire_at:
                self._delete_key(key)

    def _delete_key(self, key):
        node = self._store.get(key)
        if node is None:
            return False
        self._lru_list.remove_node(node)
        self._store.remove(key)
        self._used_memory -= self._byte_size(key, node.data[1])
        return True

    def _byte_size(self, key, value):
        return len(key.encode('utf-8')) + len(value.encode('utf-8'))

    def set(self, args):
        """
        key-value 데이터를 저장합니다. 
        만약 maxmemory 설정이 되어 있고, 새 데이터를 포함한 사용량이 이를 초과할 경우
        사용량이 한도 내로 떨어질 때까지 LRU 리스트의 뒤쪽 노드부터 차례로 삭제(Eviction)합니다.
        """
        # - SET key value
        # -성공시 ok
        # -메모리 초과시 LRU제거 수행
        # -기존키를 덮어쓰는경우: 기존 TTL은 "초기화(삭제)"

        # - LRU제거 규칙
        # -maxmemory>0
        # -SET이후 used_memory 가 maxmemory를 초과하면 used_memory가 maxmemory 이하가 될떄까지 LRU로 제거
        # -제거된 키는 evicted_keys에 누적
        # - 단일 엔트리가 maxmemory를 초과-> 저장x, oom에러 출력
        if len(args) != 2:
            return "(error) ERR wrong number of arguments for 'SET' command"
        key, value = args[0], args[1]
        self._evict_expired()
        new_size = self._byte_size(key, value)

        # [엣지케이스 방어] 새로 삽입하려는 데이터의 크기가 maxmemory 한도보다 크다면,
        # 기존 데이터를 삭제(Evict)하지 않고 즉시 OOM 에러를 반환하여 데이터를 보호합니다.
        if self._maxmemory > 0 and new_size > self._maxmemory:
            return "(error) OOM command not allowed when used_memory > 'maxmemory'"

        if self._store.contains(key):
            old_node = self._store.get(key)
            if old_node:
                old_size = self._byte_size(key, old_node.data[1])
            self._lru_list.remove_node(old_node)
            self._store.remove(key)
            self._used_memory -= old_size

        if self._maxmemory > 0:
            while self._used_memory + new_size > self._maxmemory:
                evicted = self._lru_list.remove_back()
                if evicted is None:
                    return "(error) OOM command not allowed when used_memory > 'maxmemory'"
                self._store.remove(evicted.data[0])
                self._used_memory -= self._byte_size(
                    evicted.data[0], evicted.data[1])
                self._evicted_keys += 1

        node = Node((key, value))
        self._lru_list.insert_front(node)
        self._store.put(key, node)
        self._used_memory += new_size
        return "OK"

    def get(self, args):
        """
        지정된 key의 value를 조회합니다.
        조회에 성공할 경우, 해당 노드를 LRU 리스트의 맨 앞으로 이동시켜 참조 순위를 갱신합니다.
        존재하지 않거나 이미 만료된 키일 경우 'nil'을 반환합니다.
        """
        # - GET key
        # -키가 없거나 만료 (nil)
        # -존재하는경우 "value"형태로 반환
        # -반환이 성공한 경우 LRU갱신

        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'GET' command"
        key = args[0]
        self._evict_expired()
        node = self._store.get(key)
        if node is None:
            return "(nil)"
        self._lru_list.move_to_front(node)
        return f'"{node.data[1]}"'

    def delete(self, args):

        # - DEL key
        # -삭제 성공 (integer)1, 없으면 (integer) 0
        # -삭제시 LRU/TTL관련 구조에서도 해당 엔트리를 함께 제거
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'DEL' command"
        key = args[0]
        self._evict_expired()
        return "(integer) 1" if self._delete_key(key) else "(integer) 0"

    def exists(self, args):

        # - EXIST key
        # -존재하면 (integer1), 없으면 (integer) 0
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'EXISTS' command"
        key = args[0]
        self._evict_expired()
        return "(integer) 1" if self._store.contains(key) else "(integer) 0"

    def dbsize(self, args):

        # - DBSIZE
        # -현재 저장된 키 개수를 (integer)N으로 반환
        if args:
            return "(error) ERR wrong number of arguments for 'DBSIZE' command"
        self._evict_expired()
        return f"(integer) {self._store.size()}"

    def keys(self, args):

        # - KEYS
        # - 전체 키 목록을 배열 형태로 출력(정렬은 필요 X)
        # - 키가 없으면 (empty array)로 표시가능
        if args:
            return "(error) ERR wrong number of arguments for 'KEYS' command"
        self._evict_expired()
        all_keys = self._store.keys()
        if not all_keys:
            return "(empty array)"
        return '\n'.join(f'{i + 1}. "{k}"' for i, k in enumerate(all_keys))

    def config(self, args):

        # - CONFIG SET maxmemory bytes
        # -bytes는 0이상 정수
        # -0은 무제한으로 간주
        # - 성공시 OK, 정수 파싱 실패시 에러표준
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

    def info(self, args):
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'INFO' command"
        if args[0].lower() != 'memory':
            return f"(error) ERR unknown INFO section '{args[0]}'"
        return (
            f"used_memory:{self._used_memory}\n"
            f"maxmemory:{self._maxmemory}\n"
            f"evicted_keys:{self._evicted_keys}"
        )
        # -used_memory:<number>
        # -maxmemory:<number>
        # -victed_keys:<number>a

    def expire(self, args):
        """
        특정 key에 대한 만료 시간(초 단위)을 설정합니다.
        설정된 만료 시각(현재시간 + 초) 정보는 최소 힙(self._ttl_heap)에 저장되어
        주기적으로 혹은 lazy-deletion 시점에 만료 판정 기준으로 쓰입니다.
        만약 입력된 초(seconds)가 0 이하일 경우 즉시 만료되어 키를 삭제합니다.
        """
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
        if node:
            node.expire_at = expire_at
        self._ttl_heap.push((expire_at, key))
        return "(integer) 1"
        # - EXPIRE key seconds
        # -key없으면 (integer)0
        # -seconds가 0 이하라면 "즉시만료"처리 가능
        # -정상설정시 (integer)1

    def ttl(self, args):
        """
        특정 key의 남은 수명(TTL, Time To Live)을 초 단위로 반환합니다.
        키가 존재하지 않거나 이미 만료된 경우 -2를 반환하고,
        키는 존재하지만 만료 시간이 지정되어 있지 않은 경우 -1을 반환합니다.
        """
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
        # - TTL key
        # -key가 없으면 (integer)-2
        # -key는 존재하시만 만료시간이 없으면 (integer)-1
        # -만료시간이 있으면 남은초를 (integer)N으로 반환
    
    def help(self, args):
        return HELP_TEXT
