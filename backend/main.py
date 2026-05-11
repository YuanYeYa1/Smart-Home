"""
ESP32 智能家居 - Python 后端服务
技术栈: FastAPI + SQLite + MQTT (paho-mqtt)
"""

import json
import time
import asyncio
import os
from datetime import datetime
from typing import Optional

import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# ========== 配置 ==========
MQTT_BROKER = "g78ed510.ala.cn-hangzhou.emqxsl.cn"  # 或您的 EMQX 服务器地址
MQTT_PORT = 8883

# MQTT 鉴权（EMQX 公有部署必须填写，需与 ESP32 配置一致）
MQTT_USERNAME = "esp32"     # TODO: 请填写您的 EMQX 认证用户名
MQTT_PASSWORD = "xyzworld"     # TODO: 请填写您的 EMQX 认证密码

MQTT_TOPIC_TEMP = "smart/home/temperature"
MQTT_TOPIC_HUM = "smart/home/humidity"
MQTT_TOPIC_SWITCH = "smart/home/switch"
MQTT_TOPIC_SWITCH_STATUS = "smart/home/switch/status"
MQTT_TOPIC_HEARTBEAT = "smart/home/heartbeat"

DATABASE_URL = "sqlite:///./smart_home.db"

# ========== 数据库设置 ==========
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SensorData(Base):
    """温湿度传感器数据表"""
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class SwitchEvent(Base):
    """开关事件记录表"""
    __tablename__ = "switch_events"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    state = Column(Boolean, nullable=False)
    source = Column(String(50), default="manual")
    timestamp = Column(DateTime, default=datetime.utcnow)

# 创建表
Base.metadata.create_all(bind=engine)

# ========== FastAPI 应用 ==========
app = FastAPI(title="ESP32 智能家居控制系统", version="1.0.0")

# CORS 设置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（前端页面）
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"📁 静态文件目录已挂载: {STATIC_DIR}")

# ========== 全局状态 ==========
class DeviceState:
    """设备状态（内存中维护最新状态）"""
    def __init__(self):
        self.temperature: float = 0.0
        self.humidity: float = 0.0
        self.switch_state: bool = False
        self.mqtt_connected: bool = False
        self.device_online: bool = False
        self.last_update: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None

device_state = DeviceState()

