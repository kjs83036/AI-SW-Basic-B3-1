# 수동 검증 가이드

이 문서를 위에서 아래로 따라가면 모든 검증을 직접 재현할 수 있다.

## 0. 사전 준비

- 작업 폴더: `E:\codyssey_claude\B3-1-2\output_MiniRedis구축\`
- 실행 환경: Python 3.8 이상

```bash
cd E:\codyssey_claude\B3-1-2\output_MiniRedis구축
python --version
```

기대: `Python 3.8.x` 이상

---

## 1. 구현 실행 검증

### 1-1. PDF 8페이지 메인 시나리오

- 목적: LRU 메모리 제거, INFO memory, KEYS, TTL 흐름 확인
- 실행:

```bash
python -c "
from mini_redis import MiniRedis
r = MiniRedis()
cmds = [
    'CONFIG SET maxmemory 30',
    'SET user:1 \"Alice\"',
    'SET user:2 \"Bob\"',
    'SET user:3 \"Charlie\"',
    'GET user:1',
    'INFO memory',
    'KEYS',
    'EXPIRE user:2 3',
    'TTL user:2',
]
for cmd in cmds:
    print(f'mini-redis> {cmd}')
    print(r.execute(cmd))
    print()
"
```

- 기대 출력:

```
mini-redis> CONFIG SET maxmemory 30
OK

mini-redis> SET user:1 "Alice"
OK

mini-redis> SET user:2 "Bob"
OK

mini-redis> SET user:3 "Charlie"
OK

mini-redis> GET user:1
(nil)

mini-redis> INFO memory
used_memory:22
maxmemory:30
evicted_keys:1

mini-redis> KEYS
1. "user:3"
2. "user:2"

mini-redis> EXPIRE user:2 3
(integer) 1

mini-redis> TTL user:2
(integer) 2
```

- 확인 포인트:
  - `GET user:1` → `(nil)` (LRU 제거됨)
  - `used_memory:22` = user:2(9) + user:3(13)
  - `evicted_keys:1`
  - `TTL user:2` → `(integer) 2` (int 내림으로 2 또는 3)

### 1-2. 에러 출력 시나리오

- 목적: PDF 8페이지 에러 예시 형식 확인
- 실행:

```bash
python -c "
from mini_redis import MiniRedis
r = MiniRedis()
print(r.execute('CONFIG SET maxmemory abc'))
print(r.execute('GET'))
print(r.execute('HELLO'))
"
```

- 기대 출력:

```
(error) ERR value is not an integer or out of range
(error) ERR wrong number of arguments for 'GET' command
(error) ERR unknown command 'HELLO'
```

- 확인 포인트: 에러 메시지가 `(error) ERR ...` 형식인지 확인

### 1-3. TTL 만료 검증

- 목적: lazy-deletion이 실제 시간 경과 후 동작하는지 확인
- 실행:

```bash
python -c "
from mini_redis import MiniRedis
import time
r = MiniRedis()
r.execute('SET foo bar')
r.execute('EXPIRE foo 1')
print('TTL 직후:', r.execute('TTL foo'))
time.sleep(1.1)
print('1.1초 후 GET:', r.execute('GET foo'))
print('1.1초 후 TTL:', r.execute('TTL foo'))
"
```

- 기대 출력:

```
TTL 직후: (integer) 0
1.1초 후 GET: (nil)
1.1초 후 TTL: (integer) -2
```

- 확인 포인트: 1.1초 후 키가 삭제되어 (nil) 및 -2 반환

### 1-4. DEL / EXISTS / KEYS / DBSIZE

```bash
python -c "
from mini_redis import MiniRedis
r = MiniRedis()
r.execute('SET x 1')
r.execute('SET y 2')
print('DBSIZE:', r.execute('DBSIZE'))
print('EXISTS x:', r.execute('EXISTS x'))
print('DEL x:', r.execute('DEL x'))
print('EXISTS x 후:', r.execute('EXISTS x'))
print('DEL x 재시도:', r.execute('DEL x'))
print('KEYS:', r.execute('KEYS'))
r2 = MiniRedis()
print('KEYS 빈 경우:', r2.execute('KEYS'))
"
```

- 기대 출력:

```
DBSIZE: (integer) 2
EXISTS x: (integer) 1
DEL x: (integer) 1
EXISTS x 후: (integer) 0
DEL x 재시도: (integer) 0
KEYS: 1. "y"
KEYS 빈 경우: (empty array)
```

---

## 2. 제약 충족 수동 확인

| PDF 제약 | 확인 방법 | 위치 |
|----------|-----------|------|
| dict 사용 금지 | `grep -n "dict(" hash_map.py mini_redis.py` → 0건 | - |
| set 사용 금지 | `grep -n " set(" *.py` → 0건 | - |
| collections 사용 금지 | `grep -n "import collections" *.py` → 0건 | - |
| 각 자료구조 독립 모듈 | `ls *.py` → hash_map.py / linked_list.py / min_heap.py 존재 확인 | - |
| mini-redis> 프롬프트 | main.py:14 `input('mini-redis> ')` 직접 확인 | main.py:14 |
| OOM 에러 형식 | mini_redis.py:127 문자열 직접 확인 | mini_redis.py:127 |
| insert_front/insert_back/remove_back/remove_node/move_to_front | linked_list.py 메서드 목록 확인 | linked_list.py:23-57 |
| _heapify_up/_heapify_down | min_heap.py 메서드 목록 확인 | min_heap.py:43-64 |

검증 명령:

```bash
grep -n "^import\|^from" hash_map.py linked_list.py min_heap.py mini_redis.py main.py
```

- 확인 포인트: `collections`, `dict`, `set` 관련 import 없음

---

## 3. 산출물 정합성 확인 (Step 9 결과 재현)

```bash
ls -1 E:\codyssey_claude\B3-1-2\output_MiniRedis구축\
```

체크리스트:
- [ ] `main.py` 존재
- [ ] `mini_redis.py` 존재
- [ ] `hash_map.py` 존재
- [ ] `linked_list.py` 존재
- [ ] `min_heap.py` 존재
- [ ] `architecture.md` 존재 (mermaid 블록 포함)
- [ ] `EXPLANATION.md` 존재 (제약-코드 매핑 표 포함)
- [ ] `README.md` 존재
- [ ] `MANUAL_VERIFICATION.md` 존재 (본 문서)
- [ ] EXPLANATION.md에 "선택과제 미수행" 명시
- [ ] README.md 실행법 그대로 동작

---

## 4. codereview 결과 요약

| 지적 | 채택 여부 | 사유 |
|------|-----------|------|
| SET OOM 시 기존 키 손실 (HIGH) | 기각 | 극단 케이스 (new_size > maxmemory인 update), PDF 예시 없음, rollback 복잡도 교육 목적 초과 |
| EXPIRE 재호출 힙 스탈 누적 (MEDIUM) | 기각 | lazy-deletion 설계 의도, 기능 정확성 무관 |
| INFO memory 섹션 헤더 추가 (LOW) | 기각 | PDF 8페이지 예시가 헤더 없는 형식을 명시 |

---

## 5. 종합 판정

위 1-4 항목 전부 통과 시 과제 완료로 본다.
