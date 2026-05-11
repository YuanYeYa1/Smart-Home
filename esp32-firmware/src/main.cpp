#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include "config.h"

// ========== 全局对象声明 ==========
DHT dht(DHTPIN, DHTTYPE);
WiFiClientSecure wifiClient;  // TLS 安全连接（EMQX 8883 端口需要）
PubSubClient mqttClient(wifiClient);
AsyncWebServer server(80);

// ========== 全局变量 ==========
float currentTemp = 0.0;
float currentHum = 0.0;
bool relayState = false;
unsigned long lastSensorRead = 0;
unsigned long lastMqttReconnect = 0;
unsigned long lastMqttPublish = 0;
String mqttClientId;  // 运行时生成的唯一 Client ID

// ========== HTML 页面（内嵌在固件中，无需 SPIFFS） ==========
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 智能家居系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            max-width: 420px;
            width: 100%;
        }
        .card {
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        .card-title {
            font-size: 20px;
            font-weight: 600;
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }
        .sensor-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 10px;
        }
        .sensor-item {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }
        .sensor-icon { font-size: 32px; margin-bottom: 8px; }
        .sensor-value {
            font-size: 28px;
            font-weight: 700;
            color: #333;
        }
        .sensor-unit { font-size: 16px; color: #666; }
        .sensor-label {
            font-size: 13px;
            color: #888;
            margin-top: 5px;
        }
        .switch-container {
            text-align: center;
            margin: 20px 0;
        }
        .switch-label {
            font-size: 14px;
            color: #888;
            margin-bottom: 10px;
        }
        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 80px;
            height: 44px;
        }
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background: #ccc;
            transition: 0.3s;
            border-radius: 44px;
        }
        .slider:before {
            content: "";
            position: absolute;
            height: 34px; width: 34px;
            left: 5px; bottom: 5px;
            background: white;
            transition: 0.3s;
            border-radius: 50%;
        }
        input:checked + .slider { background: #4CAF50; }
        input:checked + .slider:before { transform: translateX(36px); }
        .switch-status {
            font-size: 16px;
            font-weight: 600;
            margin-top: 10px;
        }
        .status-on { color: #4CAF50; }
        .status-off { color: #999; }
        .status-bar {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-top: 1px solid #eee;
            margin-top: 15px;
        }
        .status-item {
            text-align: center;
            flex: 1;
        }
        .status-dot {
            width: 10px; height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }
        .dot-online { background: #4CAF50; }
        .dot-offline { background: #f44336; }
        .status-text { font-size: 12px; color: #666; }
        .footer {
            text-align: center;
            color: rgba(255,255,255,0.7);
            font-size: 12px;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 14px;
            cursor: pointer;
            margin-top: 10px;
            transition: 0.3s;
        }
        .refresh-btn:hover { background: #5a6fd6; }
    </style>
</head>
<body>
    <div class="container">
        <!-- 温湿度卡片 -->
        <div class="card">
            <div class="card-title">🌡️ 温湿度监测</div>
            <div class="sensor-grid">
                <div class="sensor-item">
                    <div class="sensor-icon">🌡️</div>
                    <div class="sensor-value" id="temp">--</div>
                    <div class="sensor-unit">°C</div>
                    <div class="sensor-label">温度</div>
                </div>
                <div class="sensor-item">
                    <div class="sensor-icon">💧</div>
                    <div class="sensor-value" id="hum">--</div>
                    <div class="sensor-unit">%</div>
                    <div class="sensor-label">湿度</div>
                </div>
            </div>
            <button class="refresh-btn" onclick="refreshSensor()">🔄 刷新数据</button>
        </div>

        <!-- 开关控制卡片 -->
        <div class="card">
            <div class="card-title">🔌 智能开关</div>
            <div class="switch-container">
                <label class="toggle-switch">
                    <input type="checkbox" id="relayCheckbox" onchange="toggleRelay(this.checked)">
                    <span class="slider"></span>
                </label>
                <div class="switch-status" id="relayStatus">状态: 关闭</div>
            </div>
        </div>

        <!-- 系统状态 -->
        <div class="card">
            <div class="status-bar">
                <div class="status-item">
                    <span class="status-dot dot-online" id="wifiDot"></span>
                    <div class="status-text" id="wifiStatus">WiFi: 连接中...</div>
                </div>
                <div class="status-item">
                    <span class="status-dot dot-offline" id="mqttDot"></span>
                    <div class="status-text" id="mqttStatus">MQTT: 未连接</div>
                </div>
            </div>
        </div>

        <div class="footer">ESP32 智能家居控制系统 v1.0</div>
    </div>

    <script>
        // 获取传感器数据
        async function fetchSensorData() {
            try {
                const response = await fetch('/api/sensor');
                const data = await response.json();
                document.getElementById('temp').textContent = data.temperature.toFixed(1);
                document.getElementById('hum').textContent = data.humidity.toFixed(1);
            } catch(e) {
                console.log('获取传感器数据失败');
            }
        }

        // 获取开关状态
        async function fetchRelayState() {
            try {
                const response = await fetch('/api/relay');
                const data = await response.json();
                const isOn = data.state;
                document.getElementById('relayCheckbox').checked = isOn;
                document.getElementById('relayStatus').textContent = isOn ? '状态: 🔛 开启' : '状态: 🔴 关闭';
                document.getElementById('relayStatus').className = 'switch-status ' + (isOn ? 'status-on' : 'status-off');
            } catch(e) {
                console.log('获取开关状态失败');
            }
        }

        // 切换继电器
        async function toggleRelay(state) {
            try {
                const response = await fetch('/api/relay', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ state: state })
                });
                const data = await response.json();
                document.getElementById('relayCheckbox').checked = data.state;
                document.getElementById('relayStatus').textContent = data.state ? '状态: 🔛 开启' : '状态: 🔴 关闭';
                document.getElementById('relayStatus').className = 'switch-status ' + (data.state ? 'status-on' : 'status-off');
            } catch(e) {
                console.log('切换开关失败');
                document.getElementById('relayCheckbox').checked = !state;
            }
        }

        // 获取系统状态
        async function fetchSystemStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('wifiDot').className = 'status-dot ' + (data.wifi ? 'dot-online' : 'dot-offline');
                document.getElementById('wifiStatus').textContent = data.wifi ? 'WiFi: 已连接 (IP: ' + data.ip + ')' : 'WiFi: 未连接';
                document.getElementById('mqttDot').className = 'status-dot ' + (data.mqtt ? 'dot-online' : 'dot-offline');
                document.getElementById('mqttStatus').textContent = data.mqtt ? 'MQTT: 已连接' : 'MQTT: 未连接';
            } catch(e) {
                console.log('获取系统状态失败');
            }
        }

        function refreshSensor() {
            fetchSensorData();
            fetchRelayState();
            fetchSystemStatus();
        }

        // 页面加载时获取数据
        window.onload = function() {
            fetchSensorData();
            fetchRelayState();
            fetchSystemStatus();
        };

        // 每5秒自动刷新数据
        setInterval(fetchSensorData, 5000);
        setInterval(fetchSystemStatus, 10000);
    </script>
</body>
</html>
)rawliteral";

// ========== WiFi 初始化（仅调用一次）==========
void initWiFi() {
    WiFi.mode(WIFI_STA);

    // 关闭省电模式，稳定很多
    WiFi.setSleep(false);

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    Serial.print("Connecting to WiFi: ");
    Serial.println(WIFI_SSID);
}

// ========== 扫描并打印附近 WiFi ==========
void scanWiFi() {
    Serial.println("\n[SCAN] Scanning for nearby WiFi networks...");
    int n = WiFi.scanNetworks();
    if (n == 0) {
        Serial.println("[SCAN] No networks found");
    } else {
        Serial.print("[SCAN] Found ");
        Serial.print(n);
        Serial.println(" networks:");
        for (int i = 0; i < n; i++) {
            Serial.print("  ");
            Serial.print(i + 1);
            Serial.print(": ");
            Serial.print(WiFi.SSID(i));
            Serial.print(" (RSSI: ");
            Serial.print(WiFi.RSSI(i));
            Serial.print(" dBm, ");
            if (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) {
                Serial.print("Open");
            } else {
                Serial.print("Secured");
            }
            Serial.println(")");
        }
    }
    WiFi.scanDelete();
}

// ========== 确保 WiFi 连接（每次 loop 调用，非阻塞）==========
bool ensureWiFi() {
    static bool wasConnected = false;
    static unsigned long lastDot = 0;
    static unsigned long lastReconnect = 0;
    static unsigned long lastScan = 0;

    if (WiFi.status() == WL_CONNECTED && WiFi.localIP() != IPAddress(0, 0, 0, 0)) {
        if (!wasConnected) {
            wasConnected = true;
            Serial.println("\nWiFi connected successfully!");
            Serial.print("IP address: ");
            Serial.println(WiFi.localIP());
        }
        return true;
    }

    // WiFi disconnected - log once and trigger a scan
    if (wasConnected) {
        wasConnected = false;
        Serial.println("\n[WARN] WiFi disconnected, reconnecting...");
        scanWiFi();
        lastScan = millis();
    }

    // Show progress dots
    if (millis() - lastDot >= 500) {
        Serial.print(".");
        lastDot = millis();
    }

    // Retry connection every 5 seconds if still not connected
    if (!lastReconnect || millis() - lastReconnect >= 5000) {
        Serial.println("Retrying WiFi...");

        WiFi.disconnect(false, false);
        delay(200);

        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

        lastReconnect = millis();
    }

    // Periodic scan every 30 seconds while disconnected
    if (millis() - lastScan >= 30000) {
        scanWiFi();
        lastScan = millis();
    }

    return false;
}

// ========== MQTT 回调 ==========
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    char message[length + 1];
    memcpy(message, payload, length);
    message[length] = '\0';
    
    String topicStr = String(topic);
    String msgStr = String(message);
    
    Serial.print("MQTT message received [");
    Serial.print(topic);
    Serial.print("]: ");
    Serial.println(message);

    // 解析开关控制指令
    if (topicStr == MQTT_TOPIC_SWITCH) {
        if (msgStr == "ON" || msgStr == "on" || msgStr == "1") {
            relayState = true;
            digitalWrite(RELAY_PIN, HIGH);
        } else if (msgStr == "OFF" || msgStr == "off" || msgStr == "0") {
            relayState = false;
            digitalWrite(RELAY_PIN, LOW);
        } else {
            // 尝试解析 JSON
            StaticJsonDocument<64> doc;
            DeserializationError error = deserializeJson(doc, message);
            if (!error) {
                if (doc.containsKey("state")) {
                    relayState = doc["state"];
                    digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);
                }
            }
        }
        
        // 发布开关状态回 MQTT
        StaticJsonDocument<64> statusDoc;
        statusDoc["state"] = relayState;
        statusDoc["timestamp"] = millis();
        char statusBuffer[128];
        serializeJson(statusDoc, statusBuffer);
        mqttClient.publish(MQTT_TOPIC_SWITCH_STATUS, statusBuffer);
    }
}

