"""배열 기반 해시맵 - 선형 탐사(Linear Probing) 충돌 처리.

dict/set/collections 사용 금지 제약을 만족하기 위해 고정 크기 배열로 구현.
O(1) 평균 조회·삽입·삭제.  LRU Node를 값으로 저장해 O(1) LRU 추적 가능.
"""

_DELETED = object()  # 삭제 표시 센티넬 (tombstone)


class HashMap:
    """오픈 어드레싱(선형 탐사) 해시맵"""

    _LOAD_FACTOR = 0.7  # 이 비율 초과 시 2배 확장

    def __init__(self, capacity=64):
        self._capacity = capacity
        self._table = [None] * capacity
        self._size = 0

    # ── 내부 ──────────────────────────────────────────────

    def _hash(self, key):
        return hash(key) % self._capacity

    def _find_slot(self, key):
        """key가 있으면 (idx, True), 없으면 빈 슬롯 (idx, False) 반환"""
        idx = self._hash(key)
        first_deleted = None
        for _ in range(self._capacity):
            entry = self._table[idx]
            if entry is None:
                # 키 없음 확정 - 삽입 위치는 첫 DELETED 또는 현재 빈 슬롯
                return (first_deleted if first_deleted is not None else idx), False
            if entry is _DELETED:
                if first_deleted is None:
                    first_deleted = idx
            elif entry[0] == key:
                return idx, True
            idx = (idx + 1) % self._capacity
        return (first_deleted if first_deleted is not None else -1), False

    def _resize(self):
        """용량 2배 확장 후 재해싱"""
        old_table = self._table
        self._capacity *= 2
        self._table = [None] * self._capacity
        self._size = 0
        for entry in old_table:
            if entry is not None and entry is not _DELETED:
                self.put(entry[0], entry[1])

    # ── 공개 API ──────────────────────────────────────────

    def put(self, key, value):
        """key-value 삽입 또는 갱신"""
        if self._size >= self._capacity * self._LOAD_FACTOR:
            self._resize()
        idx, found = self._find_slot(key)
        if found:
            self._table[idx] = (key, value)
        else:
            self._table[idx] = (key, value)
            self._size += 1

    def get(self, key):
        """key에 해당하는 value 반환. 없으면 None"""
        idx, found = self._find_slot(key)
        if found:
            return self._table[idx][1]
        return None

    def contains(self, key):
        """key 존재 여부"""
        _, found = self._find_slot(key)
        return found

    def remove(self, key):
        """key 삭제. 삭제 성공 시 True"""
        idx, found = self._find_slot(key)
        if found:
            self._table[idx] = _DELETED
            self._size -= 1
            return True
        return False

    def keys(self):
        """저장된 모든 key 목록 반환 (순서 미보장)"""
        return [
            entry[0]
            for entry in self._table
            if entry is not None and entry is not _DELETED
        ]

    def size(self):
        return self._size
