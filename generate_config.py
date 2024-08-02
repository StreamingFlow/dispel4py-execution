import os

def generate_config():
    multi_num = os.getenv('MULTI_NUM', '10')
    multi_iter = os.getenv('MULTI_ITERATIONS', '10')
    multi_simple = os.getenv('MULTI_SIMPLE', 'False')
    dynamic_num = os.getenv('DYNAMIC_NUM', '10')
    dynamic_iter = os.getenv('DYNAMIC_ITER', '10')
    dynamic_simple = os.getenv('DYNAMIC_SIMPLE', 'False')
    redis_ip = os.getenv('REDIS_IP', 'localhost')
    redis_port = os.getenv('REDIS_PORT', '6379')

    config_content = f"""
[MULTI]
num = {multi_num}
iter = {multi_iter}
simple = {multi_simple}

[DYNAMIC]
num = {dynamic_num}
iter = {dynamic_iter}
simple = {dynamic_simple}
redis_ip = {redis_ip}
redis_port = {redis_port}
"""

    with open('config.ini', 'w') as config_file:
        config_file.write(config_content.strip())

if __name__ == "__main__":
    generate_config()
    print("config.ini generated successfully")