// ========== MQTT 连接 ==========
void connectMQTT() {
    // 确保 WiFi 已连接并有 IP，再尝试连接 MQTT
    if (WiFi.status() != WL_CONNECTED || WiFi.localIP() == IPAddress(0, 0, 0, 0)) {
        Serial.println("[SKIP] WiFi not connected or no IP, skipping MQTT connection");
        return;
    }
    
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    
    // ====== TLS 底层连通性测试 ======
    Serial.print("[TLS] Testing TCP/TLS connection to ");
    Serial.print(MQTT_BROKER);
    Serial.print(":");
    Serial.println(MQTT_PORT);
    
    if (!wifiClient.connect(MQTT_BROKER, MQTT_PORT)) {
        Serial.println("[TLS] TCP/TLS handshake FAILED - check network/firewall/broker");
        Serial.print("[TLS] wifiClient error: ");
        char errBuf[128];
        wifiClient.lastError(errBuf, sizeof(errBuf));
        Serial.print("TLS Error: ");
        Serial.println(errBuf);
        // 连接失败后关闭 socket，避免残留
        wifiClient.stop();
        return;
    }
    Serial.println("[TLS] TCP/TLS handshake SUCCESS");
    wifiClient.stop();  // 测试完成，关闭连接；后续 mqttClient.connect 会重新建立
    
    Serial.print("Connecting to MQTT Broker (TLS): ");
    Serial.println(MQTT_BROKER);
    
    if (mqttClient.connect(mqttClientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD)) {
        Serial.println("MQTT connected successfully!");
        
        // Subscribe to switch control topic
        mqttClient.subscribe(MQTT_TOPIC_SWITCH);
        Serial.print("Subscribed to topic: ");
        Serial.println(MQTT_TOPIC_SWITCH);
        
        // 发布上线消息
        StaticJsonDocument<128> doc;
        doc["device"] = mqttClientId;
        doc["status"] = "online";
        doc["ip"] = WiFi.localIP().toString();
        char buffer[256];
        serializeJson(doc, buffer);
        mqttClient.publish(MQTT_TOPIC_HEARTBEAT, buffer);
    } else {
        Serial.print("MQTT connection failed, state: ");
        Serial.println(mqttClient.state());
    }
}

