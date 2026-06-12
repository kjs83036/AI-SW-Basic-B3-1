"""Mini Redis CLI 진입점"""

import sys
from mini_redis import MiniRedis


def run():
    """mini-redis> 프롬프트 REPL"""
    redis = MiniRedis()
    while True:
        try:
            line = input('mini-redis> ').strip()
        except EOFError:
            break
        if not line:
            continue
        if line.lower() in ('exit', 'quit'):
            break
        result = redis.execute(line)
        if result is not None:
            print(result)


if __name__ == '__main__':
    run()
