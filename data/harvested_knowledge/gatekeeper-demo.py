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
            "universal_id": "matrix-https",
            "name": "matrix_https",
            "delegated": [],
            "app": "matrix-core",
            "config": {
                "allowlist_ips": [
                    #'ip',
                    #'ip2'
                ],
                "privkey": "##GENERATE_KEY##",  #optional: can be used to sign all outgoing messages, headed for the gui; PASTE THIS IN THE GUI FOR THE CONNECTION USED
                "remote_pubkey": "<OPTIONAL: PASTE THE PUBKEY GENERATED FROM YOUR matrix_gui HERE>", #optional: verify the signature of all incoming packets. paste pubkey generated from matrix_gui that have or will create

            },
            "filesystem": {
                "folders": [],
                "files": {}
            }
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
            "universal_id": "invisible-man",
            "name": "ghost_wire",
            "config": {
                "tick_rate": 5,
                "watch_paths": [
                    "/etc/passwd",
                    "/etc/shadow",
                    "/root/.ssh",
                    "/var/www",
                    "/home"
                ],
                "command_patterns": [
                    "rm -rf",
                    "scp",
                    "curl",
                    "wget",
                    "nano /etc",
                    "vi /etc",
                    "vim /etc",
                    "sudo",
                    "su",
                    "chmod 777",
                    "service stop",
                ],
            }
        },
        {
          "universal_id": "contact-reflex",
          "name": "contact_reflex",
          "app": "swarm-core",
          "config": {
            "oracle_timeout": 15,
            "watched_paths": [
                  "/some/path/outgoing_msgs/",
                  "/some/path/outgoing_msgs/"
            ],
            "suspended": 0,
            "enable_fallback_forward": 1,
            "enable_oracle": 1,
            "privkey": "##GENERATE_KEY##"
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
            "universal_id": "apache_watchdog-1",
            "name": "apache_watchdog",
            "app": "matrix-core",
            "config": {
                "check_interval_sec": 10,
                "service_name": "httpd",  # change to "httpd" for RHEL/CentOS
                "ports": [80, 443],
                "restart_limit": 3,
                "always_alert": 1,
                "alert_cooldown": 300,
                "report_to_role": "hive.forensics.data_feed",
                "report_handler": "cmd_ingest_status_report"
            },
            "children": [],
            "filesystem": {},
            "delegated": [],
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
            "children": []
        },
        {
            "universal_id": "gatekeeper",
            "name": "gatekeeper",
            "app": "swarm-core",
            "config": {
                "log_path": "/var/log/auth.log",
                "maxmind_db": "GeoLite2-City.mmdb",
                "geoip_enabled": 1,
                "always_alert": 1,
            }
            ,
            "children": []
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
                "role": "mysql-alarm",
                "report_to_role": "hive.forensics.data_feed",
                "report_handler": "cmd_ingest_status_report"
            }
            ,
            "children": []
        },
        {
            "universal_id": "websocket-relay",
            "name": "matrix_websocket",
            "config": {
                "port": 8765,
                "allowlist_ips": [
                    #'ip',
                    #'ip2'
                ],
                "factories": {
                    "reflex.health.status_report": {}
                },
                "service-manager": [{
                    "role": ["hive.alert.send_alert_msg, hive.rpc.route"],
                    "scope": ["parent", "any"],     # who it serves
                    "auth": {"sig": True},
                    "priority": 10,                # lower = more preferred
                    "exclusive": False             # can other services respond?
                }],
                "privkey": "##GENERATE_KEY##",     #optional: can be used to sign all outgoing messages, headed for the gui; PASTE THIS IN THE GUI FOR THE CONNECTION USED
                "remote_pubkey": "<OPTIONAL: PASTE THE PUBKEY GENERATED FROM YOUR matrix_gui HERE>",      #optional: verify the signature of all incoming packets. paste pubkey generated from matrix_gui that have or will create

            },

            "filesystem": {},
            "delegated": []
        },

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
                "service-manager": [{
                    "role": ["comm", "comm.security", "hive.alert.send_alert_msg", "comm.*"],
                    "scope": ["parent", "any"],     # who it serves
                    "auth": {"sig": True},
                    "priority": 10,                # lower = more preferred
                    "exclusive": False             # can other services respond?
                }]
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
        {
            "universal_id": "perm-guardian-1",
            "name": "permissions_guardian",
            "config": {
                "is_cron_job": 1,
                "cron_interval_sec": 300,
                "log_only": 1,
                "targets": [
                    {"path": "agent_path", "dir_mode": 493, "file_mode": 420},
                    {"path": "core_path", "dir_mode": 493, "file_mode": 420},
                    {"path": "comm_path", "dir_mode": 509, "file_mode": 436}
                ]
            }
        },
        {
            "universal_id": "forensic-detective-1",
            "name": "forensic_detective",
            "config": {
                "service-manager": [{
                    "role": ["hive.forensics.data_feed"],
                }],
                "oracle_analysis": {
                    "enable_oracle": 1,
                    "role": "hive.oracle"
                }
            }
            # It will automatically receive reports from agents using its role
        },
        {
            "universal_id": "apache-error-watcher",
            "name": "log_watcher",
            "config": {
                "log_path": "/var/log/httpd/error_log",
                "service_name": "apache.error_log", # Must match the investigator path
                "severity_rules": {
                    "CRITICAL": ["segfault"],
                    "WARNING": ["error", "client denied"]
                },
                "report_to_role": "hive.forensics.data_feed",
                "report_handler": "cmd_ingest_status_report"
            }
        },
        {
            "universal_id": "auth-log-watcher",
            "name": "log_watcher",
            "config": {
                "log_path": "/var/log/secure",
                "service_name": "system.auth_log",
                "severity_rules": {
                    "CRITICAL": ["session opened for user root"],
                    "WARNING": ["failed password", "invalid user"]
                },
                "report_to_role": "hive.forensics.data_feed",
                "report_handler": "cmd_ingest_status_report"

            }
        },
        {
            # Our new, config-driven system health monitor
            "universal_id": "system-health-1",
            "name": "system_health",
            "config": {
                "check_interval_sec": 60,
                "mem_threshold_percent": 90.0,  # Custom threshold
                "cpu_threshold_percent": 85.0,  # Custom threshold
                "disk_threshold_percent": 95.0,
                # It reports to the same data feed as the other watchdogs
                "report_to_role": "hive.forensics.data_feed",
                "report_handler": "cmd_ingest_status_report"
            }
        },
        {
            "universal_id": "network-health-1",
            "name": "network_health",
            "config": {
                "check_interval_sec": 30,  # Check network status every 30 seconds
                "exclude_interfaces": [],  # List of interfaces to skip (e.g. ["lo"])
                "tx_threshold_mbps": 100,  # Warn if outbound rate exceeds 100 Mbps
                "rx_threshold_mbps": 100,  # Warn if inbound rate exceeds 100 Mbps
                "conn_threshold": 1000,  # Warn if active TCP/UDP conns > 1000
                "top_n_procs": 5,  # Include top 5 process hogs in report
                "report_to_role": "hive.forensics.data_feed",
                "report_handler": "cmd_ingest_status_report"
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
                "service-manager": [{
                    "role": ["hive.oracle"],
                }],
                "api_key": os.getenv("OPENAI_API_KEY_2"),
            }

        },
        {
            "universal_id": "storm-crow",
            "name": "storm_crow",
            "delegated": [],
            "description": "Watches for server weather alerts for your area.",
            "config": {
                "zip-code": os.getenv("WEATHER_ZIPCODE"),
                "service-manager": [{
                    "alert-handler": ["hive.alert.send_alert_msg"], #setup discord, telegram, websocket to use this role to receive alerts from storm-crow,
                }]
            }

        },

    ]
}
