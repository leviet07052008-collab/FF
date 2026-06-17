import socket
import threading
import json
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_file
import plistlib
import uuid
import os
import time
import binascii

class FFAntiDetectProxy:
    def __init__(self, listen_ip='0.0.0.0', listen_port=8080):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.public_ip = self.get_public_ip()
        self.running = True
        self.hack_enabled = False
        self.hack_type = 'none'
        self.packet_log = []
    
    def get_public_ip(self):
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            return 'localhost'
    
    def handle_client(self, client_socket):
        try:
            target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target.connect(('34.120.100.200', 443))
            
            def forward(src, dst, direction):
                while self.running:
                    try:
                        data = src.recv(4096)
                        if not data:
                            break
                        
                        if direction == 'client_to_proxy':
                            # Log packet
                            hex_data = binascii.hexlify(data[:200]).decode('ascii')
                            log_entry = f"[{datetime.now()}] {len(data)} bytes: {hex_data[:150]}..."
                            self.packet_log.append(log_entry)
                            if len(self.packet_log) > 100:
                                self.packet_log.pop(0)
                            print(log_entry)
                            
                            # Apply hack
                            if self.hack_enabled and self.hack_type != 'none':
                                modified = False
                                # Các pattern mẫu - cần thay bằng pattern thật
                                patterns = {
                                    'aimbot': (b'\x01\x02\x03\x04', b'\xFF\xFF\xFF\xFF'),
                                    'wallhack': (b'\x05\x06\x07\x08', b'\x00\x00\x00\x00'),
                                    'speed': (b'\x09\x0A\x0B\x0C', b'\x01\x01\x01\x01')
                                }
                                for name, (pattern, replace) in patterns.items():
                                    if self.hack_type in ['all', name]:
                                        if pattern in data:
                                            data = data.replace(pattern, replace)
                                            modified = True
                                            print(f"[{datetime.now()}] ✅ {name} applied!")
                                if modified:
                                    print(f"[{datetime.now()}] ✅ Packet modified for {self.hack_type}")
                        
                        dst.send(data)
                    except Exception as e:
                        print(f"Forward error: {e}")
                        break
                try:
                    src.close()
                    dst.close()
                except:
                    pass
            
            t1 = threading.Thread(target=forward, args=(client_socket, target, 'client_to_proxy'))
            t2 = threading.Thread(target=forward, args=(target, client_socket, 'proxy_to_client'))
            t1.daemon = True
            t2.daemon = True
            t1.start()
            t2.start()
            t1.join()
            t2.join()
        except Exception as e:
            print(f"Proxy error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.listen_ip, self.listen_port))
        server.listen(50)
        print(f"[*] Proxy running on {self.public_ip}:8080")
        print(f"[*] Đang log gói tin, vào game để bắt pattern")
        while self.running:
            try:
                client, addr = server.accept()
                print(f"[+] Connection from {addr}")
                threading.Thread(target=self.handle_client, args=(client,)).start()
            except:
                break
        server.close()

app = Flask(__name__)
proxy_instance = None

def get_public_ip_web():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        return 'localhost'

PUBLIC_IP = get_public_ip_web()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FreeFire Proxy Hack</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a0a; color: #0f0; font-family: 'Courier New', monospace; min-height: 100vh; }
        .container { width: 95%; max-width: 900px; margin: 20px auto; }
        .card { background: #1a1a1a; border: 1px solid #0f0; padding: 20px; margin: 10px 0; border-radius: 10px; }
        .ip-box { background: #000; padding: 15px; border: 1px dashed #0f0; text-align: center; font-size: 1.5em; word-break: break-all; }
        select { padding: 12px; width: 100%; margin: 10px 0; background: #222; color: #0f0; border: 1px solid #0f0; font-size: 1em; }
        button { background: #0f0; color: #000; padding: 12px 24px; border: none; cursor: pointer; font-weight: bold; margin: 5px; border-radius: 5px; font-size: 1em; }
        button:hover { background: #00cc00; transform: scale(1.02); }
        .btn-danger { background: #f00; color: #fff; }
        .btn-danger:hover { background: #cc0000; }
        .btn-log { background: #00f; color: #fff; }
        .btn-log:hover { background: #0000cc; }
        .status { margin-top: 15px; padding: 15px; background: #111; border-radius: 5px; border-left: 3px solid #0f0; }
        .status-off { border-left-color: #f00; }
        h1 { text-align: center; text-shadow: 0 0 20px #0f0; }
        .hack-status { font-size: 1.5em; padding: 15px; text-align: center; border-radius: 8px; }
        .enabled { color: #0f0; background: #001a00; border: 1px solid #0f0; }
        .disabled { color: #f00; background: #1a0000; border: 1px solid #f00; }
        .log-box { background: #000; padding: 15px; max-height: 400px; overflow-y: auto; font-size: 0.75em; white-space: pre-wrap; word-break: break-all; border: 1px solid #333; border-radius: 5px; color: #aaa; }
        .log-box .highlight { color: #0f0; }
        .flex { display: flex; flex-wrap: wrap; gap: 10px; }
        .flex button { flex: 1; min-width: 100px; }
        ol { color: #aaa; line-height: 2; padding-left: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 FF PROXY HACK</h1>
        
        <div class="card">
            <h3>🌐 IP Công khai của bạn:</h3>
            <div class="ip-box" id="public_ip">{{ public_ip }}</div>
            <p style="margin-top:10px;color:#888;">Dùng IP này để cài proxy trên iPhone</p>
        </div>
        
        <div class="card">
            <h3>🎯 Chọn hack:</h3>
            <select id="hack_type">
                <option value="none">❌ Tắt hack</option>
                <option value="aimbot">🎯 Aimbot</option>
                <option value="wallhack">🧱 Wallhack</option>
                <option value="speed">⚡ Speed Hack</option>
                <option value="all">🔥 Tất cả</option>
            </select>
            <div class="flex">
                <button onclick="enableHack()">✅ BẬT HACK</button>
                <button onclick="disableHack()" class="btn-danger">⛔ TẮT HACK</button>
                <button onclick="downloadConfig()" class="btn-log">📲 Tải .mobileconfig</button>
            </div>
        </div>
        
        <div class="card">
            <div id="hack_status" class="hack-status disabled">⛔ HACK: ĐANG TẮT</div>
        </div>
        
        <div class="card">
            <div class="flex">
                <button onclick="viewLog()" class="btn-log">📋 Xem log</button>
                <button onclick="clearLog()" class="btn-danger">🗑️ Xóa log</button>
                <button onclick="autoRefresh()" class="btn-log">🔄 Tự động làm mới</button>
            </div>
            <div id="log_content" class="log-box">📡 Đang chờ dữ liệu...<br>Bật proxy trên iPhone và vào game để bắt gói tin</div>
        </div>
        
        <div class="card">
            <h3>📖 Hướng dẫn:</h3>
            <ol>
                <li>Tải file .mobileconfig và cài trên iPhone</li>
                <li>Settings → Wi-Fi → Proxy manual → IP: {{ public_ip }} Port: 8080</li>
                <li>Vào game Free Fire và chơi 1 trận</li>
                <li>Quay lại web này → bấm <span style="color:#0f0;">"Xem log"</span> để xem gói tin</li>
                <li>Chọn hack → bấm <span style="color:#0f0;">"BẬT HACK"</span> → vào game</li>
            </ol>
        </div>
        
        <div id="status" class="status">💡 Sẵn sàng. Bật proxy và vào game để bắt log.</div>
    </div>
    
    <script>
        let autoRefreshInterval = null;
        
        function enableHack() {
            const type = document.getElementById('hack_type').value;
            if (type === 'none') {
                document.getElementById('status').innerHTML = '⚠️ Vui lòng chọn loại hack trước!';
                return;
            }
            document.getElementById('status').innerHTML = '⏳ Đang bật hack...';
            fetch('/enable_hack', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({hack: type, enabled: true})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('status').innerHTML = '✅ ' + data.status;
                document.getElementById('hack_status').innerHTML = '✅ HACK: ĐANG BẬT - ' + type.toUpperCase();
                document.getElementById('hack_status').className = 'hack-status enabled';
            })
            .catch(err => {
                document.getElementById('status').innerHTML = '❌ Lỗi: ' + err;
            });
        }
        
        function disableHack() {
            document.getElementById('status').innerHTML = '⏳ Đang tắt hack...';
            fetch('/disable_hack', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('status').innerHTML = '⛔ ' + data.status;
                document.getElementById('hack_status').innerHTML = '⛔ HACK: ĐANG TẮT';
                document.getElementById('hack_status').className = 'hack-status disabled';
            })
            .catch(err => {
                document.getElementById('status').innerHTML = '❌ Lỗi: ' + err;
            });
        }
        
        function downloadConfig() {
            const ip = document.getElementById('public_ip').innerText;
            window.location.href = '/download?ip=' + ip + '&port=8080';
        }
        
        function viewLog() {
            fetch('/get_log')
            .then(r => r.text())
            .then(data => {
                document.getElementById('log_content').innerText = data || '📡 Chưa có dữ liệu. Vào game để bắt gói tin.';
                document.getElementById('log_content').scrollTop = document.getElementById('log_content').scrollHeight;
            });
        }
        
        function clearLog() {
            fetch('/clear_log')
            .then(r => r.json())
            .then(data => {
                document.getElementById('status').innerHTML = '✅ ' + data.status;
                document.getElementById('log_content').innerText = '🗑️ Đã xóa log';
            });
        }
        
        function autoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                document.getElementById('status').innerHTML = '⏹️ Đã dừng tự động làm mới';
                return;
            }
            viewLog();
            autoRefreshInterval = setInterval(viewLog, 3000);
            document.getElementById('status').innerHTML = '🔄 Đang tự động làm mới mỗi 3 giây';
        }
        
        // Tự động xem log khi load trang
        setTimeout(viewLog, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, public_ip=PUBLIC_IP)

@app.route('/enable_hack', methods=['POST'])
def enable_hack():
    global proxy_instance
    data = request.json
    hack_type = data.get('hack', 'none')
    try:
        if proxy_instance:
            proxy_instance.hack_enabled = True
            proxy_instance.hack_type = hack_type
            with open('hack_state.json', 'w') as f:
                json.dump({'active': hack_type, 'enabled': True, 'timestamp': str(datetime.now())}, f)
            return jsonify({'status': f'Đã bật hack: {hack_type}'})
        return jsonify({'status': 'Proxy chưa chạy!'}), 500
    except Exception as e:
        return jsonify({'status': f'Lỗi: {str(e)}'}), 500

@app.route('/disable_hack', methods=['POST'])
def disable_hack():
    global proxy_instance
    try:
        if proxy_instance:
            proxy_instance.hack_enabled = False
            proxy_instance.hack_type = 'none'
            with open('hack_state.json', 'w') as f:
                json.dump({'active': 'none', 'enabled': False, 'timestamp': str(datetime.now())}, f)
            return jsonify({'status': 'Đã tắt hack'})
        return jsonify({'status': 'Proxy chưa chạy!'}), 500
    except Exception as e:
        return jsonify({'status': f'Lỗi: {str(e)}'}), 500

@app.route('/get_log')
def get_log():
    global proxy_instance
    try:
        if proxy_instance:
            logs = proxy_instance.packet_log
            if logs:
                return '\n'.join(logs[-50:])
        return '📡 Chưa có dữ liệu. Vào game để bắt gói tin.'
    except:
        return 'Lỗi đọc log'

@app.route('/clear_log')
def clear_log():
    global proxy_instance
    try:
        if proxy_instance:
            proxy_instance.packet_log = []
        return jsonify({'status': 'Đã xóa log'})
    except:
        return jsonify({'status': 'Lỗi khi xóa'}), 500

@app.route('/download')
def download():
    ip = request.args.get('ip', PUBLIC_IP)
    port = request.args.get('port', '8080')
    try:
        payload_id = str(uuid.uuid4()).upper()
        config = {
            "PayloadContent": [{
                "PayloadContent": {
                    "HTTPProxy": ip,
                    "HTTPProxyPort": int(port),
                    "HTTPSProxy": ip,
                    "HTTPSProxyPort": int(port),
                    "ProxyAutoConfigEnable": 0,
                    "ProxyAutoDiscoveryEnable": 0
                },
                "PayloadDisplayName": "FF Proxy",
                "PayloadIdentifier": f"com.ff.proxy.{payload_id}",
                "PayloadType": "com.apple.proxy.http",
                "PayloadUUID": payload_id,
                "PayloadVersion": 1,
                "ProxyType": 1
            }],
            "PayloadDisplayName": "FreeFire Proxy",
            "PayloadIdentifier": f"com.ff.hack.{payload_id}",
            "PayloadType": "Configuration",
            "PayloadUUID": str(uuid.uuid4()).upper(),
            "PayloadVersion": 1,
            "PayloadRemovalDisallowed": False,
            "PayloadOrganization": "FF Hack"
        }
        filename = f"FreeFire_Proxy_{ip.replace('.','_')}.mobileconfig"
        with open(filename, "wb") as f:
            plistlib.dump(config, f)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"Lỗi: {str(e)}", 500

def run_proxy():
    global proxy_instance
    proxy_instance = FFAntiDetectProxy()
    proxy_instance.run()

def run_web():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("="*60)
    print("  🔥 FREEFIRE PROXY HACK - FULL VERSION 🔥")
    print("="*60)
    print("  📌 HƯỚNG DẪN:")
    print("  1. Bật proxy trên iPhone (Manual -> IP:Port)")
    print("  2. Vào game Free Fire và chơi 1 trận")
    print("  3. Quay lại web -> bấm 'Xem log' để bắt gói tin")
    print("  4. Chọn hack -> bấm 'BẬT HACK' -> vào game")
    print("="*60)
    
    if not os.path.exists('hack_state.json'):
        with open('hack_state.json', 'w') as f:
            json.dump({'active': 'none', 'enabled': False, 'timestamp': str(datetime.now())}, f)
    
    proxy_thread = threading.Thread(target=run_proxy, daemon=True)
    proxy_thread.start()
    time.sleep(1)
    
    try:
        run_web()
    except KeyboardInterrupt:
        print("\n[*] Đang tắt...")
        if proxy_instance:
            proxy_instance.running = False
        print("[*] Đã tắt toàn bộ hệ thống")
EOF