#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 Chrome DevTools Protocol (CDP) 直接連接到已開啟的 Chrome 並提取 Highcharts 數據
"""

import json
import requests
import websocket
import time

CDP_PORT = 9222

# 提取 Highcharts 數據的 JavaScript
EXTRACT_HIGHCHARTS_JS = '''
(function() {
    if (typeof Highcharts === 'undefined' || !Highcharts.charts) {
        return JSON.stringify({error: 'Highcharts not found'});
    }

    var charts = Highcharts.charts.filter(c => c !== undefined && c !== null);
    if (charts.length === 0) {
        return JSON.stringify({error: 'No charts found'});
    }

    var result = [];
    for (var i = 0; i < charts.length; i++) {
        var chart = charts[i];
        var chartInfo = {
            title: chart.title ? chart.title.textStr : 'Chart ' + i,
            series: []
        };

        for (var j = 0; j < chart.series.length; j++) {
            var s = chart.series[j];
            var seriesData = [];

            if (s.xData && s.xData.length > 0) {
                for (var k = 0; k < s.xData.length; k++) {
                    seriesData.push({
                        x: s.xData[k],
                        y: s.yData[k],
                        date: new Date(s.xData[k]).toISOString().split('T')[0]
                    });
                }
            } else if (s.data && s.data.length > 0) {
                seriesData = s.data.map(function(point) {
                    return {
                        x: point.x,
                        y: point.y,
                        date: point.x ? new Date(point.x).toISOString().split('T')[0] : null
                    };
                });
            }

            chartInfo.series.push({
                name: s.name,
                type: s.type,
                dataLength: seriesData.length,
                data: seriesData
            });
        }
        result.push(chartInfo);
    }
    return JSON.stringify(result);
})()
'''


def get_ws_url():
    """獲取 WebSocket 調試 URL"""
    try:
        resp = requests.get(f'http://127.0.0.1:{CDP_PORT}/json')
        pages = resp.json()
        # 找到 MacroMicro 頁面
        for page in pages:
            if 'macromicro' in page.get('url', '').lower():
                return page.get('webSocketDebuggerUrl')
        # 如果沒找到，返回第一個頁面
        if pages:
            return pages[0].get('webSocketDebuggerUrl')
    except Exception as e:
        print(f"Error getting WS URL: {e}")
    return None


def execute_js(ws_url, js_code):
    """通過 CDP 執行 JavaScript"""
    ws = websocket.create_connection(ws_url)

    # 發送執行命令
    cmd = {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": js_code,
            "returnByValue": True
        }
    }
    ws.send(json.dumps(cmd))

    # 接收結果
    result = json.loads(ws.recv())
    ws.close()

    return result


def main():
    print("正在連接到 Chrome...")
    ws_url = get_ws_url()

    if not ws_url:
        print("無法找到 Chrome 頁面，請確保 Chrome 已開啟並訪問了 MacroMicro")
        return

    print(f"WebSocket URL: {ws_url}")

    print("\n正在提取 Highcharts 數據...")
    result = execute_js(ws_url, EXTRACT_HIGHCHARTS_JS)

    if 'result' in result and 'result' in result['result']:
        value = result['result']['result'].get('value')
        if value:
            data = json.loads(value)
            if isinstance(data, dict) and 'error' in data:
                print(f"錯誤: {data['error']}")
            else:
                print(f"\n成功提取 {len(data)} 個圖表!")
                for chart in data:
                    print(f"\n圖表: {chart.get('title', 'Unknown')}")
                    for series in chart.get('series', []):
                        name = series.get('name', 'Unknown')
                        count = series.get('dataLength', 0)
                        print(f"  - {name}: {count} 個數據點")
                        if count > 0:
                            last_point = series['data'][-1]
                            print(f"    最新: {last_point.get('date')} = {last_point.get('y')}")

                # 保存到文件
                output_file = "cache/cass_freight_cdp.json"
                import os
                os.makedirs("cache", exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n數據已保存到: {output_file}")
        else:
            print(f"無法獲取值: {result}")
    else:
        print(f"執行失敗: {result}")


if __name__ == "__main__":
    main()
