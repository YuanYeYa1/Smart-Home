# 🏠 ESP32 智能家居控制系统

基于 **ESP32 + DHT11/DHT22 + 继电器 + EMQX MQTT + Python FastAPI + Vue.js** 的远程智能开关与温湿度监测系统。

## 📋 功能特性

- ✅ **温湿度实时监测** — DHT11/DHT22 传感器数据采集
- ✅ **远程开关控制** — 继电器控制，支持本地和远程切换
- ✅ **本地 Web 控制** — 浏览器访问 ESP32 IP 直接控制
- ✅ **云端数据存储** — Python 后端存储温湿度历史数据
- ✅ **数据可视化** — 温湿度历史趋势 ECharts 图表
- ✅ **实时推送** — WebSocket 实时更新数据
- ✅ **PWA 支持** — 可添加到手机桌面，像 App 一样使用

## 🗂️ 项目结构

```
smart-home/
├── esp32-firmware/          # ESP32 PlatformIO 固件
│   ├── src/
│   │   ├── main.cpp         # 主程序（含内嵌 Web 页面）
│   │   └── config.h         # WiFi/MQTT/引脚配置
│   └── platformio.ini       # PlatformIO 项目配置
├── backend/                 # Python 后端服务
│   ├── main.py              # FastAPI 应用入口
│   └── requirements.txt     # Python 依赖
├── frontend/                # Web 前端
│   └── index.html           # 独立 HTML（Vue3 + ECharts）
└── README.md
```

## 🔧 硬件接线

### 所需硬件
| 硬件 | 数量 | 说明 |
|------|------|------|
| ESP32 开发板 | 1 | 主控芯片 |
| DHT11 / DHT22 | 1 | 温湿度传感器 |
| 继电器模块 | 1 | 控制开关（5V供电） |
| 面包板 + 杜邦线 | 若干 | 连接线路 |

### 接线图

```
DHT11/DHT22 → ESP32
  VCC(3.3V)  → 3.3V
  GND        → GND
  DATA       → GPIO4

继电器模块 → ESP32
  VCC(5V)    → VIN (5V)
  GND        → GND
  IN(信号)   → GPIO2
```

> ⚠️ **注意**: 如果使用 DHT22，修改 `config.h` 中的 `DHTTYPE` 为 `DHT22`

## 🚀 快速开始

### 第一步：烧录 ESP32 固件

1. 安装 **VS Code** + **PlatformIO** 插件
2. 在 VS Code 中打开 `smart-home/esp32-firmware` 文件夹
3. 编辑 `src/config.h`，修改以下配置：
   - `WIFI_SSID` — 您的 WiFi 名称
   - `WIFI_PASSWORD` — 您的 WiFi 密码
   - `MQTT_BROKER` — 如果不想用公共 Broker，改成您的 EMQX 地址
4. 点击 PlatformIO 的 **→ (Upload and Monitor)** 按钮烧录
5. 打开串口监视器，查看 ESP32 输出的 IP 地址

### 第二步：启动后端服务

```bash
# 进入后端目录
cd smart-home/backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

后端服务将在 `http://localhost:8000` 运行。
API 文档：`http://localhost:8000/docs`

### 第三步：访问控制面板

| 方式 | 地址 | 说明 |
|------|------|------|
| **本地控制** | `http://<ESP32_IP>` | 直接访问 ESP32 内置页面 |
| **远程控制** | `http://localhost:8000` | 通过后端访问（推荐） |
| **后端前端** | `smart-home/frontend/index.html` | 直接用浏览器打开 |

## 📡 MQTT 主题说明

| 主题 | 方向 | 说明 |
|------|------|------|
| `smart/home/temperature` | ESP32 → 后端 | 温度数据（JSON: `{"value":25.5,"unit":"°C"}`） |
| `smart/home/humidity` | ESP32 → 后端 | 湿度数据（JSON: `{"value":60,"unit":"%"}`） |
| `smart/home/switch` | 后端 → ESP32 | 开关控制（JSON: `{"state":true}`） |
| `smart/home/switch/status` | 双向 | 开关状态（JSON: `{"state":true}`） |
| `smart/home/heartbeat` | ESP32 → 后端 | 心跳包 |

## 🌐 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/sensor/current` | 获取当前温湿度 |
| `GET` | `/api/sensor/history?limit=100` | 获取历史数据 |
| `GET` | `/api/switch` | 获取开关状态 |
| `POST` | `/api/switch` | 控制开关 `{"state": true}` |
| `GET` | `/api/switch/history?limit=50` | 获取开关记录 |
| `GET` | `/api/status` | 获取系统状态 |
| `WS` | `/ws` | WebSocket 实时推送 |

## 📱 手机访问

1. **本地访问**：手机连接同一 WiFi，浏览器输入 ESP32 的 IP 地址
2. **远程访问**：将后端部署到云服务器，通过公网 IP 访问
3. **PWA 支持**：在 Chrome/Safari 中打开页面，选择"添加到主屏幕"

## 🔄 数据流程

```
┌─────────────────────────────────────────────────────────────┐
│                       系统架构图                             │
│                                                             │
│  ┌──────────┐    WiFi     ┌────────────┐     MQTT     ┌──┐ │
│  │ DHT11    │◄───GPIO────►│            │◄────────────►│  │ │
│  │ 传感器    │             │   ESP32    │              │EM│ │
│  │ 继电器    │◄───GPIO────►│  (主控)    │◄────────────►│QX│ │
│  └──────────┘             │            │              │  │ │
│                            │  WebServer │              │Mq│ │
│                            │  (端口80)  │              │tt│ │
│                            └─────┬──────┘              │  │ │
│                                  │                     └──┘ │
│                                  │ HTTP                     │
│                                  ▼                          │
│  ┌────────────────────────────────────────┐                │
│  │      浏览器 / 手机 App                  │                │
│  │  ┌──────┐  ┌────────┐  ┌───────────┐  │                │
│  │  │ 本地  │  │ 远程   │  │ 数据分析  │  │                │
│  │  │ 控制  │  │ 控制   │  │ 可视化    │  │                │
│  │  └──────┘  └────────┘  └───────────┘  │                │
│  └────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ 进阶配置

### 修改传感器类型
编辑 `esp32-firmware/src/config.h`：
```cpp
#define DHTTYPE DHT11   // 改为 DHT22 如果您使用 DHT22
```

### 修改继电器引脚
```cpp
#define RELAY_PIN 2     // 改为其他 GPIO 引脚编号
```

### 使用私有 EMQX 服务器
```cpp
const char* MQTT_BROKER = "your-emqx-server.com";  // 修改为您的服务器地址
```

## 📜 许可证

MIT License
