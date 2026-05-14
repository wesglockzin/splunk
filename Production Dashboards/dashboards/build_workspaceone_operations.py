#!/usr/bin/env python3
"""
Build the WorkspaceOne: Operations Overview dashboard JSON.

Produces dashboards/workspaceone_operations_overview.json in the same shape
import_dashboard.py expects (Splunk EAI export with eai:data containing the
dashboard XML wrapper + Studio v2 JSON inside CDATA).
"""
import json
from pathlib import Path

NAME  = "workspaceone_operations_overview"
LABEL = "WorkspaceOne: Operations Overview"
DESC  = (
    "Operational health for the WorkspaceOne / AirWatch on-prem stack: "
    "device check-ins, HTTP health on the WS1 console, top API endpoints, "
    "failing requests, Tunnel latency, and service-side errors."
)

# ---------- searches ----------
# Time tokens come from the global timerange input (default -24h@h,now).
DS = {
    # KPIs
    "ds_kpi_events": "index=airwatch | stats count AS total",
    "ds_kpi_devices": (
        "index=airwatch sourcetype=iis deviceId=* "
        "| stats dc(deviceId) AS total"
    ),
    "ds_kpi_success": (
        "index=airwatch sourcetype=iis status>0 "
        "| eval ok=if(status>=200 AND status<400,1,0) "
        "| stats sum(ok) AS ok count AS total "
        "| eval rate=if(total>0,round(ok/total*100,2),0) "
        "| table rate"
    ),
    "ds_kpi_5xx": (
        "index=airwatch sourcetype=iis status>=500 | stats count AS total"
    ),

    # Server health
    "ds_volume_by_host": (
        "index=airwatch "
        "| timechart span=1h count by host"
    ),

    # HTTP status bucket trend
    "ds_status_trend": (
        "index=airwatch sourcetype=iis "
        "| eval bucket=case("
        "status>=500,\"5xx server error\","
        "status>=400,\"4xx client error\","
        "status>=300,\"3xx redirect\","
        "status>=200,\"2xx success\","
        "1=1,\"1xx/0\") "
        "| timechart span=15m count by bucket"
    ),

    # Top URIs (drop the chatty cache-validation /api/system/groups/<uuid> noise)
    "ds_top_uri": (
        "index=airwatch sourcetype=iis cs_uri_stem!=\"/\" "
        "| rex field=cs_uri_stem \"^(?<uri_norm>/api/system/groups/)[0-9a-f-]{36}.*\" "
        "| eval uri_show=coalesce(uri_norm,cs_uri_stem) "
        "| stats count by cs_method, uri_show "
        "| sort -count "
        "| head 15 "
        "| rename cs_method AS Method, uri_show AS URI, count AS Requests"
    ),

    # Failing endpoints
    "ds_fail_endpoints": (
        "index=airwatch sourcetype=iis status>=400 "
        "| stats count by status, cs_method, cs_uri_stem "
        "| sort -count "
        "| head 20 "
        "| rename status AS Status, cs_method AS Method, "
        "cs_uri_stem AS URI, count AS Count"
    ),

    # Device check-in mix from User-Agent. Limited to requests with a deviceId
    # to exclude internal service-to-service traffic (Faraday, Vert.x, splunksvc, etc.).
    "ds_platform_mix": (
        "index=airwatch sourcetype=iis deviceId=* cs_User_Agent!=\"-\" "
        "| eval platform=case("
        "match(cs_User_Agent,\"(?i)Android\"),\"Android\","
        "match(cs_User_Agent,\"(?i)iOS\"),\"iOS\","
        "match(cs_User_Agent,\"Darwin\"),\"macOS\","
        "match(cs_User_Agent,\"(?i)Windows\"),\"Windows\","
        "match(cs_User_Agent,\"^MDM/\"),\"Apple (MDM protocol)\","
        "match(cs_User_Agent,\"AppleExchangeWebServices\"),\"Apple (EWS)\","
        "match(cs_User_Agent,\"(?i)Mozilla|Chrome|Safari|Firefox|Edge\"),\"Browser\","
        "1=1,\"Other\") "
        "| stats count by platform "
        "| sort -count "
        "| rename platform AS Platform, count AS Count"
    ),

    # Tunnel latency
    "ds_tunnel_latency": (
        "index=airwatch sourcetype=*ws1.tunnel.kestrel* "
        "| spath path=\"context.elapsed\" output=elapsed_raw "
        "| rex field=elapsed_raw \"(?<elapsed_ms>\\d+)\" "
        "| eval elapsed_ms=tonumber(elapsed_ms) "
        "| where isnotnull(elapsed_ms) "
        "| timechart span=15m perc95(elapsed_ms) AS p95_ms perc99(elapsed_ms) AS p99_ms"
    ),

    # Service-side errors (level=Error rows in DeviceServices/Compliance/etc.)
    "ds_service_errors": (
        "index=airwatch ("
        "sourcetype=ComplianceService OR sourcetype=DeviceServicesLog-* "
        "OR sourcetype=AW.IntegrationService-* OR sourcetype=ChangeEventOutboundQueueService "
        "OR sourcetype=EntityReconcileService-* OR sourcetype=InterrogatorQueueService-* "
        "OR sourcetype=MessagingServiceLog-* OR sourcetype=VMware.UEM.DesiredStateManagement "
        "OR sourcetype=AirWatch.UEM.MetadataTransformService-*) "
        "| rex \"^\\d{4}/\\d{2}/\\d{2} \\d{2}:\\d{2}:\\d{2}\\.\\d+\\t\\S+\\t\\S+\\t\\S+\\s+\\(\\s*\\d+\\s*\\)\\s+(?<level>\\S+)\\t(?<method>\\S+)\" "
        "| where level=\"Error\" "
        "| stats count AS errors by sourcetype, method "
        "| sort -errors "
        "| head 25 "
        "| rename sourcetype AS Sourcetype, method AS Method, errors AS Errors"
    ),
}

