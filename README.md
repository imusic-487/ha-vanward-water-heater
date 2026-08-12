# Home Assistant 万和热水器集成

简体中文 | [English](README.en.md)

> **Fork 声明**：本仓库 fork 自 [orangeboyChen/ha-vanward-water-heater](https://github.com/orangeboyChen/ha-vanward-water-heater)，在完整保留原版功能的基础上，新增**电热水器**支持。欢迎反馈问题或提交 PR。

这是一个用于万和热水器的 Home Assistant 自定义集成。原版插件主要面向**燃气热水器**，本 fork 在此基础上增加了**电热水器**（如 E60-Q2WY10-20）的支持。

## 与上游的差异

### 新增：电热水器支持
- `protocol.py`：根据设备类型自动识别燃气/电热两种状态布局。电热水器状态载荷仅有 27 个字段（无 gas_usage / water_flowing / fan 等燃气专属属性），此前会直接报 `ValueError: Status payload does not contain the expected fields`
- `water_heater.py`：电热水器新增当前水温读取（`current_temperature`）
- 燃气热水器行为完全不变

**已实测**：Home Assistant 2026.7.4 + 万和 E60-Q2WY10-20（60L 电热水器），集成正常加载、水温读取正常。

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

## HomeKit 接入

通过 HomeKit 桥（HASS Bridge）配对后，热水器会以 **WaterHeater（热水器）** 配件出现在家庭 App 中，可查看水温、目标温度与操作模式。

**注意**：WaterHeater 配件自带当前水温特征，iOS 家庭 App 会把它和其他温度设备一起显示在"温度"分类中——这是 HomeKit 的正常设计，并非错误。

**如不希望水温出现在"环境温度"汇总里**：

1. 打开家庭 App → 找到热水器配件
2. 长按卡片 → 设置（齿轮）
3. 关闭 **"包含在家庭摘要中"（Include in Home Summaries）**

热水器卡片上的水温不受影响，照常显示。

## 免责声明

本项目是非官方社区集成，与万和官方无关联，也不受万和官方支持或背书。请自行承担使用风险。设备行为、云端连接和兼容性可能随时变化。

## 协议

MIT
