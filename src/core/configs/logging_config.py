from logging.config import dictConfig

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console_formatter': {
            'format': '%(asctime)s [%(levelname)s] (%(name)s): %(message)s',
        },
        'file_formatter': {
            'format': '%(asctime)s [%(levelname)s] (%(name)s/%(funcName)s:%(lineno)s): %(message)s',
        }
    },
    'handlers': {
        'console_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'console_formatter',
            'level': 'DEBUG',
        },
        'file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'file_formatter',
            'level': 'DEBUG',
            'filename': 'logs/app/app.log',
            'maxBytes': 10_000_000,
            'backupCount': 5,
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console_handler', 'file_handler']
    },
    'loggers': {
        'app': {
            'level': 'DEBUG',
            'handlers': ['console_handler', 'file_handler'],
            'propagate': False,
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console_handler', 'file_handler'],
            'propagate': False,
        },
    }
}


def setup_logging():
    dictConfig(LOGGING_CONFIG)