# ---------- visualizations ----------
def kpi(ds, title, color=None):
    options = {"sparklineDisplay": "off", "trendDisplay": "off"}
    if color:
        options["majorColor"] = color
    return {
        "containerOptions": {},
        "dataSources": {"primary": ds},
        "options": options,
        "showLastUpdated": False,
        "showProgressBar": False,
        "title": title,
        "type": "splunk.singlevalue",
    }

def chart(ds, title, vtype, options=None):
    return {
        "containerOptions": {},
        "dataSources": {"primary": ds},
        "options": options or {},
        "showLastUpdated": False,
        "showProgressBar": False,
        "title": title,
        "type": vtype,
    }

VIZ = {
    "viz_kpi_events":  kpi("ds_kpi_events",  "Events Ingested"),
    "viz_kpi_devices": kpi("ds_kpi_devices", "Distinct Devices"),
    "viz_kpi_success": kpi("ds_kpi_success", "HTTP Success %"),
    "viz_kpi_5xx":     kpi("ds_kpi_5xx",     "HTTP 5xx", color="#c12f28"),

    "viz_volume_by_host":  chart("ds_volume_by_host",  "Events by Host", "splunk.area"),
    "viz_status_trend":    chart("ds_status_trend",    "HTTP Status (15-min buckets)", "splunk.column", {"stackMode": "stacked"}),
    "viz_top_uri":         chart("ds_top_uri",         "Top API Endpoints (chatty group GETs collapsed)", "splunk.table"),
    "viz_fail_endpoints":  chart("ds_fail_endpoints",  "Top Failing Endpoints (status >= 400)", "splunk.table"),
    "viz_platform_mix":    chart("ds_platform_mix",    "Device Platform Mix (from User-Agent)", "splunk.pie"),
    "viz_tunnel_latency":  chart("ds_tunnel_latency",  "WS1 Tunnel API Latency p95/p99 (ms)", "splunk.line"),
    "viz_service_errors":  chart("ds_service_errors",  "Service-Side Errors (top method × sourcetype)", "splunk.table"),
}

