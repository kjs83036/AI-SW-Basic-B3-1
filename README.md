# Custom Mini Redis (In-Memory Key-Value Store)

파이썬의 내장 Key-Value 자료형(`dict`, `set`, `collections`)을 전혀 사용하지 않고, 직접 구현한 **이중 연결 리스트(Doubly Linked List)**, **해시맵(HashMap)**, **최소 힙(Min Heap)**을 사용하여 설계한 CLI 기반 인메모리 데이터 저장소입니다.

본 프로젝트는 메모리 제한 환경에서의 **LRU 캐시 교체 알고리즘**과 힙을 활용한 **TTL(Time-To-Live) 지연 만료 삭제(Lazy Deletion)** 동작 원리를 바닥부터 설계하여 자료구조와 알고리즘의 동작을 깊이 이해할 수 있도록 구현되었습니다.

---

## 1. 파일 구조 및 역할

| 파일명 | 역할 | 상세 설명 |
| :--- | :--- | :--- |
| [**`main.py`**](file:///Users/kotaro83038303/.CMVolumes/프로트수/codyssey/antigravity/B3-1-2/last_output/mini_redis/main.py) | **CLI REPL 진입점** | 사용자의 콘솔 입력을 받아 파싱 및 토큰화하고, 해당 명령어를 Redis 핵심 컨트롤러로 라우팅하는 무한 루프 환경을 실행합니다. |
| [**`mini_redis.py`**](file:///Users/kotaro83038303/.CMVolumes/프로트수/codyssey/antigravity/B3-1-2/last_output/mini_redis/mini_redis.py) | **Redis 핵심 컨트롤러** | 해시맵, 이중 연결 리스트, 최소 힙을 총괄하여 데이터베이스 동작 및 명령어를 실행하고, 메모리 제한 및 만료 라이프사이클을 제어합니다. |
| [**`hash_map.py`**](file:///Users/kotaro83038303/.CMVolumes/프로트수/codyssey/antigravity/B3-1-2/last_output/mini_redis/hash_map.py) | **배열 기반 체이닝 해시맵** | 고정 크기 배열 내에서 커스텀 해시 함수(DJB2 기반)를 사용해 인덱스를 얻고, 충돌 시 이중 연결 리스트를 활용한 체이닝 방식으로 해결합니다. 로드 팩터가 **0.75 초과 시 버킷 크기를 2배 확장하고 재해싱(`_resize`)**합니다. |
| [**`doubly_linked_list.py`**](file:///Users/kotaro83038303/.CMVolumes/프로트수/codyssey/antigravity/B3-1-2/last_output/mini_redis/doubly_linked_list.py) | **이중 연결 리스트** | 노드 간 `prev`/`next` 연결 관계를 관리합니다. LRU 우선순위 갱신 및 만료/퇴출 시 임의 노드를 **\(O(1)\)**에 신속하게 격리 및 삽입할 수 있는 포인터 연산을 담당합니다. |
| [**`min_heap.py`**](file:///Users/kotaro83038303/.CMVolumes/프로트수/codyssey/antigravity/B3-1-2/last_output/mini_redis/min_heap.py) | **최소 힙 (이진 힙)** | 1차원 동적 배열상에서 부모/자식 간 인덱스 연산으로 트리 구조를 모사하여 `_heapify_up`/`_heapify_down`을 통해 `(expire_at, key)` 요소를 만료 시간 기준으로 정렬 및 추출합니다. |
| [**`srs.md`**](file:///Users/kotaro83038303/.CMVolumes/프로트수/codyssey/antigravity/B3-1-2/last_output/mini_redis/srs.md) | **요구사항 정의서** | 과제의 공통 요구사항, 예외 조건, 엣지 케이스별 처리 기준을 서술해둔 참조 문서입니다. |

---

## 2. 주요 핵심 설계 아키텍처

```
             ┌───────────────── [ main.py (REPL CLI) ] ─────────────────┐
                                          │
                                   (Command Input)
                                          ▼
             ┌───────────── [ mini_redis.py (MiniRedis) ] ──────────────┐
             │                            │                             │
             │               (Lazy Deletion - Peek/Pop)                 │
             │                            ▼                             │
             │              ┌───────────────────────────┐               │
             │              │   min_heap.py (MinHeap)   │               │
             │              └───────────────────────────┘               │
             │                            │                             │
    (Key Lookup / Contains)               │ (O(1) Access)         (LRU Priority)
             │                            ▼                             │
             ▼              ┌───────────────────────────┐               ▼
    ┌───────────────────┐   │   doubly_linked_list.py   │   ┌───────────────────┐
    │    hash_map.py    │ ──┼─> (DoublyLinkedList Node) │ <─│     LRU List      │
    │     (HashMap)     │   │     (key, value, exp)     │   │(Head=Hot,Tail=Old)│
    └───────────────────┘   └───────────────────────────┘   └───────────────────┘
```

1. **\(O(1)\) 시간 복잡도 LRU 연산**:
   * HashMap의 버킷 노드 데이터(`Value`)로 Doubly Linked List의 `Node` 메모리 주소를 저장합니다.
   * 이를 통해 별도의 리스트 탐색 순회 없이 해시 조회 한 번만으로 Node 포인터를 직접 획득하여 \(O(1)\) 내에 리스트 양옆 링크를 끊고 앞(`head` 뒤)으로 옮기는 `move_to_front` 갱신을 완료합니다.
2. **지연 만료 삭제 (Lazy Deletion) & 스탈 엔트리(Stale Entry) 제어**:
   * 만료 시간의 관리는 최소 힙(Min Heap)에 `(expire_at, key)` 형태로 정렬 배치합니다.
   * 성능 낭비를 유발하는 타이머/백그라운드 스레드 대신, 매 명령 실행 직전에 힙의 최상단을 스캔해 만료된 키들을 제거합니다.
   * `SET` 등으로 만료 시각이 갱신되어 힙 내부에 예전 만료 정보가 중복으로 남아있는 스탈 엔트리 문제는, 실제 노드의 `expire_at` 값과 힙 요소 값을 비교 검증하여 잘못된 조기 삭제를 막아줍니다.

---

## 3. 지원 명령어 목록

### ① String 기본 명령어
* **`SET key value`**
  * 키-값 데이터를 데이터베이스에 기록합니다. (성공 시 `OK` 반환)
  * 새로운 데이터 기록으로 메모리 한도가 초과될 경우, 가장 오래 사용되지 않은 키(LRU tail 노드)를 한도 범위 내에 들어올 때까지 순차 제거합니다.
  * 기존 키를 덮어쓰는(Overwrite) 경우, 해당 키의 기존 만료 시간(TTL) 정보는 자동으로 초기화 및 소멸됩니다.
* **`GET key`**
  * 지정한 키의 값을 조회합니다.
  * 키가 없거나 만료 기한이 지났다면 `nil`을 반환합니다.
  * 조회 성공 시 해당 데이터 노드의 사용 순위를 이중 연결 리스트 최상단(`head` 방향)으로 갱신합니다.
* **`DEL key`**
  * 키를 즉시 삭제합니다. 삭제 성공 시 `(integer) 1`, 데이터가 없으면 `(integer) 0`을 반환합니다.
  * 삭제 시 HashMap 데이터는 물론 LRU 순위 리스트 및 TTL 최소 힙과의 연결 구조도 모두 안전하게 분리 및 해제합니다.
* **`EXISTS key`**
  * 키의 존재 여부를 반환합니다. (있으면 `(integer) 1`, 없으면 `(integer) 0`)
* **`DBSIZE`**
  * 만료되지 않고 현재 저장되어 있는 순수 활성 키의 개수를 `(integer) N` 포맷으로 반환합니다.
* **`KEYS`**
  * 저장된 모든 키를 1차원 목록 배열 형태로 출력합니다. (정렬 순서 없음)
  * 저장된 데이터가 존재하지 않는다면 `(empty array)`를 출력합니다.

### ② 메모리 제어 명령어
* **`CONFIG SET maxmemory <bytes>`**
  * Mini Redis가 사용할 수 있는 최대 가용 메모리 상한선(바이트 단위)을 설정합니다. (성공 시 `OK`)
  * `0`을 인자로 주면 메모리를 무제한으로 사용하겠다는 의미가 됩니다.
  * 정수로 파싱 불가능한 값이 들어오거나 음수가 들어오는 경우, 자료구조 범위 검증 에러를 출력합니다.
* **`INFO memory`**
  * 현재 데이터베이스의 메모리 현황 정보를 출력합니다.
  * 출력 포맷:
    ```text
    used_memory:<현재_바이트_사용량>
    maxmemory:<설정된_최대_허용량>
    evicted_keys:<메모리_초과로_제거된_키_누적_개수>
    ```
  * *used_memory 계산 방식*: 데이터 오버헤드를 제외한 \(len(\text{UTF-8}(key)) + len(\text{UTF-8}(value))\)의 누적 총합입니다.

### ③ TTL (만료 시간) 제어 명령어
* **`EXPIRE key seconds`**
  * 특정 키의 만료 시간을 설정(초 단위)합니다.
  * 키가 없으면 `(integer) 0`을 반환하고, 성공하면 `(integer) 1`을 반환합니다.
  * 만약 인자로 넘긴 `seconds`가 `0` 이하의 정수라면, 해당 키를 즉시 만료 및 완전 삭제합니다.
* **`TTL key`**
  * 키의 남은 유효 시간을 조회합니다.
  * 키 자체가 없거나 만료되어 소멸된 상태인 경우 `(integer) -2`를 반환합니다.
  * 키는 존재하지만 만료 한계 시간(TTL)이 설정되지 않은 무제한 데이터인 경우 `(integer) -1`을 반환합니다.
  * 만료 시간이 남아있다면 남은 시간(초)을 `(integer) N` 형태로 반환합니다.

### ④ 유틸리티 명령어
* **`HELP`**
  * 전체 지원 명령어에 대한 도움말 사용법 가이드를 텍스트로 출력합니다.
* **`exit` / `quit`**
  * CLI 프로그램 실행 루프를 안전하게 종료하고 빠져나갑니다.

---

## 4. 표준 에러 포맷

예외적인 호출이나 인자 개수 오류 등 비정상 동작 발생 시 Redis 공식 사양에 맞춘 다음과 같은 에러 규격 메시지를 반환합니다.

* **존재하지 않는 명령 입력**: `(error) ERR unknown command '<명령어>'`
* **인자 개수가 불일치할 때**: `(error) ERR wrong number of arguments for '<명령어>' command`
* **정수 변환 실패 및 범위 초과**: `(error) ERR value is not an integer or out of range`
* **새 데이터가 전체 메모리 한도를 초과할 때(OOM)**: `(error) OOM command not allowed when used_memory > 'maxmemory'`

---

## 5. 실행 방법

1. Python 3.8 이상이 설치되어 있는지 확인합니다.
2. 터미널에서 프로젝트 루트 디렉토리로 이동하여 아래 명령어를 실행합니다.
   ```bash
   python3 main.py
   ```
3. 나타나는 `mini-redis>` 프롬프트 상에서 명령어를 자유롭게 실행해 볼 수 있습니다.
   ```text
   mini-redis> CONFIG SET maxmemory 30
   OK
   mini-redis> SET user:1 "Alice"
   OK
   mini-redis> SET user:2 "Bob"
   OK
   mini-redis> SET user:3 "Charlie"
   OK
   mini-redis> GET user:1
   nil
   mini-redis> INFO memory
   used_memory:22
   maxmemory:30
   evicted_keys:1
   mini-redis> KEYS
   1. "user:3"
   2. "user:2"
   ```
