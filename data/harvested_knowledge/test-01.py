import os
from dotenv import load_dotenv
load_dotenv()

matrix_directive = {

        "universal_id": 'matrix',
        "name": "matrix",
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
                "universal_id": "websocket-relay",
                "name": "matrix_websocket",
                "config": {
                    "port": 8765,
                    "factories": {
                        "reflex.health.status_report": {}
                    },
                    "service-manager": [{
                        "role": ["hive.alert.send_alert_msg, hive.rpc.route"],
                        "scope": ["parent", "any"],     # who it serves
                        "auth": {"sig": True},
                        "priority": 10,                # lower = more preferred
                        "exclusive": False             # can other services respond?
                    }]
                },
                "filesystem": {},
                "delegated": []
                },
            {
                "universal_id": "soulmate-express",
                "name": "load_range",
                "delegated": [],
                "filesystem": {
                    "folders": [],
                    "files": {}
                    }

            },
            {
                "universal_id": "storm-crow",
                "name": "storm_crow",
                "delegated": [],
                "filesystem": {
                    "folders": [],
                    "files": {}
                    }

            },
{
            "universal_id": "telegram-bot-father-2",
            "name": "telegram_relay",
            "app": "mysql-demo",
            "filesystem": {
                "folders": []
            },
            "config": {
                "bot_token": os.getenv("TELEGRAM_API_KEY"),
                "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
                "service-manager": [{
                    "role": ["comm", "comm.security", "comm.*, hive.alert.send_alert_msg"],
                    "scope": ["parent", "any"],     # who it serves
                    "auth": {"sig": True},
                    "priority": 10,                # lower = more preferred
                    "exclusive": False             # can other services respond?
                }]
            }
        },
        ]
    }
