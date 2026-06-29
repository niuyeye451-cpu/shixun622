import requests

base = 'http://localhost:8001'

tests = [
    ('GET', '/', {}),
    ('GET', '/api/v1/common/knowledge-graph/disease-graph?disease_name=感冒', {}),
    ('GET', '/api/v1/common/knowledge-graph/entities/search?keyword=感冒', {}),
    ('GET', '/api/v1/common/knowledge-graph/statistics', {}),
    ('GET', '/api/v1/common/knowledge-graph/labels', {}),
    ('GET', '/api/v1/common/knowledge-graph/relation-types', {}),
    ('GET', '/api/v1/llm/health', {}),
    ('POST', '/api/v1/llm/query', {'question': '感冒怎么治疗', 'user_type': 'patient'}),
    ('POST', '/api/v1/llm/graph-analysis', {'question': '糖尿病'}),
    ('POST', '/api/v1/llm/rag/search', {'query': '高血压'}),
    ('GET', '/api/v1/llm/symptom-diagnosis?symptoms=发热&symptoms=头痛&symptoms=咽痛', {}),
    ('GET', '/api/v1/llm/drug-recommendation?disease_name=感冒', {}),
]

print('=' * 70)
print('知识图谱与大模型接口测试')
print('=' * 70)

success = 0
failed = 0

for method, path, data in tests:
    try:
        if method == 'GET':
            resp = requests.get(base + path, timeout=30)
        else:
            resp = requests.post(base + path, json=data, timeout=30)
        
        result = resp.json()
        code = result.get('code', -1)
        
        if code == 200:
            print(f'✅ {method} {path}')
            success += 1
        else:
            print(f'❌ {method} {path}')
            print(f'   Status: {resp.status_code}')
            print(f'   Code: {code}')
            print(f'   Message: {result.get("message", "Unknown")}')
            failed += 1
            
    except Exception as e:
        print(f'❌ {method} {path}')
        print(f'   Exception: {e}')
        failed += 1

print('=' * 70)
print(f'测试结果: {success} 成功, {failed} 失败')
print('=' * 70)
