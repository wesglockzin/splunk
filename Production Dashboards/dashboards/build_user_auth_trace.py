#!/usr/bin/env python3
"""
Build the User Auth Trace dashboard JSON — Wireshark-style auth flow viewer.

Three panels, two user inputs, one chronological trace:

  Inputs
    - input_global_trp (token: global_time)   default @d,now
    - input_user_sam   (token: user_input)    default *   — sAMAccountName for ADFS / Duo
    - input_user_email (token: user_email)    default *   — Okta email pattern

  Panels
    1. viz_ws1_devices  — WS1 enrolled device(s) for the sAMAccountName user (header strip)
    2. viz_trace_density— timechart count by System (ADFS / Duo / Okta) — event density
    3. viz_trace        — unified normalized event stream across ADFS + Duo + Okta,
                          sorted -_time, columns: Time, System, Event, Subject, Target,
                          Outcome, IP, Detail

  v3 logic is NOT forked. v3 stays untouched as the dedicated ADFS+Duo correlation tool.
  user_auth_trace is a different model — chronological trace, not session correlation.
"""
import json
from pathlib import Path

NAME  = "user_auth_trace"
LABEL = "User Auth Trace"
DESC  = (
    "Wireshark-style chronological trace of authentication events for one user "
    "across ADFS, Duo, and Okta — one normalized stream sorted by time. "
    "Header strip shows the user's enrolled WorkspaceOne device(s) for context. "
    "Defaults to today; both user filters default to wildcard for fleet-mode use."
)

# ---------- searches ----------
# ADFS — token+cred events. v3-style identity matching against $user_input$ and the organization-AD\$user_input$.
ADFS_BASE = (
    'search index=windows_events EventCode IN (1200,1201,1202,1203) '
    '("$user_input$" OR "the organization-AD\\\\$user_input$") '
    '(host=*-ess-sen-adf5* OR host=s-ess-sen-sso1* OR host=s-ess-sen-sso2*) '
    '| rex "Activity ID:\\s*(?<activity_id>[0-9A-Fa-f-]{36})" '
    '| rex field=_raw "<UserId>(?<xml_user>[^<]+)" '
    '| rex field=_raw "<RelyingParty>(?<rp>[^<]+)" '
    '| rex field=_raw "<AuthProtocol>(?<auth_protocol>[^<]+)" '
    '| rex field=_raw "<IpAddress>(?<src_ip>[^<]*)</IpAddress>" '
    '| eval Subject=replace(coalesce(UserId,xml_user),"^the organization-AD\\\\\\\\","") '
    '| eval Event=case(EventCode=1200,"token_issued",EventCode=1201,"token_failed",'
    'EventCode=1202,"cred_ok",EventCode=1203,"cred_failed") '
    '| eval Outcome=if(EventCode IN (1200,1202),"Success","Failure") '
    '| eval System="ADFS" '
    '| eval Target=rp '
    '| eval IP=mvindex(split(coalesce(src_ip,""),","),0) '
    '| eval proto=lower(coalesce(auth_protocol,"")) '
    '| eval Detail=case(match(proto,"oauth"),"OIDC",match(proto,"saml"),"SAML",'
    'match(proto,"wsfed"),"WS-Fed",isnotnull(activity_id),"activity="+activity_id,1=1,"") '
    '| table _time System Event Subject Target Outcome IP Detail'
)

DUO_BASE = (
    'search index=duo username="$user_input$" '
    '| spath '
    '| eval Subject=mvindex(username,0) '
    '| eval factor=mvindex(factor,0) '
    '| eval result=mvindex(result,0) '
    '| eval integration=mvindex(integration,0) '
    '| eval reason=mvindex(reason,0) '
    '| eval IP=coalesce(mvindex(ip,0),mvindex(access_device_ip,0)) '
    '| eval Outcome=case(result="SUCCESS","Success",result="FAILURE","Failure",'
    'result="DENIED","Denied",result="FRAUD","Fraud",isnotnull(result),result,1=1,"") '
    '| eval System="Duo" '
    '| eval Event=if(isnotnull(factor),"mfa","auth") '
    '| eval Target=integration '
    '| eval Detail=trim(coalesce(factor,"")+if(isnotnull(reason) AND reason!="","; "+reason,"")) '
    '| table _time System Event Subject Target Outcome IP Detail'
)

