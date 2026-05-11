# 🏠 ESP32 智能家居控制系统 — 完整原理解释

> 对找实习有帮助的重点内容会标注 ⭐

---

## 一、系统架构总览 ⭐

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           整体架构（三层）                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  用户浏览器（前端）
  Vue 3 + ECharts + WebSocket
        ↕ HTTP / WebSocket
  阿里云服务器（后端）
  FastAPI + SQLite + paho-mqtt
        ↕ MQTT (TLS/8883)
  家中的 ESP32（设备端）
  Arduino + WiFi + DHT11 + 继电器
```

这是一个典型的 **物联网（IoT）三层架构**：

| 层级 | 技术 | 作用 |
|------|------|------|
| **设备层** | ESP32 + 传感器 | 采集环境数据、执行物理操作 |
| **平台层** | 阿里云服务器 + FastAPI | 数据处理、存储、转发 |
| **应用层** | 浏览器 Vue 页面 | 可视化展示、远程控制 |

### 为什么用云服务器而非局域网？⭐
这是面试常问的问题。本项目经历了两个阶段：

1. **初期：ESP32 自带 Web 服务器** — 只能在内网访问，手机出门就没法用
2. **升级后：云服务器中转** — ESP32 通过 MQTT 连上云端的 EMQX Broker，用户在公网访问云服务器上的 Web 页面，实现了**真正的远程控制**

> 面试点：能解释清楚"为什么需要云端"而不是"ESP32 自己就能当服务器"

---

## 二、数据流详解（这是最核心的）⭐

### 2.1 传感器数据上报（设备 → 云端 → 页面）

```
ESP32 每 5 秒读取 DHT11 温湿度
    │
    ▼
发布 MQTT 消息到 EMQX Broker
  主题: smart/home/temperature → {"value": 28.1, "unit": "°C"}
  主题: smart/home/humidity    → {"value": 30, "unit": "%"}
    │
    ▼
阿里云上的 Python 后端已订阅这些主题
收到消息后：
  ① 更新内存中的 DeviceState（最新状态）
  ② 存入 SQLite 数据库（历史记录）
  ③ 通过 WebSocket 推送到浏览器
    │
    ▼
用户浏览器实时显示温湿度
```

**关键设计点**：
- **MQTT 是异步的发布/订阅模型**，ESP32 不用管谁在收数据，只需往主题发消息
- **SQLite 存历史数据**用于图表展示，**内存 DeviceState** 存最新状态用于实时显示
- **WebSocket 推送**比轮询效率高，数据变化立即通知前端

### 2.2 远程控制（页面 → 云端 → 设备）

```
用户在浏览器点击开关
    │
    ▼
前端发送 HTTP POST 到 /api/switch
  body: {"state": true}
    │
    ▼
后端收到请求：
  ① 通过 MQTT 发布指令
     主题: smart/home/switch → {"state": true}
  ② 记录操作到 SQLite
    │
    ▼
ESP32 通过 MQTT 收到指令
  ① 控制继电器引脚 (GPIO 2)
  ② 发布状态回执
     主题: smart/home/switch/status → {"state": true}
    │
    ▼
后端收到回执，更新状态，推送到前端
```

---

## 三、核心技术栈详解 ⭐

### 3.1 ESP32 端（C++ / Arduino Framework）

**使用的库**：
| 库 | 用途 |
|----|------|
| `WiFi.h` | 连接 WiFi |
| `WiFiClientSecure` | TLS 加密连接（MQTT 8883 端口必须） |
| `PubSubClient` | MQTT 客户端 |
| `ArduinoJson` | JSON 序列化/反序列化 |
| `DHT.h` | DHT11/DHT22 温湿度传感器驱动 |
| `ESPAsyncWebServer` | 局域网 Web 界面（备用） |

**关键代码逻辑**（`main.cpp` 中的 `loop()` 函数）：
```
loop():
  1. ensureWiFi()     → 保持 WiFi 连接
  2. connectMQTT()    → 连接到 EMQX 云端
  3. mqttClient.loop() → 处理 MQTT 消息（非阻塞）
  4. readSensor()     → 读取 DHT11 数据
  5. publishMQTTData() → 发布温湿度到 MQTT
