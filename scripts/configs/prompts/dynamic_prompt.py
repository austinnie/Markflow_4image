# prompts/dynamic_prompt.py
# 这是一个“触发器”风格，用来告诉 cli.py 进入 Ollama 交互模式

STYLE = {
    "dynamic_prompt": {
        "folder": "Ollama动态生成",
        "strength": 0.35,
        
        # 这里的提示词完全不会被用到，因为会被 cli.py 拦截并替换
        "subjects": [
            "placeholder subject"
        ],
        
        "styles": [
            "placeholder style"
        ],
        
        "moods": [
            "placeholder mood"
        ],
        
        "content_texts": [] 
    }
}