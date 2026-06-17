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

class FFAntiDetectProxy:
    def __init__(self, listen_ip='0.0.0.0', listen_port=8080):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.hack_rules = self.load_hack_rules()
        self.public_ip = self.get_public_ip()
        self.running = True
    
    def get_public_ip(self):
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            try:
                response = requests.get('https://ifconfig.me/ip', timeout=5)
                return response.text.strip()
            except:
                return 'localhost'
    
    def load_hack_rules(self):
        return {
            "aimbot": {"pattern": rb'\x01\x02\x03\x04', "replace": rb'\xFF\xFF\xFF\xFF'},
            "wallhack": {"pattern": rb'\x05\x06\x07\x08', "replace": rb'\x00\x00\x00\x00'},
            "speed": {"pattern": rb'\x09\x0A\x0B\x0C', "replace": rb'\x01\x01\x01\x01'},
            "damage": {"pattern": rb'\x0D\x0E\x0F\x10', "replace": rb'\xFF\xFF\xFF\xFF'},
            "esp": {"pattern": rb'\x11\x12\x13\x14', "replace": rb'\x01\x01\x01\x01'}
        }
    
    def handle_client(self, client_socket, target_host='34.120.100.200', target_port=443):
        try:
            target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target.connect((target_host, target_port))
            
            def forward(src, dst, direction):
                while self.running:
                    try:
                        data = src.recv(4096)
                        if not data:
                            break
                        if direction == 'client_to_proxy':
                            try:
                                if os.path.exists('hack_state.json'):
                                    with open('hack_state.json', 'r') as f:
                                        state = json.load(f)
                                    active = state.get('active', 'none')
                                    if active != 'none':
                                        for rule_name, rule in self.hack_rules.items():
                                            if rule['pattern'] in data and (active == 'all' or active == rule_name):
                                                data = data.replace(rule['pattern'], rule['replace'])
                                                print(f"[{datetime.now()}] Applied: {rule_name}")
                            except:
                                pass
                        dst.send(data)
                    except:
                        break
                src.close()
                dst.close()
            
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
        print(f"[*] Proxy running on {self.public_ip}:{self.listen_port}")
        print(f"[*] Press Ctrl+C to stop")
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
        body { 
            background: #0a0a0a; 
            color: #0f0; 
            font-family: 'Courier New', monospace;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container { 
            width: 90%; 
            max-width: 800px; 
            padding: 20px;
        }
        h1 { 
            text-align: center; 
            font-size: 2.5em;
            text-shadow: 0 0 20px #0f0;
            margin-bottom: 30px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .card { 
            background: rgba(26, 26, 26, 0.95); 
            border: 1px solid #0f0; 
            padding: 25px; 
            margin: 15px 0; 
            border-radius: 12px;
            box-shadow: 0 0 30px rgba(0, 255, 0, 0.05);
        }
        .ip-box { 
            background: #000; 
            padding: 15px; 
            border: 1px dashed #0f0;
            text-align: center;
            font-size: 1.5em;
            border-radius: 8px;
            word-break: break-all;
        }
        select { 
            padding: 12px; 
            width: 100%; 
            margin: 10px 0; 
            background: #222; 
            color: #0f0; 
            border: 1px solid #0f0;
            border-radius: 8px;
            font-size: 1em;
            font-family: 'Courier New', monospace;
        }
        button { 
            background: #0f0; 
            color: #000; 
            padding: 12px 30px; 
            border: none; 
            cursor: pointer; 
            font-weight: bold;
            font-size: 1em;
            border-radius: 8px;
            margin: 5px;
            transition: all 0.3s;
            font-family: 'Courier New', monospace;
        }
        button:hover { 
            background: #00cc00; 
            transform: scale(1.02);
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
        }
        .btn-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 10px 0;
        }
        .btn-group button {
            flex: 1;
            min-width: 120px;
        }
        ol { 
            color: #aaa; 
            padding-left: 20px;
            line-height: 1.8;
        }
        .status { 
            margin-top: 15px; 
            padding: 15px; 
            background: #111;
            border-radius: 8px;
            min-height: 50px;
            border-left: 3px solid #0f0;
        }
        .footer {
            text-align: center;
            color: #444;
            margin-top: 30px;
            font-size: 0.8em;
        }
        .highlight { color: #0f0; }
        @media (max-width: 600px) {
            h1 { font-size: 1.8em; }
            .ip-box { font-size: 1em; }
            .btn-group button { min-width: 80px; font-size: 0.8em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 FF PROXY HACK</h1>
        
        <div class="card">
            <h3>🌐 IP Công khai của bạn:</h3>
            <div class="ip-box" id="public_ip">{{ public_ip }}</div>
            <p style="margin-top:10px;color:#888;">Dùng IP này để cài proxy trên điện thoại</p>
        </div>
        
        <div class="card">
            <h3>🎯 Chọn loại hack:</h3>
            <select id="hack_type">
                <option value="none">❌ Tắt hack</option>
                <option value="aimbot">🎯 Aimbot (tự động ngắm)</option>
                <option value="wallhack">🧱 Wallhack (xuyên tường)</option>
                <option value="speed">⚡ Speed Hack (tăng tốc)</option>
                <option value="damage">💀 Damage Boost (tăng sát thương)</option>
                <option value="esp">👁️ ESP (nhìn xuyên)</option>
                <option value="all">🔥 Tất cả hack</option>
            </select>
            <div class="btn-group">
                <button onclick="applyHack()">✅ Áp dụng hack</button>
                <button onclick="downloadConfig()">📲 Tải .mobileconfig</button>
                <button onclick="checkStatus()">📊 Kiểm tra trạng thái</button>
            </div>
        </div>
        
        <div class="card">
            <h3>📖 Hướng dẫn sử dụng:</h3>
            <ol>
                <li>Tải file <span class="highlight">.mobileconfig</span> về iPhone</li>
                <li>Vào <span class="highlight">Settings → General → VPN & Device Management</span></li>
                <li>Cài profile vừa tải xuống</li>
                <li>Vào <span class="highlight">Wi-Fi</span> → chọn mạng đang dùng</li>
                <li>Chọn <span class="highlight">Proxy manual</span> → IP: <strong>{{ public_ip }}</strong> Port: <strong>8080</strong></li>
                <li>Quay lại web, chọn hack và bấm <span class="highlight">Áp dụng hack</span></li>
                <li>Mở Free Fire và chơi!</li>
            </ol>
        </div>
        
        <div id="status" class="status">💡 Chưa áp dụng hack nào</div>
        <div class="footer">⚡ Bypass By nhatanh Dev ⚡</div>
    </div>

    <script>
        function applyHack() {
            const type = document.getElementById('hack_type').value;
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '⏳ Đang áp dụng...';
            
            fetch('/apply_hack', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({hack: type})
            })
            .then(r => r.json())
            .then(data => {
                statusDiv.innerHTML = '✅ ' + data.status;
                statusDiv.style.borderLeftColor = '#0f0';
            })
            .catch(err => {
                statusDiv.innerHTML = '❌ Lỗi: ' + err;
                statusDiv.style.borderLeftColor = '#f00';
            });
        }

        function downloadConfig() {
            const ip = document.getElementById('public_ip').innerText;
            window.location.href = '/download?ip=' + ip + '&port=8080';
        }

        function checkStatus() {
            const statusDiv = document.getElementById('status');
            fetch('/get_status')
            .then(r => r.json())
            .then(data => {
                statusDiv.innerHTML = '📊 ' + data.status;
                statusDiv.style.borderLeftColor = '#0f0';
            })
            .catch(err => {
                statusDiv.innerHTML = '❌ Lỗi: ' + err;
                statusDiv.style.borderLeftColor = '#f00';
            });
        }

        setInterval(checkStatus, 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, public_ip=PUBLIC_IP)

@app.route('/apply_hack', methods=['POST'])
def apply_hack():
    data = request.json
    hack = data.get('hack', 'none')
    try:
        with open('hack_state.json', 'w') as f:
            json.dump({'active': hack, 'timestamp': str(datetime.now())}, f)
        return jsonify({'status': f'Đã kích hoạt: {hack}'})
    except Exception as e:
        return jsonify({'status': f'Lỗi: {str(e)}'}), 500

@app.route('/get_status')
def get_status():
    try:
        if os.path.exists('hack_state.json'):
            with open('hack_state.json', 'r') as f:
                state = json.load(f)
            active = state.get('active', 'none')
            ts = state.get('timestamp', 'N/A')
            return jsonify({'status': f'Hack đang bật: {active} (từ {ts})'})
        return jsonify({'status': 'Chưa có hack nào được kích hoạt'})
    except:
        return jsonify({'status': 'Lỗi đọc trạng thái'}), 500

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
                "PayloadDisplayName": "FF Hack Proxy",
                "PayloadIdentifier": f"com.ff.proxy.{payload_id}",
                "PayloadType": "com.apple.proxy.http",
                "PayloadUUID": payload_id,
                "PayloadVersion": 1,
                "ProxyType": 1
            }],
            "PayloadDisplayName": "FreeFire Proxy Tool",
            "PayloadIdentifier": f"com.ff.hack.{payload_id}",
            "PayloadType": "Configuration",
            "PayloadUUID": str(uuid.uuid4()).upper(),
            "PayloadVersion": 1,
            "PayloadRemovalDisallowed": False,
            "PayloadOrganization": "FF Hack Team"
        }
        
        filename = f"FreeFire_Proxy_{ip.replace('.','_')}.mobileconfig"
        with open(filename, "wb") as f:
            plistlib.dump(config, f)
        
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"Lỗi tạo file: {str(e)}", 500

def run_proxy():
    global proxy_instance
    proxy_instance = FFAntiDetectProxy()
    proxy_instance.run()

def run_web():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("="*60)
    print("  🔥 FREEFIRE PROXY HACK - ALL-IN-ONE 🔥")
    print("="*60)
    print("  Đang khởi động Proxy Server trên port 8080...")
    print("  Đang khởi động Web Server trên port 5000...")
    print("  Truy cập: http://localhost:5000")
    print("="*60)
    
    if not os.path.exists('hack_state.json'):
        with open('hack_state.json', 'w') as f:
            json.dump({'active': 'none', 'timestamp': str(datetime.now())}, f)
    
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