// ========== 读取传感器 ==========
void readSensor() {
    float newTemp = dht.readTemperature();
    float newHum = dht.readHumidity();
    
    if (isnan(newTemp) || isnan(newHum)) {
        Serial.println("[WARN] DHT sensor read failed");
        return;
    }
    
    currentTemp = newTemp;
    currentHum = newHum;
    
    Serial.printf("Temp: %.1fC | Humidity: %.1f%%\n", currentTemp, currentHum);
}

// ========== 发布 MQTT 数据 ==========
void publishMQTTData() {
    if (!mqttClient.connected()) return;
    
    // 发布温度
    StaticJsonDocument<64> tempDoc;
    tempDoc["value"] = currentTemp;
    tempDoc["unit"] = "°C";
    char tempBuffer[128];
    serializeJson(tempDoc, tempBuffer);
    mqttClient.publish(MQTT_TOPIC_TEMP, tempBuffer);
    
    // 发布湿度
    StaticJsonDocument<64> humDoc;
    humDoc["value"] = currentHum;
    humDoc["unit"] = "%";
    char humBuffer[128];
    serializeJson(humDoc, humBuffer);
    mqttClient.publish(MQTT_TOPIC_HUM, humBuffer);
    
    // 发布开关状态
    StaticJsonDocument<64> relayDoc;
    relayDoc["state"] = relayState;
    char relayBuffer[128];
    serializeJson(relayDoc, relayBuffer);
    mqttClient.publish(MQTT_TOPIC_SWITCH_STATUS, relayBuffer);
    
    Serial.println("[MQTT] Data published");
}

