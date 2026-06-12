# Mini Redis 구축

## 개요

Python에서 `dict`/`set`/`collections`를 사용하지 않고, 배열 기반 해시맵·이중 연결 리스트·최소힙을 직접 구현하여 CLI 기반 Mini Redis를 구축한다. LRU 메모리 관리와 TTL lazy-deletion을 지원한다.

## 실행 방법

```bash
cd output_MiniRedis구축
python main.py
```

```
mini-redis> SET user:1 "Alice"
OK
mini-redis> GET user:1
"Alice"
mini-redis> exit
```

## 파일

| 파일 | 역할 |
|------|------|
| `main.py` | CLI 진입점, REPL 루프 |
| `mini_redis.py` | 명령어 파싱·실행, 자료구조 조율 |
| `hash_map.py` | 배열+선형탐사 해시맵 (dict 대체) |
| `linked_list.py` | 이중 연결 리스트 (LRU 순서) |
| `min_heap.py` | 최소힙 (TTL 만료 관리) |
| `architecture.md` | Mermaid 구조도 |
| `EXPLANATION.md` | 코드리뷰 수준 통합 설명 |
| `MANUAL_VERIFICATION.md` | 수동 검증 가이드 |
| `README.md` | 본 문서 |

## 지원 명령어

| 명령어 | 설명 |
|--------|------|
| `SET key value` | 키-값 저장 (maxmemory 초과 시 LRU 제거) |
| `GET key` | 값 조회 |
| `DEL key` | 키 삭제 |
| `EXISTS key` | 존재 여부 확인 |
| `DBSIZE` | 저장된 키 수 |
| `KEYS` | 전체 키 목록 |
| `CONFIG SET maxmemory N` | 최대 메모리 설정 (0 = 무제한) |
| `INFO memory` | 메모리 사용량 조회 |
| `EXPIRE key N` | TTL 설정 (초) |
| `TTL key` | 남은 만료 시간 조회 |
| `exit` / `quit` | 종료 |

## 결과 요약

- PDF 8페이지 예시 입출력 전부 일치
- 에러 메시지 형식 (`ERR`, `OOM`) 일치
- TTL lazy-deletion 동작 확인 (1초 대기 후 키 자동 삭제)
- `dict`/`set`/`collections` 미사용, 각 자료구조 독립 모듈 분리