```

### 3.2 后端（Python / FastAPI）⭐

**为什么用 FastAPI？**
- ⭐ **异步框架** — 同时处理 HTTP、WebSocket、MQTT，高并发场景性能好
- ⭐ 自动生成 API 文档（访问 `/docs` 就能看到 Swagger 文档）
- ⭐ Pydantic 模型自动参数校验

**后端同时运行三种协议**：
| 协议 | 端口 | 用途 |
|------|------|------|
| HTTP | 8000 | REST API（获取数据、控制开关） |
| WebSocket | 8000 | 实时推送温度更新到页面 |
| MQTT | 8883（作为客户端） | 与 ESP32 通讯（通过 EMQX Broker） |

**数据库设计**：
```
sensor_data 表：
  id, temperature, humidity, timestamp
  → 用于历史曲线图

switch_events 表：
  id, state, source, timestamp
  → 用于开关操作记录
  source 字段: "api"（网页控制）或 "mqtt"（物理开关）
```

### 3.3 前端（Vue 3 + ECharts）

**技术点**：
- ⭐ **Vue 3 Composition API**（`ref`、`onMounted` 等）
- ⭐ **WebSocket 实时通信** — 建立长连接，后端主动推数据
- ⭐ **ECharts 图表** — 温湿度历史趋势折线图
- 响应式 CSS（支持手机和电脑）

**前端数据获取策略**：
```
① WebSocket 长连接 — 实时接收推送（主要）
   ② 定时轮询（10秒）— WebSocket 断连时的补充
```

### 3.4 MQTT 协议详解 ⭐

这是面试中 IoT 方向的高频考点。

**MQTT 特点**：
- **发布/订阅模型** — 解耦生产者和消费者
- **QoS 级别**（本项目用默认 QoS 0）
- **保留消息** — 新客户端订阅时能收到最后一条消息
- **遗嘱消息（Will Message）** — 检测设备异常离线

**本项目 MQTT 主题设计**：
```
smart/home/temperature       ← ESP32 发布温度
smart/home/humidity          ← ESP32 发布湿度
smart/home/switch            → ESP32 订阅（接收控制指令）
smart/home/switch/status     ← ESP32 发布开关状态
smart/home/heartbeat         ← ESP32 发布心跳
```

### 3.5 EMQX Cloud（公有 MQTT Broker）⭐

**为什么用它？**
- ESP32 在家庭内网，云服务器在公网，两者不能直接互联
- EMQX 作为**云端中转站**，ESP32 和云服务器都主动连接到它
- MQTT 是 TCP 长连接 + TLS 加密，EMQX 8883 端口提供加密传输

```
  ESP32 ──TLS──→ EMQX Cloud ──TLS──→ 阿里云后端
    ↑               ↑                   ↑
  家庭内网        公网中继            公网服务器
```

---

## 四、部署架构 ⭐

```
                用户访问
                   │
                   ▼
            阿里云 ECS 服务器
          (8.137.21.211:8000)
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    FastAPI     SQLite     WebSocket
    后端        数据库      实时推送
        │
        ▼
  systemd 管理进程（开机自启、崩溃重启）
        │
        ▼
  UFW 防火墙 → 放行 8000 端口
        │
        ▼
  阿里云安全组 → 放行 8000 端口（独立于服务器防火墙）
```

**部署相关技术**：
| 技术 | 用途 |
|------|------|
| ⭐ **systemd** | Linux 守护进程管理，`systemctl restart smart-home-backend` |
| ⭐ **SSH + SFTP** | 远程连接服务器、上传文件 |
| **UFW** | Ubuntu 防火墙管理 |
| **阿里云安全组** | 云平台的网络访问控制（容易被忽略！） |

---

## 五、面试重点总结 ⭐

### 5.1 简历上可以写的内容

```
智能家居控制系统 | Python + FastAPI + ESP32 + MQTT + Vue 3