OKTA_BASE = (
    'search index=okta sourcetype=OktaIM2:log host=host.example.gov "$user_email$" '
    'eventType IN (user.authentication.sso,user.authentication.auth_via_mfa,'
    'user.authentication.auth_via_IDP,policy.evaluate_sign_on,user.session.start,'
    'user.authentication.auth_via_AD_agent) '
    '| spath output=Subject path="actor.alternateId" '
    '| spath output=app path="target{0}.displayName" '
    '| spath output=Outcome path="outcome.result" '
    '| spath output=IP path="client.ipAddress" '
    '| spath output=signOnMode path="debugContext.debugData.signOnMode" '
    '| spath output=factor path="debugContext.debugData.factor" '
    '| eval Event=case(eventType="user.authentication.sso","sso",'
    'eventType="user.authentication.auth_via_mfa","mfa",'
    'eventType="user.authentication.auth_via_IDP","via_idp",'
    'eventType="policy.evaluate_sign_on","policy_eval",'
    'eventType="user.session.start","session_start",'
    'eventType="user.authentication.auth_via_AD_agent","ad_agent",1=1,eventType) '
    '| eval Protocol=case(signOnMode="SAML 2.0","SAML",signOnMode="OpenID Connect","OIDC",'
    'isnotnull(signOnMode),signOnMode,1=1,"") '
    '| eval Factor=case(lower(factor)="push" OR factor="OKTA_VERIFY_PUSH","Okta Verify Push",'
    'lower(factor)="signed_nonce" OR factor="SIGNED_NONCE","Passkey/FIDO2",'
    'factor="PASSWORD_AS_FACTOR","Password",factor="OKTA_SOFT_TOKEN","TOTP",'
    'isnotnull(factor),factor,1=1,"") '
    '| eval Detail=trim(Protocol+if(Protocol!="" AND Factor!=""," / ","")+Factor) '
    '| eval System="Okta" '
    '| eval Target=app '
    '| table _time System Event Subject Target Outcome IP Detail'
)

DS = {
    "ds_ws1_devices": (
        'index=ws1_extract sourcetype=csv UserName="$user_input$" '
        '| stats latest(_time) AS lt latest(EnrollmentStatus) AS Status '
        'latest(Model) AS Model latest(SerialNumber) AS Serial latest(Uuid) AS UUID '
        'by UserName, UserEmailAddress '
        '| eval "Last Seen"=strftime(lt,"%Y-%m-%d %H:%M:%S") '
        '| table UserName UserEmailAddress Model Serial UUID Status "Last Seen"'
    ),
    "ds_trace_density": (
        ADFS_BASE + ' | append [' + DUO_BASE + '] | append [' + OKTA_BASE + '] '
        '| timechart span=5m count by System'
    ),
    "ds_trace": (
        ADFS_BASE + ' | append [' + DUO_BASE + '] | append [' + OKTA_BASE + '] '
        '| sort -_time '
        '| eval Time=strftime(_time,"%Y-%m-%d %H:%M:%S") '
        '| table Time System Event Subject Target Outcome IP Detail'
    ),
}

VIZ = {
    "viz_ws1_devices": {
        "containerOptions":{}, "dataSources":{"primary":"ds_ws1_devices"},
        "options":{}, "showLastUpdated":False, "showProgressBar":False,
        "title":"WorkspaceOne Enrolled Device(s)", "type":"splunk.table",
    },
    "viz_trace_density": {
        "containerOptions":{}, "dataSources":{"primary":"ds_trace_density"},
        "options":{"stackMode":"stacked"},
        "showLastUpdated":False, "showProgressBar":False,
        "title":"Event Density by System (5-min buckets)", "type":"splunk.column",
    },
    "viz_trace": {
        "containerOptions":{}, "dataSources":{"primary":"ds_trace"},
        "options":{}, "showLastUpdated":False, "showProgressBar":False,
        "title":"Auth Trace — chronological, all systems", "type":"splunk.table",
    },
}

