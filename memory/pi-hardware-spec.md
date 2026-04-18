# Raspberry Pi Agent — Hardware Spec & Test Plan

## Hardware Profile
| Spec | Detail |
|------|--------|
| **Model** | Raspberry Pi Model B Rev 2 (original!) |
| **CPU** | ARMv6l, 1 core, 700MHz |
| **RAM** | 427MB (311MB available) |
| **Storage** | 3.1GB SD card (852MB free) |
| **OS** | Raspbian, kernel 6.12.47 |
| **Python** | 3.13.5 |
| **Temp** | 49.8°C |

## Available Interfaces
| Interface | Status | Notes |
|-----------|--------|-------|
| **GPIO** (28 pins) | ✅ Ready | gpiod available, 15+ free input pins |
| **SPI** (CE0, CE1) | ⚠️ Disabled | spidev module available, needs config.txt enable |
| **I2C** (SDA1/SCL1) | ⚠️ Disabled | Needs smbus install + config.txt enable |
| **UART** (TX/RX) | ✅ Active | /dev/ttyAMA0, GPIO14/15 in alt0 mode |
| **Audio out** | ✅ Ready | 3.5mm headphone jack + HDMI audio |
| **USB** | ✅ 2 ports | Currently: ethernet adapter only |
| **Ethernet** | ✅ Connected | 192.168.99.25 |
| **Camera (CSI)** | ❌ None | Video devices exist but no camera detected |
| **Bluetooth** | ❌ None | Not available on this model |
| **WiFi** | ❌ None | Not available on this model |

## Software Available
- Python 3.13, curl, wget, aplay, arecord, pinctrl
- gpiod, spidev (Python modules)
- EvoClaw agent running

## What's Missing (can install, ~852MB free)
- RPi.GPIO or lgpio (GPIO control)
- smbus (I2C)
- pyserial (UART)
- paho-mqtt (direct MQTT)
- flask (web server)
- espeak/festival (TTS)
- ffmpeg (media)
