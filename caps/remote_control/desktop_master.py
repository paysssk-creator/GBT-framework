# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
# desktop_master.py — 桌面操控大师
# 鼠标 · 键盘 · 截屏 · 窗口 · 剪贴板 · 进程
# ============================================================
"""GBT Desktop Master — Windows 桌面全操控"""

import subprocess, base64, time, json, re, sys
from pathlib import Path

ENCODING = 'gbk' if sys.platform == 'win32' else 'utf-8'
PS_INIT = """
    Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
    Add-Type -AssemblyName System.Drawing -ErrorAction SilentlyContinue
"""

def _ps(command, raw=False):
    full = PS_INIT + "\n" + command
    result = subprocess.run(
        ['powershell', '-NoProfile', '-Command', full],
        capture_output=True, text=True, timeout=15, encoding=ENCODING, errors='replace'
    )
    return result.stdout.strip() if raw else result

def _parse_kv(output):
    """解析 PowerShell Format-List 输出为 dict"""
    return dict(re.findall(r'(\w+)\s*:\s*(\S+)', output))

class Desktop:
    def __init__(self):
        pass

    # === 鼠标 ===
    def position(self):
        out = _ps("[System.Windows.Forms.Cursor]::Position | Format-List X,Y", raw=True)
        d = _parse_kv(out)
        return (int(d.get('X', 0)), int(d.get('Y', 0)))

    def move(self, x, y):
        _ps(f"$p=New-Object System.Drawing.Point({x},{y});[System.Windows.Forms.Cursor]::Position=$p")
        return self

    def click(self, x=None, y=None):
        if x is not None: self.move(x, y)
        _ps("""
            $c=[System.Windows.Forms.Cursor]::Position
            $s=Add-Type -MemberDefinition '[DllImport("user32.dll")]public static extern void mouse_event(int f,int dx,int dy,int d,int e);' -Name M -PassThru
            $s::mouse_event(2,0,0,0,0);$s::mouse_event(4,0,0,0,0)
        """)
        return self

    def right_click(self, x=None, y=None):
        if x is not None: self.move(x, y)
        _ps("""
            $s=Add-Type -MemberDefinition '[DllImport("user32.dll")]public static extern void mouse_event(int f,int dx,int dy,int d,int e);' -Name M -PassThru
            $s::mouse_event(8,0,0,0,0);$s::mouse_event(16,0,0,0,0)
        """)
        return self

    def double_click(self, x=None, y=None):
        self.click(x, y); time.sleep(0.1); self.click()
        return self

    def drag(self, x1, y1, x2, y2, steps=20, duration=0.5):
        self.move(x1, y1); time.sleep(0.1)
        _ps("$s=Add-Type -MemberDefinition '[DllImport(\"user32.dll\")]public static extern void mouse_event(int f,int dx,int dy,int d,int e);' -Name M -PassThru;$s::mouse_event(2,0,0,0,0)")
        dx, dy, dt = (x2-x1)/steps, (y2-y1)/steps, duration/steps
        for i in range(1, steps+1):
            self.move(int(x1+dx*i), int(y1+dy*i)); time.sleep(dt)
        _ps("$s=Add-Type -MemberDefinition '[DllImport(\"user32.dll\")]public static extern void mouse_event(int f,int dx,int dy,int d,int e);' -Name M -PassThru;$s::mouse_event(4,0,0,0,0)")
        return self

    def scroll(self, clicks, x=None, y=None):
        if x is not None: self.move(x, y)
        _ps(f"$s=Add-Type -MemberDefinition '[DllImport(\"user32.dll\")]public static extern void mouse_event(int f,int dx,int dy,int d,int e);' -Name M -PassThru;$s::mouse_event(0x0800,0,0,{clicks*120},0)")
        return self

    # === 键盘 ===
    def type(self, text):
        safe = text.replace('"', '`"').replace('$', '`$').replace('+', '{+}').replace('^', '{^}').replace('%', '{%}').replace('~', '{~}').replace('(', '{(}').replace(')', '{)}')
        _ps(f'[System.Windows.Forms.SendKeys]::SendWait("{safe}")')
        return self

    def hotkey(self, *keys):
        combo = '+'.join(f'({k})' if len(k) > 1 else k.upper() for k in keys)
        _ps(f'[System.Windows.Forms.SendKeys]::SendWait("%{combo}")')
        return self

    def press(self, key):
        _ps(f"""
            $s=Add-Type -MemberDefinition '[DllImport("user32.dll")]public static extern void keybd_event(byte vk,byte sc,uint f,int e);' -Name K -PassThru
            $v=[byte][int][char]'{key}';$s::keybd_event($v,0,0,0);Start-Sleep -Milliseconds 50;$s::keybd_event($v,0,2,0)
        """)
        return self

    # === 截屏 ===
    def screenshot(self, save_path=None):
        if save_path:
            _ps(f"""
                $b=New-Object System.Drawing.Rectangle(0,0,[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
                $i=New-Object System.Drawing.Bitmap($b.Width,$b.Height)
                $g=[System.Drawing.Graphics]::FromImage($i)
                $g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size)
                $i.Save('{save_path}');$g.Dispose();$i.Dispose()
            """)
            return save_path

    def screen_size(self):
        """屏幕分辨率 → (w, h)"""
        out = _ps("[System.Windows.Forms.Screen]::PrimaryScreen.Bounds | Format-List Width,Height", raw=True)
        d = _parse_kv(out)
        return (int(d.get('Width', 0)), int(d.get('Height', 0)))
    # === 窗口 ===
    def windows(self):
        """列出有标题的窗口"""
        out = _ps("Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object MainWindowTitle,Id | ConvertTo-Json -Compress", raw=True)
        try:
            data = json.loads(out)
            if isinstance(data, dict): data = [data]
            return [{"title": w.get("MainWindowTitle",""), "pid": w.get("Id",0)} for w in data]
        except:
            return []

    def find_window(self, title_substring):
        for w in self.windows():
            if title_substring.lower() in w["title"].lower():
                return w
        return None

    def focus_window(self, title_substring):
        """按标题聚焦窗口"""
        _ps(f"""
            $s=Add-Type @'
            using System;using System.Runtime.InteropServices;using System.Text;
            public class FW{{
                public delegate bool CB(IntPtr h,IntPtr l);
                [DllImport("user32.dll")]public static extern bool EnumWindows(CB c,IntPtr l);
                [DllImport("user32.dll")]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);
                [DllImport("user32.dll")]public static extern int GetWindowTextLength(IntPtr h);
                [DllImport("user32.dll")]public static extern bool IsWindowVisible(IntPtr h);
                [DllImport("user32.dll")]public static extern bool SetForegroundWindow(IntPtr h);
                [DllImport("user32.dll")]public static extern bool ShowWindow(IntPtr h,int c);
                [DllImport("user32.dll")]public static extern bool IsIconic(IntPtr h);
            }}
'@
            $found=$null;$cb={{param($h,$l)if([FW]::IsWindowVisible($h)){{$n=[FW]::GetWindowTextLength($h);
            $b=New-Object Text.StringBuilder($n+1);[FW]::GetWindowText($h,$b,$b.Capacity)|Out-Null
            if($b.ToString() -like '*{title_substring}*'){{$found=$h;return $false}}}}return $true}}
            [FW]::EnumWindows($cb,[IntPtr]::Zero)|Out-Null
            if($found){{if([FW]::IsIconic($found)){{[FW]::ShowWindow($found,9)}}[FW]::SetForegroundWindow($found)|Out-Null}}
        """)
        return self

    # === 剪贴板 ===
    def clipboard_get(self):
        return _ps("[System.Windows.Forms.Clipboard]::GetText()", raw=True)

    def clipboard_set(self, text):
        safe = text.replace('"', '`"')
        _ps(f'[System.Windows.Forms.Clipboard]::SetText("{safe}")')
        return self

    # === 应用 ===
    def run(self, path, args=None, wait=False):
        cmd = f'Start-Process "{path}"'
        if args: cmd += f' -ArgumentList "{args}"'
        if wait: cmd += ' -Wait'
        _ps(cmd)
        return self

    def kill(self, name_or_pid):
        if isinstance(name_or_pid, int):
            _ps(f"Stop-Process -Id {name_or_pid} -Force")
        else:
            _ps(f"Stop-Process -Name '{name_or_pid}' -Force")
        return self

    # === 工具 ===
    def sleep(self, seconds):
        time.sleep(seconds)
        return self

    def open_url(self, url):
        _ps(f'Start-Process "{url}"')
        return self


