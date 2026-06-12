"""이중 연결 리스트 - LRU 캐시 순서 관리용"""


class Node:
    """이중 연결 리스트 노드"""

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None
        self.expire_at = None  # TTL 만료 시각 (없으면 None)


class DoublyLinkedList:
    """LRU 순서를 관리하는 이중 연결 리스트.

    head(더미) ↔ [최신] ↔ ... ↔ [가장 오래된] ↔ tail(더미)
    LRU 제거: tail.prev를 꺼낸다.
    """

    def __init__(self):
        # 경계 더미 노드 - 실제 데이터 없음
        self.head = Node(None, None)
        self.tail = Node(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head
        self._size = 0

    def insert_front(self, node):
        """head 바로 뒤(가장 최근 위치)에 노드 삽입"""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
        self._size += 1

    def insert_back(self, node):
        """tail 바로 앞(가장 오래된 위치)에 노드 삽입"""
        node.next = self.tail
        node.prev = self.tail.prev
        self.tail.prev.next = node
        self.tail.prev = node
        self._size += 1

    def remove_node(self, node):
        """임의 노드 연결 해제"""
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = None
        node.next = None
        self._size -= 1

    def remove_back(self):
        """LRU(가장 오래된) 노드 제거 후 반환. 비어있으면 None"""
        if self._size == 0:
            return None
        lru_node = self.tail.prev
        self.remove_node(lru_node)
        return lru_node

    def move_to_front(self, node):
        """최근 접근 갱신: 노드를 맨 앞으로 이동"""
        self.remove_node(node)
        self.insert_front(node)

    def size(self):
        return self._size
