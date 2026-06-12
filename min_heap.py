"""배열 기반 최소힙 - TTL 만료 시각 관리용.

요소: (expire_at: float, key: str)
expire_at 기준 최솟값이 루트. 스탈 엔트리는 pop 시점에 호출자가 처리.
"""


class MinHeap:
    """배열 기반 최소힙"""

    def __init__(self):
        self._data = []

    def push(self, expire_at, key):
        """(expire_at, key) 삽입"""
        self._data.append((expire_at, key))
        self._heapify_up(len(self._data) - 1)

    def pop(self):
        """최솟값(가장 빨리 만료) 추출. 비어있으면 None"""
        if not self._data:
            return None
        self._data[0], self._data[-1] = self._data[-1], self._data[0]
        val = self._data.pop()
        if self._data:
            self._heapify_down(0)
        return val

    def peek(self):
        """최솟값 조회 (제거 안 함). 비어있으면 None"""
        return self._data[0] if self._data else None

    def size(self):
        return len(self._data)

    # ── 내부 ──────────────────────────────────────────────

    def _heapify_up(self, idx):
        """삽입 후 힙 속성 복구 (아래→위)"""
        while idx > 0:
            parent = (idx - 1) // 2
            if self._data[idx][0] < self._data[parent][0]:
                self._data[idx], self._data[parent] = self._data[parent], self._data[idx]
                idx = parent
            else:
                break

    def _heapify_down(self, idx):
        """추출 후 힙 속성 복구 (위→아래)"""
        n = len(self._data)
        while True:
            smallest = idx
            left = 2 * idx + 1
            right = 2 * idx + 2
            if left < n and self._data[left][0] < self._data[smallest][0]:
                smallest = left
            if right < n and self._data[right][0] < self._data[smallest][0]:
                smallest = right
            if smallest == idx:
                break
            self._data[idx], self._data[smallest] = self._data[smallest], self._data[idx]
            idx = smallest