class Window:
    def __init__(self, info):
        self.title = info.get("title", "")
        self.hwnd = info.get("hwnd", 0)
        self.pid = info.get("pid", 0)

    def focus(self):
        _ps(f"""
            $s=Add-Type -MemberDefinition '[DllImport("user32.dll")]public static extern bool SetForegroundWindow(IntPtr h);[DllImport("user32.dll")]public static extern bool ShowWindow(IntPtr h,int c);[DllImport("user32.dll")]public static extern bool IsIconic(IntPtr h);' -Name W -PassThru
            if([W]::IsIconic({self.hwnd})){{[W]::ShowWindow({self.hwnd},9)}};[W]::SetForegroundWindow({self.hwnd})|Out-Null
        """)
        return self

    def close(self):
        _ps(f"$s=Add-Type -MemberDefinition '[DllImport(\"user32.dll\")]public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);' -Name W -PassThru;$s::PostMessage({self.hwnd},0x0010,[IntPtr]::Zero,[IntPtr]::Zero)|Out-Null")
        return self

    def __repr__(self):
        return f"Window('{self.title[:30]}', pid={self.pid})"


if __name__ == "__main__":
    d = Desktop()
    print(f"Screen: {d.screen_size()}")
    print(f"Mouse: {d.position()}")
    print(f"Clipboard: {d.clipboard_get()[:60] if d.clipboard_get() else '(empty)'}")
    wins = d.windows()
    print(f"Windows: {len(wins)} visible")
    for w in wins[:5]:
        print(f"  - {w}")
