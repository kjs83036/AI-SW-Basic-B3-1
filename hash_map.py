from doubly_linked_list import Doubly_linked_list, Node

class Hash_map:
    # 충돌해결은 체이닝방식으로 구현(이중연결리스트 재사용)
    # 로드팩터는 0.75초과시 버킷 2배 확장
    def __init__(self, base_size: int = 10):
        self.hashmap_size = base_size
        self.table = [Doubly_linked_list() for _ in range(self.hashmap_size)]
        self.entry_count = 0

    def hash_func(self, string):
        # 해시알고리즘
        # 1. 초기값으로 소수(5381)를 설정
        hash_value = 5381

        for char in string:
            # hash_value * 17 + ord(char)를 비트 연산으로 빠르게 처리(DJB2 약간 수정)
            hash_value = ((hash_value << 4) + hash_value) + ord(char)

            # 32비트 정수 범위를 유지하기 위한 마스킹
            hash_value &= 0xFFFFFFFF

        return hash_value

    def _hash(self, key):
        hashed_key = self.hash_func(str(key))
        return hashed_key % self.hashmap_size

    def _resize(self):
        old_table = self.table
        self.hashmap_size *= 2
        self.table = [Doubly_linked_list() for _ in range(self.hashmap_size)]
        self.entry_count = 0

        # for bucket in old_table:
        #     current = bucket.head
        #     while current:
        #         k, v = current.data
        #         self.put(k, v, disable_resize=True)
        #         current = current.next
        for bucket in old_table:
            # 구현된 __iter__를 사용하여 안전하고 간결하게 순회
            for node in bucket:
                k, v = node.data
                self.put(k, v, disable_resize=True)
            # bucket.head = None
            # bucket.tail = None

    def put(self, key, value, disable_resize=False):
        """
        해시맵에 (key, value) 쌍을 추가하거나 기존 값을 갱신합니다.
        체이닝 버킷의 이중 연결 리스트 뒤쪽에 삽입하며,
        로드 팩터가 0.75를 초과하면 해시 테이블 크기를 2배로 확장(Resize)합니다.
        """
        hash_index = self._hash(key)
        bucket = self.table[hash_index]

        # 🟢 리사이징 중이 아닐 때만 중복 키 체크 및 업데이트 수행
        if not disable_resize:
            current = bucket.head
            while current:
                if current.data[0] == key:
                    current.data = (key, value)
                    return "update"
                current = current.next

        # 리사이징 중이거나 신규 데이터인 경우 바로 삽입
        bucket.insert_back(Node((key, value)))
        self.entry_count += 1

        if not disable_resize and self.entry_count / self.hashmap_size > 0.75:
            self._resize()
        return "add"

    def get(self, key):
        """
        주어진 key가 속한 해시 버킷(이중 연결 리스트)을 탐색하여,
        일치하는 key의 실제 value(Node 객체 등)를 반환합니다.
        """
        hash_index = self._hash(key)
        bucket = self.table[hash_index]
        current = bucket.head
        while current:
            if current.data[0] == key:
                return current.data[1]
            current = current.next
        # for node in bucket:
        #     if node.data[0] == key:
        #         return node.data[1]
        return None

    def remove(self, key):
        """
        주어진 key가 속한 해시 버킷에서 해당 노드를 찾아 완전히 삭제합니다.
        이중 연결 리스트의 remove_node 헬퍼 메서드를 호출하여 체인을 안전하게 유지합니다.
        """
        hash_index = self._hash(key)
        bucket = self.table[hash_index]

        current = bucket.head
        while current:
            if current.data[0] == key:
                bucket.remove_node(current)
                self.entry_count -= 1
                return True
            current = current.next
        return False

    def contains(self, key):
        hash_index = self._hash(key)
        bucket = self.table[hash_index]

        current = bucket.head
        while current:
            if current.data[0] == key:
                return True
            current = current.next

        return False

    def keys(self):
        key_list = []
        for b in self.table:
            for node in b:
                key_list.append(node.data[0])
        return key_list

    def size(self):
        return self.entry_count