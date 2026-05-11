# Smart Home - ESP32 智能家居控制系统

基于 ESP32 的智能家居项目，实现温湿度采集、远程继电器控制、数据存储与可视化。

## 系统架构

```
ESP32（传感器采集 + 继电器控制）
        │ MQTT
        ▼
EMQX Broker（消息中转）
        │
        ▼
FastAPI 后端（数据处理 + API + WebSocket）
        │
        ▼
Web 前端（实时仪表盘）
```

## 项目结构

```
smart-home/
├── esp32-firmware/          # ESP32 固件（PlatformIO）
│   └── src/
│       ├── main.cpp         # 主程序：采集、MQTT 通信、WebServer
│       └── config.h         # WiFi、MQTT、引脚配置
├── backend/                 # Python 后端服务
│   ├── main.py              # FastAPI 应用入口
│   ├── requirements.txt
│   └── deploy_remote.py     # 远程部署脚本
├── frontend/                # 前端页面
│   └── index.html           # Vue 3 单页应用
└── scripts/                 # 部署与调试脚本
```

## 功能

- **温湿度监测**：DHT11 采集环境温湿度，5 秒轮询
- **远程开关控制**：通过 Web 界面或 MQTT 指令控制继电器
- **数据持久化**：温湿度数据与开关事件写入 SQLite，支持历史查询
- **实时推送**：后端通过 WebSocket 向前端推送状态更新
- **数据可视化**：ECharts 绘制温湿度变化趋势图
- **本地控制**：ESP32 内置 Web 页面，不依赖后端也可直接控制

## 硬件清单

| 组件 | 型号 |
|------|------|
| 主控 | ESP32（WiFi 版本） |
| 温湿度传感器 | DHT11 / DHT22 |
| 继电器模块 | 光耦隔离继电器 |

### 引脚连接

| DHT11 | ESP32 |
|-------|-------|
| VCC   | 3.3V  |
| GND   | GND   |
| DATA  | GPIO4 |

| 继电器 | ESP32 |
|--------|-------|
| VCC    | 5V    |
| GND    | GND   |
| IN     | GPIO2 |

## 快速开始

### 1. ESP32 烧录

使用 PlatformIO 打开 `esp32-firmware` 目录，修改 `src/config.h` 中的配置项：

```cpp
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER = "YOUR_MQTT_BROKER_ADDRESS";
const char* MQTT_USERNAME = "YOUR_MQTT_USERNAME";
const char* MQTT_PASSWORD = "YOUR_MQTT_PASSWORD";
```

编译上传至 ESP32 即可。

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

服务默认运行在 `http://localhost:8000`，API 文档地址为 `http://localhost:8000/docs`。

### 3. 访问前端

前端页面可通过后端地址直接访问，也支持单独部署。

## 技术栈

- **嵌入式**：ESP32 + Arduino Framework（PlatformIO）
- **消息协议**：MQTT（EMQX）
- **后端**：Python FastAPI + SQLAlchemy + SQLite
- **前端**：Vue 3 + ECharts
- **通信**：MQTT（设备到后端）、WebSocket（后端到前端）

## 设计思路

- **MQTT 作为设备与后端的中间层**，降低耦合度，后续新增设备只需订阅/发布对应主题即可
- **ESP32 只负责采集与上报**，数据存储与业务逻辑交由后端处理，减轻设备端负担
- **WebSocket 实时推送**，前端无需轮询即可获取最新数据

## 待优化

- 接入 Home Assistant
- 支持多设备管理
- 用户认证系统
- ESP32 OTA 远程升级
