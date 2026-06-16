"""Gunicorn configuration for the contact diary application."""

import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
accesslog = "-"
errorlog = "-"
capture_output = True
loglevel = "info"
timeout = 180