# Layout: 2700 wide canvas. Header strip 140h, density 220h, trace 620h. Total 1000h.
LAYOUT = [
    {"item":"viz_ws1_devices",  "position":{"h":140,"w":2700,"x":0,"y":  0}, "type":"block"},
    {"item":"viz_trace_density","position":{"h":220,"w":2700,"x":0,"y":160}, "type":"block"},
    {"item":"viz_trace",        "position":{"h":620,"w":2700,"x":0,"y":400}, "type":"block"},
]

def studio_json():
    return {
        "title": LABEL,
        "description": DESC,
        "inputs": {
            "input_global_trp": {
                "options":{"defaultValue":"@d,now","token":"global_time"},
                "title":"Global Time Range", "type":"input.timerange",
            },
            "input_user_sam": {
                "options":{"defaultValue":"*","token":"user_input"},
                "title":"User (sAMAccountName) — for ADFS / Duo / WS1",
                "type":"input.text",
            },
            "input_user_email": {
                "options":{"defaultValue":"*","token":"user_email"},
                "title":"User (Okta email) — for Okta",
                "type":"input.text",
            },
        },
        "defaults":{
            "dataSources":{"ds.search":{"options":{"queryParameters":{
                "earliest":"$global_time.earliest$",
                "latest":"$global_time.latest$",
            }}}}
        },
        "visualizations": VIZ,
        "dataSources": {
            ds_id: {"options":{
                "query": q,
                "queryParameters":{
                    "earliest":"$global_time.earliest$",
                    "latest":"$global_time.latest$",
                },
            }, "type":"ds.search"}
            for ds_id, q in DS.items()
        },
        "layout":{
            "globalInputs":["input_global_trp","input_user_sam","input_user_email"],
            "layoutDefinitions":{"layout_1":{
                "options":{"display":"auto","height":1040,"width":2700},
                "structure":LAYOUT, "type":"absolute",
            }},
            "tabs":{"items":[{"label":"Trace","layoutId":"layout_1"}]},
        },
    }

def make_eai_data():
    studio = json.dumps(studio_json())
    return (
        f'<dashboard version="2" theme="light">\n'
        f'    <label>{LABEL}</label>\n'
        f'    <description>{DESC}</description>\n'
        f'    <definition><![CDATA[{studio}]]></definition>\n'
        f'    <meta type="hiddenElements"><![CDATA[\n'
        f'{{\n\t"hideEdit": false,\n\t"hideOpenInSearch": false,\n\t"hideExport": false\n}}\n'
        f'    ]]></meta>\n'
        f'</dashboard>'
    )

def make_export():
    return {
        "links":{},"origin":"","updated":"",
        "generator":{"build":"manual","version":"9.4.3"},
        "entry":[{
            "name":NAME,"id":"","updated":"","links":{},
            "author":"your-username",
            "acl":{"app":"search","owner":"your-username","sharing":"user"},
            "fields":{"required":["eai:data"],"optional":[],"wildcard":[]},
            "content":{
                "description":DESC,"disabled":False,"eai:acl":None,
                "eai:appName":"search","eai:data":make_eai_data(),
                "eai:type":"views","eai:userName":"your-username",
                "isDashboard":True,"isVisible":True,"label":LABEL,
                "rootNode":"dashboard","version":"2",
            },
        }],
        "paging":{"total":1,"perPage":30,"offset":0},"messages":[],
    }

if __name__ == "__main__":
    out = Path(__file__).parent / f"{NAME}.json"
    out.write_text(json.dumps(make_export(), indent=2))
    print(f"Wrote {out}")