# ---------- layout (canvas 2100w) ----------
LAYOUT = [
    # Row 1 — KPIs
    {"item": "viz_kpi_events",      "position": {"h": 160, "w": 510, "x":    0, "y":   0}, "type": "block"},
    {"item": "viz_kpi_devices",     "position": {"h": 160, "w": 510, "x":  520, "y":   0}, "type": "block"},
    {"item": "viz_kpi_success",     "position": {"h": 160, "w": 510, "x": 1040, "y":   0}, "type": "block"},
    {"item": "viz_kpi_5xx",         "position": {"h": 160, "w": 540, "x": 1560, "y":   0}, "type": "block"},
    # Row 2 — server volume
    {"item": "viz_volume_by_host",  "position": {"h": 320, "w":2100, "x":    0, "y": 170}, "type": "block"},
    # Row 3 — HTTP status + top URIs
    {"item": "viz_status_trend",    "position": {"h": 380, "w":1040, "x":    0, "y": 500}, "type": "block"},
    {"item": "viz_top_uri",         "position": {"h": 380, "w":1050, "x": 1050, "y": 500}, "type": "block"},
    # Row 4 — failing endpoints + platforms
    {"item": "viz_fail_endpoints",  "position": {"h": 380, "w":1390, "x":    0, "y": 890}, "type": "block"},
    {"item": "viz_platform_mix",    "position": {"h": 380, "w": 700, "x": 1400, "y": 890}, "type": "block"},
    # Row 5 — tunnel latency + service errors
    {"item": "viz_tunnel_latency",  "position": {"h": 360, "w":1040, "x":    0, "y":1280}, "type": "block"},
    {"item": "viz_service_errors",  "position": {"h": 360, "w":1050, "x": 1050, "y":1280}, "type": "block"},
]

# ---------- assemble ----------
def make_studio_json():
    return {
        "title": LABEL,
        "description": DESC,
        "inputs": {
            "input_global_trp": {
                "options": {"defaultValue": "-24h@h,now", "token": "global_time"},
                "title": "Time Range",
                "type": "input.timerange",
            }
        },
        "defaults": {
            "dataSources": {
                "ds.search": {
                    "options": {
                        "queryParameters": {
                            "earliest": "$global_time.earliest$",
                            "latest":   "$global_time.latest$",
                        }
                    }
                }
            }
        },
        "visualizations": VIZ,
        "dataSources": {
            ds_id: {
                "options": {
                    "query": query,
                    "queryParameters": {
                        "earliest": "$global_time.earliest$",
                        "latest":   "$global_time.latest$",
                    },
                },
                "type": "ds.search",
            }
            for ds_id, query in DS.items()
        },
        "layout": {
            "globalInputs": ["input_global_trp"],
            "layoutDefinitions": {
                "layout_1": {
                    "options": {"display": "auto", "height": 1660, "width": 2100},
                    "structure": LAYOUT,
                    "type": "absolute",
                }
            },
            "tabs": {"items": [{"label": "Operations", "layoutId": "layout_1"}]},
        },
    }

def make_eai_data():
    studio = json.dumps(make_studio_json())
    xml = (
        f'<dashboard version="2" theme="light">\n'
        f'    <label>{LABEL}</label>\n'
        f'    <description>{DESC}</description>\n'
        f'    <definition><![CDATA[{studio}]]></definition>\n'
        f'    <meta type="hiddenElements"><![CDATA[\n'
        f'{{\n\t"hideEdit": false,\n\t"hideOpenInSearch": false,\n\t"hideExport": false\n}}\n'
        f'    ]]></meta>\n'
        f'</dashboard>'
    )
    return xml

def make_export():
    return {
        "links": {},
        "origin": "",
        "updated": "",
        "generator": {"build": "manual", "version": "9.4.3"},
        "entry": [{
            "name": NAME,
            "id": "",
            "updated": "",
            "links": {},
            "author": "your-username",
            "acl": {"app": "search", "owner": "your-username", "sharing": "user"},
            "fields": {"required": ["eai:data"], "optional": [], "wildcard": []},
            "content": {
                "description": DESC,
                "disabled": False,
                "eai:acl": None,
                "eai:appName": "search",
                "eai:data": make_eai_data(),
                "eai:type": "views",
                "eai:userName": "your-username",
                "isDashboard": True,
                "isVisible": True,
                "label": LABEL,
                "rootNode": "dashboard",
                "version": "2",
            },
        }],
        "paging": {"total": 1, "perPage": 30, "offset": 0},
        "messages": [],
    }

if __name__ == "__main__":
    out = Path(__file__).parent / f"{NAME}.json"
    out.write_text(json.dumps(make_export(), indent=2))
    print(f"Wrote {out}")
