from mini_redis import MiniRedis


def run():
    """
    Mini-Redis의 대화형 CLI(REPL) 환경을 실행하는 메인 루프입니다.
    사용자의 입력을 받고, 종료 명령('quit', 'exit')을 감지하며, 
    생성된 단일 MiniRedis 인스턴스를 계속 유지하면서 명령어를 실행합니다.
    """
    mini_redis = MiniRedis()
    while True:

        try:
            line = input('mini-redis> ').strip()
        except EOFError:
            break
        if not line:
            continue
        if line.lower() in ('quit' , 'exit'):
            break
        result = excute(line, mini_redis)
        if result:
            print(result)

def tokenizer(line):
    """
    입력된 한 줄의 문자열 명령어를 파싱하여 토큰 리스트로 변환합니다.
    공백을 기준으로 자르되, 큰따옴표("") 내부의 공백은 하나의 토큰으로 취급하고,
    빈 문자열("") 도 생략하지 않고 정상적인 토큰으로 파싱되도록 상태 머신 방식으로 처리합니다.
    """
    tokens = []
    current = []
    have_quote = False

    for ch in line:
        if ch == '"':
            have_quote = not have_quote
             # 2. 따옴표가 닫히는 시점에 내부에 있던 문자열(빈 문자열 포함)을 토큰으로 즉시 확정
            if not have_quote:
                tokens.append(''.join(current))
                current = []
        elif ch ==' ' and not have_quote:
            if current:
                tokens.append(''.join(current))
                current = []
        else:
            current.append(ch)
    if current:
        tokens.append(''.join(current))
    
    return tokens
    

def excute(line, mini_redis):
    """
    문자열 입력을 토크나이징하고, 첫 번째 토큰인 명령어(Command)를 
    대문자로 변환하여 해당 Redis 기능 메서드로 안전하게 매핑(Dispatch) 및 호출합니다.
    존재하지 않는 명령어가 올 경우 알맞은 오류 메시지를 리턴합니다.
    """
    token = tokenizer(line)
    if not token:
        return None
    cmd = token[0].upper()
    args = token[1:]
    
    dispatch = {
            'SET':    mini_redis.set,
            'GET':    mini_redis.get,
            'DEL':    mini_redis.delete,
            'EXISTS': mini_redis.exists,
            'DBSIZE': mini_redis.dbsize,
            'KEYS':   mini_redis.keys,
            'CONFIG': mini_redis.config,
            'INFO':   mini_redis.info,
            'EXPIRE': mini_redis.expire,
            'TTL':    mini_redis.ttl,
            'HELP': mini_redis.help
        }
    if cmd in dispatch:
        return dispatch[cmd](args)
    return f"(error) ERR unknown command '{cmd}'"


if __name__ == "__main__":
    run()
