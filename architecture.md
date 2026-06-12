# 구조도

```mermaid
flowchart TD
    User["사용자 입력"] --> main["main.py\nREPL 루프\nmini-redis> 프롬프트"]
    main --> execute["MiniRedis.execute()\n명령어 파싱·라우팅"]

    execute --> SET["_cmd_set\nLRU 제거 + 삽입"]
    execute --> GET["_cmd_get\nLRU 갱신"]
    execute --> DEL["_cmd_del\n키 삭제"]
    execute --> EXISTS["_cmd_exists"]
    execute --> DBSIZE["_cmd_dbsize"]
    execute --> KEYS["_cmd_keys"]
    execute --> CONFIG["_cmd_config\nmaxmemory 설정"]
    execute --> INFO["_cmd_info\nused_memory 조회"]
    execute --> EXPIRE["_cmd_expire\nTTL 힙 등록"]
    execute --> TTL["_cmd_ttl\n남은 시간 조회"]

    SET --> evict["_evict_expired()\nlazy-deletion"]
    GET --> evict
    DEL --> evict
    EXPIRE --> evict
    TTL --> evict

    SET --> delete_key["_delete_key()\nstore + lru + memory 동기화"]
    DEL --> delete_key
    evict --> delete_key

    subgraph 자료구조
        HashMap["hash_map.py\nHashMap\n배열+선형탐사\nkey → Node"]
        DLL["linked_list.py\nDoublyLinkedList\nLRU 순서\nhead ↔ [최신] ↔ [오래된] ↔ tail"]
        Heap["min_heap.py\nMinHeap\nexpire_at 기준 최소힙\n(expire_at, key)"]
    end

    SET --> HashMap
    SET --> DLL
    EXPIRE --> Heap
    evict --> Heap
    evict --> HashMap
    GET --> HashMap
    GET --> DLL
    delete_key --> HashMap
    delete_key --> DLL
```

## 모듈 역할 요약

| 파일 | 역할 |
|------|------|
| `main.py` | REPL 루프, `mini-redis> ` 프롬프트 |
| `mini_redis.py` | 명령어 파싱·실행, 세 자료구조 조율 |
| `hash_map.py` | O(1) 키 조회용 배열 기반 해시맵 |
| `linked_list.py` | LRU 순서 유지용 이중 연결 리스트 |
| `min_heap.py` | TTL 만료 순서 관리용 최소힙 |
