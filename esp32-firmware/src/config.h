#ifndef CONFIG_H
#define CONFIG_H

// ========== WiFi 配置 ==========
// TODO: 修改为您的 WiFi 名称和密码
const char* WIFI_SSID = "yuanye";
const char* WIFI_PASSWORD = "xyzworld";

// ========== MQTT 配置 ==========
// EMQX 免费公有 MQTT Broker，也可以使用您自己的服务器
const char* MQTT_BROKER = "g78ed510.ala.cn-hangzhou.emqxsl.cn";  // 或您的 EMQX 服务器地址
const int MQTT_PORT = 8883;
// 基础 Client ID（setup 中会追加芯片唯一 ID）
const char* MQTT_CLIENT_ID_BASE = "esp32_smart_home";

// MQTT 鉴权（EMQX 公有部署必须填写）
const char* MQTT_USERNAME = "esp32";     // TODO: 请填写您的 EMQX 认证用户名
const char* MQTT_PASSWORD = "xyzworld";     // TODO: 请填写您的 EMQX 认证密码

// MQTT 主题（Topic）
const char* MQTT_TOPIC_TEMP = "smart/home/temperature";      // 温度上报
const char* MQTT_TOPIC_HUM = "smart/home/humidity";          // 湿度上报
const char* MQTT_TOPIC_SWITCH = "smart/home/switch";         // 开关控制（订阅）
const char* MQTT_TOPIC_SWITCH_STATUS = "smart/home/switch/status";  // 开关状态上报
const char* MQTT_TOPIC_HEARTBEAT = "smart/home/heartbeat";   // 心跳

// ========== 引脚配置 ==========
#define DHTPIN 4           // DHT11/DHT22 数据引脚
#define DHTTYPE DHT11      // 如果使用 DHT22，改为 DHT22
#define RELAY_PIN 2        // 继电器控制引脚

// ========== 其他配置 ==========
#define SERIAL_BAUD 115200
#define SENSOR_READ_INTERVAL 5000    // 温湿度读取间隔（毫秒）
#define MQTT_RECONNECT_INTERVAL 5000 // MQTT重连间隔（毫秒）

#endif