# ========== WebSocket 连接管理 ==========
class ConnectionManager:
    """管理 WebSocket 连接，实现实时推送"""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """广播消息到所有连接的客户端"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# ========== MQTT 客户端 ==========
class MQTTHandler:
    """MQTT 消息处理器"""
    
    def __init__(self):
        self.client = mqtt.Client(client_id="python_backend_server")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self._running = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ MQTT Broker 连接成功!")
            device_state.mqtt_connected = True
            
            # 订阅相关主题
            client.subscribe(MQTT_TOPIC_TEMP)
            client.subscribe(MQTT_TOPIC_HUM)
            client.subscribe(MQTT_TOPIC_SWITCH_STATUS)
            client.subscribe(MQTT_TOPIC_HEARTBEAT)
            print(f"📡 已订阅主题: {MQTT_TOPIC_TEMP}, {MQTT_TOPIC_HUM}, {MQTT_TOPIC_SWITCH_STATUS}, {MQTT_TOPIC_HEARTBEAT}")
        else:
            print(f"❌ MQTT 连接失败，返回码: {rc}")
            device_state.mqtt_connected = False

    def on_disconnect(self, client, userdata, rc):
        print("⚠️ MQTT 断开连接")
        device_state.mqtt_connected = False
        # 注意：不在这里设 device_online = False！
        # 后端到 EMQX 的连接短暂断开会自动重连，不代表 ESP32 设备离线

    def on_message(self, client, userdata, msg):
        """处理收到的 MQTT 消息"""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)
            
            print(f"📩 收到 MQTT [{topic}]: {payload}")
            
            db = SessionLocal()
            
            # 收到任何设备发来的消息，都标记为在线
            now = datetime.utcnow()
            device_state.device_online = True
            
            if topic == MQTT_TOPIC_TEMP:
                device_state.temperature = data.get("value", 0.0)
                device_state.last_update = now
                
            elif topic == MQTT_TOPIC_HUM:
                device_state.humidity = data.get("value", 0.0)
                device_state.last_update = now
                
            elif topic == MQTT_TOPIC_SWITCH_STATUS:
                device_state.switch_state = data.get("state", False)
                device_state.last_update = now
                
                # 记录开关事件到数据库
                switch_event = SwitchEvent(
                    state=device_state.switch_state,
                    source="mqtt"
                )
                db.add(switch_event)
                db.commit()
                
            elif topic == MQTT_TOPIC_HEARTBEAT:
                device_state.device_online = True
                device_state.last_heartbeat = datetime.utcnow()
                device_state.mqtt_connected = True
                print(f"💓 设备心跳: {data}")
            
            # 当同时收到温度和湿度后，保存到数据库
            if topic in [MQTT_TOPIC_TEMP, MQTT_TOPIC_HUM]:
                # 检查是否同时有温度和湿度数据
                if device_state.temperature > 0 and device_state.humidity > 0:
                    sensor_record = SensorData(
                        temperature=device_state.temperature,
                        humidity=device_state.humidity
                    )
                    db.add(sensor_record)
                    db.commit()
            
            db.close()
            
            # 广播最新状态到 WebSocket 客户端
            asyncio.run(manager.broadcast({
                "type": "sensor_update",
                "temperature": device_state.temperature,
                "humidity": device_state.humidity,
                "switch_state": device_state.switch_state,
                "device_online": device_state.device_online,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }))
            
        except json.JSONDecodeError:
            print(f"⚠️ MQTT 消息 JSON 解析失败: {payload}")
        except Exception as e:
            print(f"❌ MQTT 消息处理错误: {e}")

    def publish_switch(self, state: bool):
        """发布开关控制指令"""
        payload = json.dumps({"state": state})
        result = self.client.publish(MQTT_TOPIC_SWITCH, payload)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"📤 已发送开关指令: {'ON' if state else 'OFF'}")
            return True
        else:
            print(f"❌ 开关指令发送失败")
            return False

    def start(self):
        """启动 MQTT 客户端"""
        if self._running:
            return
        self._running = True
        try:
            # Set authentication credentials
            if MQTT_USERNAME:
                self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

            # TLS 配置（EMQX 8883 端口需要）
            self.client.tls_set()  # 使用系统 CA 证书验证 EMQX 服务端
            # 如果连接失败，可以尝试 tls_set(insecure=True) 跳过证书验证
            # 但生产环境建议保留证书验证

            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            print("🔄 MQTT 客户端已启动")
        except Exception as e:
            print(f"❌ MQTT 启动失败: {e}")
            self._running = False

    def stop(self):
        """停止 MQTT 客户端"""
        if not self._running:
            return
        self._running = False
        self.client.loop_stop()
        self.client.disconnect()
        print("🛑 MQTT 客户端已停止")

# 创建全局 MQTT 处理器
mqtt_handler = MQTTHandler()

# ========== API 数据模型 ==========
class SwitchControl(BaseModel):
    """开关控制请求"""
    state: bool

class SensorResponse(BaseModel):
    """传感器数据响应"""
    temperature: float
    humidity: float
    timestamp: Optional[str] = None

class SwitchStatusResponse(BaseModel):
    """开关状态响应"""
    state: bool
    source: Optional[str] = None
    timestamp: Optional[str] = None

class SystemStatusResponse(BaseModel):
    """系统状态响应"""
    temperature: float
    humidity: float
    switch_state: bool
    mqtt_connected: bool
    device_online: bool
    last_update: Optional[str] = None
    last_heartbeat: Optional[str] = None

# ========== API 路由 ==========

@app.on_event("startup")
async def startup():
    """应用启动时初始化 MQTT"""
    mqtt_handler.start()

@app.on_event("shutdown")
async def shutdown():
    """应用关闭时停止 MQTT"""
    mqtt_handler.stop()

@app.get("/")
async def serve_frontend():
    """根路径 - 返回前端页面"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {
        "message": "ESP32 智能家居控制系统",
        "version": "1.0.0",
        "docs": "/docs"
    }

