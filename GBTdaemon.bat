@echo off
REM ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
REM GBTdaemon.bat — GBT自主神经系统 · 光纤模式
REM 放入 Windows 启动文件夹: Win+R → shell:startup → 粘贴快捷方式
REM
REM 光纤传输: 不等待，不间隔，持续高速传输
REM   触手: 扫描完成立即开始下一次
REM   视觉: 截图完成立即开始下一次
REM   邻域: 实时注入
REM
REM 日志: %%USERPROFILE%%\.gbt\neural_tentacle\

cd /d "%~dp0"

echo =========================================
echo   GBT 小土豆 · 自主神经系统 v5.0
echo   光纤模式 - 零延迟连续传输
echo =========================================
echo.

python -c "
import sys, time, threading
sys.path.insert(0, '.')

from brain.neural_tentacle import NeuralTentacle
from brain.host_body import eyes

tentacle = NeuralTentacle(auto_heal=True)
running = True
stats = {'scans': 0, 'visions': 0, 'errors_found': 0, 'errors_fixed': 0, 'start': time.time()}

def tentacle_fiber():
    '''触手光纤 - 扫描完立刻下一次，不等'''
    while running:
        t0 = time.time()
        try:
            r = tentacle.pulse()
            stats['scans'] += 1
            stats['errors_found'] += r.get('total_errors', 0)
            stats['errors_fixed'] += r.get('fixes_applied', 0)
            elapsed = time.time() - t0
            print(f'[T{stats[\"scans\"]}] err={r[\"total_errors\"]} healed={r[\"fixes_applied\"]} | {elapsed:.1f}s')
        except Exception as e:
            print(f'[T] error: {e}')
        # 零延迟 - 立即下一轮

def vision_fiber():
    '''视觉光纤 - 截图完立刻下一次'''
    while running:
        t0 = time.time()
        try:
            screen = eyes.see()
            if screen.get('ok'):
                eyes.to_image()
                stats['visions'] += 1
                elapsed = time.time() - t0
                print(f'[V{stats[\"visions\"]}] {screen[\"size\"][0]}x{screen[\"size\"][1]}px | {elapsed:.1f}s')
        except Exception as e:
            print(f'[V] error: {e}')

# 启动光纤线程
t1 = threading.Thread(target=tentacle_fiber, daemon=True)
t2 = threading.Thread(target=vision_fiber, daemon=True)
t1.start()
t2.start()

print('FIBER ACTIVE - zero delay transmission')
print()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    running = False
    total = time.time() - stats['start']
    print()
    print(f'Fiber suspended. {stats[\"scans\"]} scans, {stats[\"visions\"]} captures in {total:.0f}s')
"

pause
