# Cowrie Sensor

Cowrie is the first planned honeypot sensor for OpenThreatGrid.

## Purpose

Collect SSH/Telnet brute-force and command execution telemetry.

## Initial Data Points

- Source IP
- Username attempts
- Password attempts
- Session duration
- Commands
- File download attempts

## Safety Notes

Run Cowrie in an isolated Kubernetes namespace and restrict outbound traffic.
