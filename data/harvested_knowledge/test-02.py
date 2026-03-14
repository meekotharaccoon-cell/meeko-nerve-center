import os
from dotenv import load_dotenv
load_dotenv()

matrix_directive = {
        "universal_id": 'matrix',
        "name": "matrix",
        "children": [

                {
                "universal_id": "matrix-https",
                "name": "matrix_https",
                "delegated": [],
                "filesystem": {
                    "folders": [],
                    "files": {}
                    }
                },
                {
                    "universal_id": "commander-2",
                    "name": "commander",
                    "children": []
                },
                {
                    "universal_id": "email-check-1",
                    "name": "email_check",
                    "filesystem": {
                        "folders": []
                    },
                    "config": {
                        "imap_host": os.getenv("EMAILCHECKAGENT_IMAP_HOST"),
                        "email": os.getenv("EMAILCHECKAGENT_EMAIL"),
                        "password": os.getenv("EMAILCHECKAGENT_PASSWORD"),
                        "report_to": os.getenv("EMAILCHECKAGENT_REPORT_TO", "mailman-1"),
                        "interval": int(os.getenv("EMAILCHECKAGENT_INTERVAL", 60))
                    }
                },
                {
                    "universal_id": "mirror-9",
                    "name": "filesystem_mirror",
                    "filesystem": {
                        "folders": []
                    },
                    "config": {
                        "watch_path": "/etc",
                        "mode": "once",
                        "self_destruct": True,
                        "report_to": "mailman-1"
                    }
                }
                ,
                {
                    "universal_id": "email-send-1",
                    "name": "email_send",
                    "filesystem": {
                        "folders": []
                    },
                    "config": {
                        "smtp_host": os.getenv("EMAILSENDAGENT_SMTP_HOST"),
                        "smtp_port": os.getenv("EMAILSENDAGENT_SMTP_PORT"),
                        "email": os.getenv("EMAILSENDAGENT_SMTP_EMAIL"),
                        "password": os.getenv("EMAILSENDAGENT_PASSWORD")
                    }
                },
                {
                    "universal_id": "commander-1",
                    "name": "commander",
                    "children": []
                },
                {
                    "universal_id": "worker-backup-2",
                    "name": "worker",
                    "directives": {
                        "do something": ["sentinel-root"],
                        "do something else": ["something else"]
                    },
                    "children": [
                              {
                                "universal_id": "logger-1",
                                "name": "logger",
                                "children": [
                                  {
                                    "universal_id": "logger-2",
                                    "name": "logger",
                                    "children": [
                                      {
                                        "universal_id": "logger-3",
                                        "name": "logger",
                                        "children": [
                                          {
                                            "universal_id": "logger-4",
                                            "name": "logger",
                                            "children": [

                                                {
                                                    "universal_id": "worker-backup-3",
                                                    "name": "worker",
                                                    "children": []
                                                }
                                            ]
                                          },
                                            {
                                                "universal_id": "email-check-1",
                                                "name": "email_check",
                                                "filesystem": {
                                                    "folders": []
                                                },
                                                "config": {
                                                    "imap_host": os.getenv("EMAILCHECKAGENT_IMAP_HOST"),
                                                    "email": os.getenv("EMAILCHECKAGENT_EMAIL"),
                                                    "password": os.getenv("EMAILCHECKAGENT_PASSWORD"),
                                                    "report_to": os.getenv("EMAILCHECKAGENT_REPORT_TO", "mailman-1"),
                                                    "interval": int(os.getenv("EMAILCHECKAGENT_INTERVAL", 60))
                                                }

                                        }]
                                      }
                                    ]
                                  }
                                ]
                              }
                            ]
                }
        ]
    }
