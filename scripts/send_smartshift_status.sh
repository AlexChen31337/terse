#!/bin/bash
MESSAGE='🔋 **SmartShift Status Report** - Sat Apr 25, 8:40 PM AEDT

**Battery:** 74% SOC  
**Mode:** self_consumption (discharging 921W to load)  
**Solar:** 0W (nighttime)  
**Current Prices:** Buy 23.9c/kWh | Feed-in 8.05c/kWh  

**AI Advisor Strategy:** HOLD  
- Current feed-in (8.05c) below export threshold (9.1c)  
- Better export window at 18:00 tomorrow: 10.47c, ~3.25kWh planned  
- Expected profit today: 56.5c  
- Next export window: 8:00 AM tomorrow, expected earn 34c  

**Today'\''s Summary:**  
- Exported: 14.8 kWh  
- Imported: 1.34 kWh  
- Battery available: 5.4 kWh  

System operating normally. Holding charge for better export window tomorrow morning.'

curl -s -X POST "http://localhost:7437/api/v1/messages" \
  -H "Content-Type: application/json" \
  -d "{\"channel\": \"telegram\", \"target\": \"2069029798\", \"message\": \"$MESSAGE\"}"
