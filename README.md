# Home Assistant 万和热水器集成

简体中文 | [English](README.en.md)

> **Fork 声明**：本仓库 fork 自 [orangeboyChen/ha-vanward-water-heater](https://github.com/orangeboyChen/ha-vanward-water-heater)，在完整保留原版功能的基础上，新增**电热水器**支持。欢迎反馈问题或提交 PR。

这是一个用于万和热水器的 Home Assistant 自定义集成。原版插件主要面向**燃气热水器**，本 fork 在此基础上增加了**电热水器**（如 E60-Q2WY10-20）的支持。

## 与上游的差异

### 新增：电热水器支持（v3.1）
- `protocol.py`：根据设备类型自动识别燃气/电热两种状态布局。电热水器状态载荷仅有 27 个字段（无 gas_usage / water_flowing / fan 等燃气专属属性），此前会直接报 `ValueError: Status payload does not contain the expected fields`
- **电热模式码表**：普通(1) / 中温(2) / 抑菌(10) / 增容(12) / ECO峰谷(32) / e-push(35)，读写双向映射（e-push 带自动断电标志时读值为 43，显示归一到 e-push）
- **双轨读写**：模式读写走 `Status[4]`、温度走 `Status[6]`，与燃气布局（模式在 `Status[1]`）自动区分，两套布局互不干扰
- **温度范围**：电热水器 35–75°C（燃气版为 30–65°C），按设备类型自适应
- `water_heater.py`：电热水器新增当前水温读取（`current_temperature`）
- **新增 4 个电热传感器**：当前水温 / 目标温度 / 当前模式 / 电源状态
- **功能位掩码**：自动断电等标志位按位读写，带注释说明，避免误写其他位
- **设备离线检测（v3.2）**：解析登录响应中的 `isOnline` 字段（万和 App「设备离线」同源），设备离线时实体自动变为 `unavailable`，HA 与 HomeKit 桥同步显示离线，不再残留过期缓存状态；无 `isOnline` 字段的老版本 payload 默认视为在线，不误判
- 燃气热水器行为完全不变

**已实测**：Home Assistant 2026.7.4 + 万和 E60-Q2WY10-20（60L 电热水器），集成正常加载、水温读取正常、6 个实体全部工作。

**已知限制**：
- 仅实测 E60-Q2WY10-20 一个型号，其他电热型号（不同容量/新款）未验证
- 燃气专属实体（实时产水量/实时耗气量/总耗气量/总耗水量）在电热水器上仍会注册，但恒为 0.0
- 详见上游 issue：[#1 电热水器（E60-Q2WY10-20）支持建议 + 补丁代码](https://github.com/orangeboyChen/ha-vanward-water-heater/issues/1)

## 安装

通过 HACS 自定义仓库安装：

1. 打开 Home Assistant 中的 HACS。
2. 进入 `Integrations`。
3. 打开右上角菜单，选择 `Custom repositories`。
4. 添加仓库（如需电热水器支持，请使用本 fork）：

```text
https://github.com/imusic-487/ha-vanward-water-heater
```

> 提示：安装原版（仅燃气热水器）请添加 `https://github.com/orangeboyChen/ha-vanward-water-heater`。

5. 分类选择 `Integration`。
6. 安装 `Vanward Water Heater`。
7. 重启 Home Assistant。

## 使用

安装后进入：

```text
设置 -> 设备与服务 -> 添加集成
```

搜索 `Vanward Water Heater`，并按照配置流程完成添加。

电热水器新增的 4 个传感器（当前水温/目标温度/当前模式/电源状态）添加后自动出现，可直接用于仪表盘、自动化或趋势图。

## HomeKit 接入

通过 HomeKit 桥（HASS Bridge）配对后，热水器会以 **WaterHeater（热水器）** 配件出现在家庭 App 中，可查看水温、目标温度与操作模式。

**注意**：
- HomeKit 协议中热水器仅暴露"关闭 / 升温"两种加热状态（协议限制，非插件问题）；抑菌 / ECO峰谷 / e-push 等模式请在 HA 中选择
- HomeKit 桥中的操作是**双向控制**：在家庭 App 里调目标温度、开关设备，都会真实下发到热水器
- WaterHeater 配件自带当前水温特征，iOS 家庭 App 会把它和其他温度设备一起显示在"温度"分类中——这是 HomeKit 的正常设计，并非错误

**如不希望水温出现在"环境温度"汇总里**：

1. 打开家庭 App → 找到热水器配件
2. 长按卡片 → 设置（齿轮）
3. 关闭 **"包含在家庭摘要中"（Include in Home Summaries）**

**关于电热传感器与 HomeKit**：当前水温/目标温度等传感器（sensor 域）默认会被 HomeKit 桥接为独立温度配件，若不需要可在 HomeKit 桥配置中将对应实体加入排除列表（`exclude_entities`）。

## 更新记录

### 2026-08-13
- **新增（v3.2）**：设备离线检测——解析登录响应的 `isOnline` 字段（万和 App「设备离线」同源），设备离线时实体自动变为 `unavailable`，HA 与 HomeKit 桥同步显示离线，不再残留过期缓存状态；老 payload 无此字段时默认在线不误判
- **新增（v3.2）**：4 个离线判断测试用例（在线/离线/缺字段兼容/默认值），测试总数 33 → 37
- **新增（v3.1）**：电热模式码表（普通/中温/抑菌/增容/ECO峰谷/e-push）读写双向映射；模式/温度双轨读写（电热 Status[4]/Status[6]）；温度范围 35–75°C 自适应；功能位掩码按位读写
- **新增（v3.1）**：4 个电热传感器——当前水温 / 目标温度 / 当前模式 / 电源状态
- **修复**：代码审查发现的 3 个 CRITICAL + 3 个 MAJOR 问题（模式读取位置、电热模式码表、幽灵实体隐藏、温度范围、e-push 标志、补测试）
- **HomeKit**：电热传感器默认桥接为独立温度配件，可通过桥配置排除

### 2026-08-12
- **修复（无代码改动）**：HomeKit 环境温度汇总中包含热水器水温的问题，通过 iOS 家庭 App 关闭「包含在家庭摘要中 / Include in Home Summaries」解决（详见上方 HomeKit 接入小节）
- **说明**：曾尝试移除 `number.py` 中巡航温度实体的 `device_class=temperature`，经评估后回退——该实体未被 HomeKit 暴露（Number 域不在包含列表），改动对解决问题无实际作用，且可能影响其他依赖此分类的用户，故保持与上游一致
- **文档**：README 重构为中英双语（中文主文件 + 独立英文版）

### 2026-08-11
- **新增**：电热水器支持（E60-Q2WY10-20）——27 字段状态布局自动识别 + 当前水温读取

## 免责声明

本项目是非官方社区集成，与万和官方无关联，也不受万和官方支持或背书。本集成通过分析设备本地通信协议实现，不包含任何厂商专有代码或资源。请自行承担使用风险。设备行为、云端连接和兼容性可能随时变化。

## 协议

MIT