• 设计并实现了一套完整的 IoT 系统，涵盖设备端（ESP32/C++）、
  服务端（FastAPI/SQLite）、前端（Vue 3/ECharts）三层架构
• 基于 MQTT 协议实现 ESP32 与云端服务器的双向通信，
  使用 TLS 加密传输（8883端口）
• 利用 WebSocket 实现服务器→浏览器的实时数据推送，
  替代传统轮询方案，降低延迟和带宽消耗
• 部署在阿里云 ECS，使用 systemd 管理进程生命周期
• 解决 MQTT 连接不稳定导致的设备状态闪烁问题
```

### 5.2 面试可能问的高频问题

**1. 为什么选 MQTT 而不是 HTTP？**
> MQTT 是轻量级发布/订阅协议，适合 IoT 场景。HTTP 是请求/响应模型，服务器不能主动推数据给设备。MQTT 的 TCP 长连接 + 心跳保活更适合嵌入式设备。

**2. WebSocket 和轮询的区别？**
> 轮询是前端定时发 HTTP 请求，浪费带宽且有延迟。WebSocket 建立双向长连接，数据变化时服务器主动推送。

**3. 怎么保证 ESP32 不掉线？**
> 心跳机制（每5秒发传感器数据也算心跳）、WiFi 掉线自动重连、MQTT 自动重连。

**4. TLS 是什么？为什么用 8883 端口？**
> TLS（传输层安全协议）加密 MQTT 通信，防止数据被中间人窃取。EMQX 公有部署的 8883 端口是 MQTT over TLS。

**5. 数据库为什么用 SQLite 而不是 MySQL？**
> 轻量级，单文件，无需独立数据库服务。本项目的并发量用 SQLite 完全够。

**6. 项目有什么改进空间？**
> - 添加用户认证（JWT）
> - 用 Redis 替代 SQLite 做实时状态缓存
> - 多条 ESP32 设备支持
> - HTTPS 证书（Nginx 反向代理）
> - Docker 容器化部署

---

## 六、遇到的问题与解决方案（面试加分项）⭐

| 问题 | 根因 | 解决 |
|------|------|------|
| 外网无法访问 | 阿里云安全组没放行 8000 端口 | 在阿里云控制台添加规则 |
| 时间显示差8小时 | 后端 UTC 时间没标注 `Z`，浏览器误当本地时间 | ISO 时间戳加 `Z` 后缀 |
| 设备在线状态反复横跳 | MQTT 断开时后端立即标记离线，但短暂断开会自动重连 | 改为收到消息才标记在线，断开不标记离线 |
| MQTT TLS 连接失败 | 证书验证问题 | ESP32 用 `setInsecure()` 跳过证书验证 |

---

## 七、文件结构

```
smart-home/
├── backend/
│   ├── main.py              # FastAPI 后端主程序（所有逻辑在这里）
│   ├── smart_home.db        # SQLite 数据库文件
│   ├── static/
│   │   └── index.html       # Vue 3 前端页面
│   └── requirements.txt     # Python 依赖
│
├── esp32-firmware/
│   ├── src/
│   │   ├── main.cpp         # ESP32 主程序
│   │   └── config.h         # WiFi / MQTT 配置
│   ├── platformio.ini       # PlatformIO 项目配置
│   └── .gitignore
│
├── deploy.bat / deploy.py   # 部署脚本
└── README.md
```

---

> 💡 **提示**：面试时不要背所有细节，重点讲清楚：
> 1. **整体架构**（三层 + 数据流）
> 2. **为什么选这些技术**（MQTT 适合 IoT、FastAPI 异步高性能）
> 3. **碰到过什么问题，怎么解决的**（外网访问、时间、状态闪烁）


