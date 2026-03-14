import os
from dotenv import load_dotenv

load_dotenv()

# MATRIX CORE DEPLOYMENT
matrix_directive = {
    "universal_id": 'matrix',
    "name": "matrix",
    "filesystem": {
        "folders": [],
        "files": {}
    },

    "children": [

        # MATRIX PROTECTION LAYER 4 SENTINELS
        # 4th SENTINEL WATCHES MATRIX, REST WATCH SENTINEL IN FRONT
        # ONLY WAY TO KILL MATRIX WOULD BE TO KILL THEM ALL, TAKING ANY COMBO OF 4 OUT DOES NOTHING
        {
            "universal_id": "guardian-1",
            "name": "sentinel",
            "app": "matrix-core",
            "filesystem": {},
            "config": {"matrix_secure_verified": 1},
            "children": [
                {
                    "universal_id": "guardian-2",
                    "name": "sentinel",
                    "app": "matrix-core",
                    "filesystem": {},
                    "config": {"matrix_secure_verified": 1},
                    "children": [
                        {
                            "universal_id": "guardian-3",
                            "name": "sentinel",
                            "app": "matrix-core",
                            "filesystem": {},
                            "config": {"matrix_secure_verified": 1},
                            "children": [
                                {
                                    "universal_id": "guardian-4",
                                    "name": "sentinel",
                                    "app": "matrix-core",
                                    "filesystem": {},
                                    "config": {
                                        "matrix_secure_verified": 1,
                                        "watching": "the Queen",
                                        "universal_id_under_watch": "matrix"
                                    }
                                }
                            ]
                        }
                    ]
                }
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
            "universal_id": "matrix-https",
            "name": "matrix_https",
            "delegated": [],
            "app": "matrix-core",
            "filesystem": {
                "folders": [],
                "files": {}
            }
        },
        {
            "universal_id": "scavenger-strike",
            "name": "scavenger",
            "app": "matrix-core",
            "filesystem": {
                "folders": []
            },
            "config": {}
        },

        {
            "universal_id": "commander-1",
            "name": "commander",
            "app": "matrix-core",
            "children": []
        },
        {
            "universal_id": "redis-hammer",
            "name": "redis_watchdog",
            "app": "redis-core",
            "config": {
                "check_interval_sec": 10,
                "restart_limit": 3,
                "redis_port": 6379,
                "always_alert": 1,
                "socket_path": "/var/run/redis/redis-server.sock",
                "service_name": "redis"
            }
            ,
            "children": [

                {
                    "universal_id": "discord-delta",
                    "name": "discord_relay",
                    "app": "mysql-demo",
                    "filesystem": {
                        "folders": []
                    },
                    "config": {
                        "bot_token": os.getenv("DISCORD_TOKEN"),
                        "channel_id": os.getenv("DISCORD_CHANNEL_ID"),
                        "role": "comm",

                    }
                },
                {
                    "universal_id": "telegram-bot-father",
                    "name": "telegram_relay",
                    "app": "mysql-demo",
                    "filesystem": {
                        "folders": []
                    },
                    "config": {
                        "bot_token": os.getenv("TELEGRAM_API_KEY"),
                        "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
                        "role": "comm",

                    }
                },
                {
                    "universal_id": "golden-child-4",
                    "name": "oracle",
                    "app": "blackhole-cometh",
                    "filesystem": {
                        "folders": [],
                        "files": {}
                    },
                    "children": [],
                    "config": {
                        "role": "oracle",
                        "api_key": os.getenv("OPENAI_API_KEY_2"),
                    }

                },

            ]
        },
        {
            "universal_id": "mysql-red-phone",
            "name": "mysql_watchdog",
            "app": "mysql-demo",
            "config": {
                "mysql_port": 3306,
                "socket_path": "/var/run/mysqld/mysqld.sock",
                "service_name": "mariadb",
                "check_interval_sec": 20,
                "restart_limit": 3,
                "alert_thresholds": {
                    "uptime_pct_min": 90,
                    "slow_restart_sec": 10
                },
                "role": "mysql-alarm",  # could be "mariadb" if applicable
            }
            ,
            "children": [

                {
                    "universal_id": "discord-delta-5",
                    "name": "discord_relay",
                    "app": "mysql-demo",
                    "filesystem": {
                        "folders": []
                    },
                    "config": {
                        "bot_token": os.getenv("DISCORD_TOKEN"),
                        "channel_id": os.getenv("DISCORD_CHANNEL_ID"),
                        "role": "comm",

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
                        "role": "comm",

                    }
                },


            ]
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
