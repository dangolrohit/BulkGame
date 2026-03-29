"""
Phusion Passenger entry point for cPanel (Setup Python App).
Set "Application startup file" to: passenger_wsgi.py
"""
from bulkdel.wsgi import application  # noqa: F401