// ========== 初始化 Web 服务器 ==========
void initWebServer() {
    // API: 获取传感器数据
    server.on("/api/sensor", HTTP_GET, [](AsyncWebServerRequest *request) {
        StaticJsonDocument<128> doc;
        doc["temperature"] = currentTemp;
        doc["humidity"] = currentHum;
        doc["timestamp"] = millis();
        String response;
        serializeJson(doc, response);
        request->send(200, "application/json", response);
    });

    // API: 获取/控制继电器
    server.on("/api/relay", HTTP_GET, [](AsyncWebServerRequest *request) {
        StaticJsonDocument<64> doc;
        doc["state"] = relayState;
        String response;
        serializeJson(doc, response);
        request->send(200, "application/json", response);
    });

    server.on("/api/relay", HTTP_POST, [](AsyncWebServerRequest *request) {
        // 处理 JSON body
    }, NULL, [](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
        StaticJsonDocument<64> doc;
        DeserializationError error = deserializeJson(doc, data, len);
        
        if (error) {
            request->send(400, "application/json", "{\"error\":\"Invalid JSON\"}");
            return;
        }
        
        if (doc.containsKey("state")) {
            relayState = doc["state"];
            digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);
            
            // 通过MQTT通知状态变化
            if (mqttClient.connected()) {
                StaticJsonDocument<64> statusDoc;
                statusDoc["state"] = relayState;
                char buffer[128];
                serializeJson(statusDoc, buffer);
                mqttClient.publish(MQTT_TOPIC_SWITCH_STATUS, buffer);
            }
        }
        
        StaticJsonDocument<64> responseDoc;
        responseDoc["state"] = relayState;
        responseDoc["success"] = true;
        String response;
        serializeJson(responseDoc, response);
        request->send(200, "application/json", response);
    });

    // API: 获取系统状态
    server.on("/api/status", HTTP_GET, [](AsyncWebServerRequest *request) {
        StaticJsonDocument<128> doc;
        doc["wifi"] = (WiFi.status() == WL_CONNECTED);
        doc["mqtt"] = mqttClient.connected();
        doc["ip"] = WiFi.localIP().toString();
        doc["uptime"] = millis() / 1000;
        String response;
        serializeJson(doc, response);
        request->send(200, "application/json", response);
    });

    // 主页面
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        request->send_P(200, "text/html", index_html);
    });

    // 启动服务器
    server.begin();
    Serial.println("Web server started");
}

