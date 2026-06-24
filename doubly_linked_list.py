from typing import Optional

class Node:
    def __init__(self, data):
        self.data = data
        self.prev: Optional["Node"] = None
        self.next: Optional["Node"] = None
        self.expire_at = None  # TTL 만료 시각 (없으면 None)


class Doubly_linked_list:

    def __init__(self) -> None:
        self.head: Optional["Node"] = None
        self.tail: Optional["Node"] = None
        self._size = 0

    def __iter__(self):
        current = self.head
        while current:
            yield current
            current = current.next

    def insert_front(self, node):
        """
        주어진 Node 객체를 리스트의 맨 앞(head)에 직접 연결하여 삽입합니다.
        LRU 정책에서 가장 최근에 추가/참조된 데이터를 헤드에 위치시킬 때 사용됩니다.
        """
        result = False

        if self.head:
            node.next = self.head
            self.head.prev = node
            self.head = node
            result = True
        else:
            self.head = node
            self.tail = node
            result = True
        self._size += 1
        return result

    def insert_back(self, node):
        result = False

        if self.tail:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
            result = True
        else:
            self.head = node
            self.tail = node
            result = True
        self._size += 1
        return result

    def remove_front(self):
        if not self.head:
            print("no data")
            return None

        removed_node = self.head
        if self.head == self.tail:  # 노드가 1개뿐인 경우
            self.head = None
            self.tail = None
        else:                      # 노드가 여러 개 있는 경우
            self.head = removed_node.next
            if self.head:
                self.head.prev = None

        # 완전히 고립시켜 메모리 누수 방지
        removed_node.next = None
        removed_node.prev = None
        self._size -= 1
        return removed_node

    def remove_back(self):

        if not self.tail:
            print("no data")
            return None

        removed_node = self.tail
        if self.head == self.tail:
            self.head = None
            self.tail = None
        else:
            self.tail = removed_node.prev
            if self.tail:
                self.tail.next = None

        removed_node.next = None
        removed_node.prev = None
        self._size -= 1
        return removed_node

    def remove_node(self, node):
        """
        리스트 내의 임의의 위치에 있는 노드를 안전하게 끊어내고 제거합니다.
        헤드/테일 노드일 때와 중간 노드일 때의 예외 처리를 수행하고 연결 관계를 보존합니다.
        """
        # 인자로 받은 node 자체의 유효성 검사 추가
        if not self.head or not node:
            print("no data")
            return None

        if self.head == node:
            return self.remove_front()
        if self.tail == node:
            return self.remove_back()

        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev

        node.next = None
        node.prev = None
        self._size -= 1

        return node

    def move_to_front(self, node):
        """
        이미 리스트에 존재하는 노드를 기존 연결 링크에서 끊어내어 맨 앞(head)으로 이동시킵니다.
        GET 조회나 SET 갱신으로 인한 LRU 순위 갱신 시 핵심적으로 사용됩니다.
        """
        if not self.head or self.head == node:
            return False

        # 1. 기존 위치에서 노드 끊어내기
        if node == self.tail:
            self.tail = node.prev
            if self.tail:
                self.tail.next = None
        else:
            # 중간 노드인 경우
            if node.prev:
                node.prev.next = node.next
            if node.next:
                node.next.prev = node.prev

        # 2. 맨 앞으로 보내기
        node.next = self.head
        node.prev = None
        if self.head:
            self.head.prev = node
        self.head = node

        return True