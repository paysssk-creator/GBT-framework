import sys
from pathlib import Path


# ⛔ 思维导图驱动执行协议
# 每个任务必须:
# ① 生成思维导图 → ② 按导图执行 → ③ 卡点先搜索 → ④ 无方案再推理 → ⑤ 重新生成导图

def generate_mind_map(task_description, previous_results=None):
    """为任务生成精细思维导图"""
    import json
    # 搜索现有方案
    try:
        import subprocess
        r = subprocess.run([
            sys.executable, str(Path(__file__).parent.parent / 'caps' / 'web_search' / 'run.py'),
            'search', json.dumps({'query': task_description[:200], 'max_results': 5})
        ], capture_output=True, text=True, timeout=20)
        existing = json.loads(r.stdout).get('results', []) if r.stdout else []
    except:
        existing = []
    
    # 生成导图
    phases = []
    steps = task_description.split('→') if '→' in task_description else [task_description]
    for i, step in enumerate(steps):
        phase = {
            'id': f'p{i+1}',
            'step': step.strip()[:200],
            'existing_solutions': [e.get('title','')[:100] for e in existing[:2]],
            'status': 'pending',
            'sub_agents': []
        }
        phases.append(phase)
    
    return {
        'task': task_description[:200],
        'phases': phases,
        'total_phases': len(phases),
        'search_results': len(existing),
        'mode': 'search_first' if existing else 'reasoning_only'
    }
