import os
from dotenv import load_dotenv
load_dotenv()

matrix_directive = {
        "universal_id": 'matrix',
        "name": "matrix",
        "config": {
            "factories": {
                "reflex.health.status_report": {}
            },
        },
        "filesystem": {
            "folders": [],
            "files": {}
        },

        "children": [{
                "universal_id": "matrix-https",
                "name": "matrix_https",
                "delegated": [],
                "filesystem": {
                    "folders": [],
                    "files": {}
                    }
                },
                {
                    "universal_id": "scavenger-strike",
                    "name": "scavenger",
                    "filesystem": {
                        "folders": []
                    },
                    "config": {}
                },

                {
                    "universal_id": "commander-1",
                    "name": "commander",
                    "children": [
                        {
                            "universal_id": "commander-2",
                            "name": "commander",
                            "children": []
                        },
                    ]
                },
                {
                  "universal_id": "agent_doctor-1",
                  "name": "agent_doctor",
                  "config": {
                    "scan_interval_sec": 20,
                    "max_allowed_beacon_age": 10,
                    "threads_to_check": ["worker", "cmd_listener"]
                  }
                },
                {
                  "universal_id": "health-probe-oracle-1",
                  "name": "agent_health_probe",
                  "config": {
                    "target": "oracle-1",
                    "interval": 5,
                    "stream_to": "websocket-relay"
                  },
                  "filesystem": {},
                  "delegated": []
                },
            {
                "universal_id": "websocket-relay",
                "name": "matrix_websocket",
                "config": {
                    "port": 8765,
                    "factories": {
                        "reflex.health.status_report": {}
                    },
                },
                "filesystem": {},
                "delegated": []
            }
        ]
    }
