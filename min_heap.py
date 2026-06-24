from typing import Optional, Tuple


class Min_heap:

    def __init__(self):
        self.heap = []

    def _heapify_up(self, index):
        while index > 0:
            # 현재 노드의 부모 노드 인덱스를 계산합니다.
            parent_index = (index - 1) // 2
            # 조건: 만약 현재 노드의 값 < 부모 노드의 값이라면, 두 값의 위치를 바꿉니다(swap).
            if self.heap[index] < self.heap[parent_index]:
                self.heap[index], self.heap[parent_index] = self.heap[parent_index], self.heap[index]
            # 위치를 바꾼 후, 현재 index를 부모의 index로 갱신하여 계속 위로 올라갑니다.
                index = parent_index
            # 만약 부모가 더 작다면 힙 구조가 만족된 것이므로 루프를 탈출(break)합니다.
            else:
                break

    def _heapify_down(self, index):
        total_elements = len(self.heap)

        # 왼쪽 자식의 인덱스가 힙의 크기보다 작을 때까지(len(self.heap)) while 루프를 돕니다. (자식이 없으면 멈춤)
        while (2*index + 1) < total_elements:
            # 왼쪽 자식과 오른쪽 자식(존재하는지 확인 필요) 중 더 작은 값을 가진 자식의 인덱스를 찾습니다.
            left_child = 2*index + 1
            right_child = 2*index + 2
            smallest = left_child

            if right_child < total_elements and self.heap[right_child] < self.heap[left_child]:
                smallest = right_child
        # 조건: 만약 현재 노드의 값 > 가장 작은 자식 노드의 값이라면, 두 값의 위치를 바꿉니다(swap).
            if self.heap[index] > self.heap[smallest]:
                self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
                index = smallest
        # 위치를 바꾼 후, 현재 index를 해당 자식의 index로 갱신하여 아래로 내려갑니다.
            else:
                break
        # 만약 현재 노드가 자식들보다 작다면 힙 구조가 만족된 것이므로 루프를 탈출(break)합니다.

    def push(self, data):
        """
        새로운 (expire_at, key) 만료 정보를 힙의 끝에 추가한 후, 
        상향식 힙 구조 정렬(_heapify_up)을 진행하여 최소 힙 구조를 유지합니다.
        """
        self.heap.append(data)
        self._heapify_up(len(self.heap) - 1)

    def pop(self):
        """
        만료일이 가장 빠른 최상단(루트 노드)의 만료 정보를 제거 및 추출합니다.
        마지막 노드를 최상단으로 옮긴 후, 하향식 힙 구조 정렬(_heapify_down)을 진행해 구조를 재조정합니다.
        """
        if len(self.heap) == 0:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        result = self.heap[0]

        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return result

    def peek(self) -> Optional[Tuple]:
        if len(self.heap) == 0:
            return None
        return self.heap[0]

    def size(self):
        return len(self.heap)
