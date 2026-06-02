# OpenThreatGrid Weekly Threat Report

Period: {{start_date}} - {{end_date}}

## Executive Summary

During this period, OpenThreatGrid observed {{total_events}} events from {{sensor_count}} honeypot sensor(s).

## Key Findings

- Total events: {{total_events}}
- Top attacked service: {{top_service}}
- Top username: {{top_username}}
- Top password: {{top_password}}
- Malware download attempts: {{malware_download_attempts}}
- Suspected botnet patterns: {{suspected_botnet_count}}

## Attack Timeline

{{attack_timeline}}

## Top Usernames

{{top_usernames_table}}

## Top Passwords

{{top_passwords_table}}

## Top Commands

{{top_commands_table}}

## Malware Delivery Attempts

{{malware_delivery_table}}

## Suspected Botnet Patterns

{{botnet_patterns}}

## Defensive Recommendations

- Disable password-based SSH authentication where possible.
- Use strong unique credentials.
- Restrict management services by IP allowlist or VPN.
- Monitor for suspicious `wget`, `curl`, `chmod`, and shell execution chains.
- Patch exposed internet-facing services regularly.