// ========== Arduino Setup ==========
void setup() {
    Serial.begin(SERIAL_BAUD);
    Serial.println("\n==================================");
    Serial.println("ESP32 Smart Home System starting...");
    Serial.println("==================================");
    
    // 初始化引脚
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);
    
    // 初始化 DHT 传感器
    dht.begin();
    Serial.println("DHT sensor initialized");
    
    // 生成唯一 Client ID（基础名 + 芯片 MAC 地址后四位）
    uint64_t chipId = ESP.getEfuseMac();
    mqttClientId = String(MQTT_CLIENT_ID_BASE) + "_" + String((uint16_t)(chipId >> 32), HEX) + String((uint32_t)chipId, HEX);
    Serial.print("MQTT Client ID: ");
    Serial.println(mqttClientId);
    
    // 提前初始化 TLS（移出 connectMQTT，一次初始化即可）
    wifiClient.setInsecure();
    Serial.println("[TLS] WiFiClientSecure set to insecure mode");
    
    // Initialize WiFi (non-blocking)
    initWiFi();
    
    // 初始化 Web 服务器
    initWebServer();
    
    // 首次读取传感器
    delay(2000);
    readSensor();
    
    Serial.println("\nSystem startup complete!");
    Serial.print("Web UI: http://");
    Serial.println(WiFi.localIP());
    Serial.println("==================================\n");
}

// ========== Arduino Loop ==========
void loop() {
    unsigned long now = millis();
    
    // 1. Ensure WiFi is connected with an IP
    bool wifiOk = ensureWiFi();
    
    // 2. Only handle MQTT if WiFi is connected with an IP
    if (wifiOk) {
        if (!mqttClient.connected()) {
            if (now - lastMqttReconnect >= MQTT_RECONNECT_INTERVAL) {
                connectMQTT();
                lastMqttReconnect = now;
            }
        } else {
            mqttClient.loop();
            
            // 3. Publish MQTT data periodically
            if (now - lastMqttPublish >= SENSOR_READ_INTERVAL) {
                publishMQTTData();
                lastMqttPublish = now;
            }
        }
    }
    
    // 4. Read sensor periodically (independent of WiFi/MQTT)
    if (now - lastSensorRead >= SENSOR_READ_INTERVAL) {
        readSensor();
        lastSensorRead = now;
    }
}
