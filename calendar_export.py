"""Portable approved-event calendar export; no external calendar writes."""
from datetime import datetime, timezone

def _utc(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Calendar timestamps must include a timezone.')
    return dt.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

def _escape(value):
    return str(value or '').replace('\\', '\\\\').replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')

def _fold(line):
    parts, current = [], ''
    for char in line:
        if len((current + char).encode('utf-8')) > 75:
            parts.append(current)
            current = ' '
        current += char
    return '\r\n'.join(parts + [current])

def calendar_ics(events):
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//QIU//Student Life Division//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH']
    for event in sorted(events, key=lambda e: (e['start_at'], e['id'])):
        lines += ['BEGIN:VEVENT', 'UID:' + _escape('qiu-sld-' + event['id'] + '@qiu.edu.my'),
                  'DTSTAMP:' + _utc(event['approved_at']), 'DTSTART:' + _utc(event['start_at']),
                  'DTEND:' + _utc(event['end_at']), 'SUMMARY:' + _escape(event['title']),
                  'LOCATION:' + _escape(event.get('venue')), 'DESCRIPTION:' + _escape(event.get('description')), 'END:VEVENT']
    return ('\r\n'.join(_fold(line) for line in lines + ['END:VCALENDAR']) + '\r\n').encode('utf-8')
