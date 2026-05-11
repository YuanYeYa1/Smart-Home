# ESP32 Smart Home Control System

一个基于 ESP32 的轻量级智能家居系统，用于实现**温湿度采集 + 远程继电器控制 + Web 可视化监控**。

这个项目的初衷是：  
在没有智能家居网关的情况下，自己搭一个“能在手机上控制灯 + 查看温湿度”的完整 IoT 系统。

---

## 📌 项目特点

- 📡 ESP32 实时采集温湿度（DHT11 / DHT22）
- 🔌 继电器控制家电开关（本地 + 远程）
- 🌐 ESP32 内置 Web 页面（局域网直连控制）
- 📊 Python FastAPI 后端记录历史数据
- 📈 Vue + ECharts 实现数据可视化
- 🔄 MQTT 实现设备与云端解耦通信
- 📱 手机浏览器直接访问，无需安装 App

---

## 🧠 系统架构

```
ESP32（数据采集 + 控制）
        ↓ MQTT
EMQX Broker（消息中转）
        ↓
FastAPI 后端（数据存储 + API）
        ↓
Web 前端（可视化 + 控制界面）
```

---

## 🗂️ 项目结构

```bash
smart-home/
├── esp32-firmware/     # ESP32 固件（PlatformIO）
│   ├── src/main.cpp    # 主程序（采集 + MQTT + WebServer）
│   └── config.h        # WiFi / MQTT / GPIO 配置
│
├── backend/            # Python 后端
│   ├── main.py         # FastAPI 服务入口
│   └── requirements.txt
│
├── frontend/           # Web 前端
│   └── index.html      # Vue + ECharts 页面
│
└── README.md
```

---

## 🔧 硬件连接

### DHT11 / DHT22

| 引脚 | ESP32 |
|------|------|
| VCC  | 3.3V |
| GND  | GND |
| DATA | GPIO4 |

---

### 继电器模块

| 引脚 | ESP32 |
|------|------|
| VCC  | 5V |
| GND  | GND |
| IN   | GPIO2 |

⚠️ 建议使用带光耦隔离的继电器模块，避免电压干扰

---

## ⚙️ 快速开始

### 1️⃣ ESP32 烧录

使用 PlatformIO 打开 `esp32-firmware`

修改配置：

```cpp
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define MQTT_BROKER "YOUR_MQTT_BROKER_ADDRESS"
```

---

## 🚀 后续优化方向

- ：接入 Home Assistant
- : 支持多设备管理
- : 用户登录系统
- : ESP32 OTA 升级

---

## 🧰 技术栈

- ESP32（Arduino / PlatformIO）
- MQTT（EMQX）
- FastAPI
- Vue 3
- ECharts
- WebSocket
```