# ----- 传感器 API -----

@app.get("/api/sensor/current", response_model=SensorResponse)
async def get_current_sensor():
    """获取当前温湿度数据"""
    return SensorResponse(
        temperature=device_state.temperature,
        humidity=device_state.humidity,
timestamp=(device_state.last_update.isoformat() + "Z") if device_state.last_update else None
    )

@app.get("/api/sensor/history")
async def get_sensor_history(limit: int = 100):
    """获取温湿度历史记录"""
    db = SessionLocal()
    records = db.query(SensorData).order_by(SensorData.timestamp.desc()).limit(limit).all()
    db.close()
    
    return [
        {
            "temperature": r.temperature,
            "humidity": r.humidity,
            "timestamp": r.timestamp.isoformat() + "Z"
        }
        for r in reversed(records)  # 按时间正序返回
    ]

# ----- 开关 API -----

@app.get("/api/switch", response_model=SwitchStatusResponse)
async def get_switch_status():
    """获取当前开关状态"""
    return SwitchStatusResponse(
        state=device_state.switch_state,
        timestamp=(device_state.last_update.isoformat() + "Z") if device_state.last_update else None
    )

@app.post("/api/switch", response_model=SwitchStatusResponse)
async def control_switch(control: SwitchControl):
    """控制开关"""
    # 通过 MQTT 发送控制指令
    success = mqtt_handler.publish_switch(control.state)
    if not success and not device_state.device_online:
        raise HTTPException(status_code=503, detail="设备不在线，无法发送控制指令")
    
    # 记录开关事件
    db = SessionLocal()
    switch_event = SwitchEvent(
        state=control.state,
        source="api"
    )
    db.add(switch_event)
    db.commit()
    db.close()
    
    device_state.switch_state = control.state
    
    return SwitchStatusResponse(
        state=control.state,
        source="api",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )

@app.get("/api/switch/history")
async def get_switch_history(limit: int = 50):
    """获取开关历史记录"""
    db = SessionLocal()
    records = db.query(SwitchEvent).order_by(SwitchEvent.timestamp.desc()).limit(limit).all()
    db.close()
    
    return [
        {
            "state": r.state,
            "source": r.source,
            "timestamp": r.timestamp.isoformat() + "Z"
        }
        for r in reversed(records)
    ]

# ----- 系统状态 API -----

@app.get("/api/status", response_model=SystemStatusResponse)
async def get_system_status():
    """获取系统整体状态"""
    return SystemStatusResponse(
        temperature=device_state.temperature,
        humidity=device_state.humidity,
        switch_state=device_state.switch_state,
        mqtt_connected=device_state.mqtt_connected,
        device_online=device_state.device_online,
        last_update=(device_state.last_update.isoformat() + "Z") if device_state.last_update else None,
        last_heartbeat=(device_state.last_heartbeat.isoformat() + "Z") if device_state.last_heartbeat else None
    )

# ----- WebSocket API（实时推送）-----

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 实时数据推送"""
    await manager.connect(websocket)
    print(f"🟢 WebSocket 客户端已连接 (总连接数: {len(manager.active_connections)})")
    
    try:
        # 发送当前状态
        await websocket.send_json({
            "type": "sensor_update",
            "temperature": device_state.temperature,
            "humidity": device_state.humidity,
            "switch_state": device_state.switch_state,
            "device_online": device_state.device_online,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # 保持连接，等待消息
        while True:
            data = await websocket.receive_text()
            # 处理客户端发来的消息（心跳等）
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"🔴 WebSocket 客户端已断开 (总连接数: {len(manager.active_connections)})")

# ========== 主入口 ==========
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 ESP32 智能家居后端服务启动中...")
    print("📡 MQTT Broker: " + MQTT_BROKER)
    print("🌐 API 文档: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
