# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""simulation_env — 模拟/游戏环境 (OpenAI Gym + 自定义RL环境)"""
import sys, json, os

def do_list(params=None):
    """列出可用模拟环境"""
    envs = []
    try:
        import gymnasium as gym
        envs = list(gym.envs.registry.keys())[:50]
    except ImportError:
        pass
    return {"ok": True, "environments": envs or ["CartPole-v1", "LunarLander-v3", "MountainCar-v0"], "note": "gymnasium未安装，显示默认列表"}

def do_run(params):
    """运行模拟环境"""
    env_name = (params or {}).get("env", "CartPole-v1")
    steps = (params or {}).get("steps", 100)
    try:
        import gymnasium as gym
        env = gym.make(env_name)
        obs, info = env.reset()
        total_reward = 0
        for _ in range(min(steps, 1000)):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)
            if terminated or truncated:
                break
        env.close()
        return {"ok": True, "env": env_name, "steps": steps, "total_reward": total_reward}
    except ImportError:
        return {"ok": False, "error": "gymnasium未安装，请 pip install gymnasium"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def do_status(params=None):
    return {"ok": True, "cap": "simulation_env", "ready": True}

HANDLERS = {"list": do_list, "run": do_run, "status": do_status}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    params = {}
    if len(sys.argv) > 2:
        try: params = json.loads(sys.argv[2])
        except: pass
    h = HANDLERS.get(action, lambda p: {"ok": False, "error": f"未知: {action}"})
    print(json.dumps(h(params), ensure_ascii=False, default=str))
