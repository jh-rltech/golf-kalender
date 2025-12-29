"""
Golf Calendar Updater
Henter automatisk turneringsdata og opdaterer golf.ics kalenderfilen.
Kører via GitHub Actions hver uge.
"""

import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import json

# ============================================================
# KONFIGURATION - Turneringer vi tracker
# ============================================================

# Faste turneringer vi altid vil have med (majors + Ryder Cup)
# Disse opdateres manuelt når datoer annonceres
FIXED_TOURNAMENTS = [
    # 2026 Majors
    {
        "uid": "masters-2026",
        "name": "The Masters 2026",
        "start": "2026-04-09",
        "end": "2026-04-12",
        "venue": "Augusta National Golf Club",
        "location": "Augusta, Georgia, USA",
        "channel": "Viaplay / V Sport Golf",
        "times": "Torsdag-Søndag: ca. 19:00-02:00",
        "description": "MAJOR - Første major i 2026",
        "is_major": True
    },
    {
        "uid": "pga-championship-2026",
        "name": "PGA Championship 2026",
        "start": "2026-05-14",
        "end": "2026-05-17",
        "venue": "Aronimink Golf Club",
        "location": "Newtown Square, Pennsylvania, USA",
        "channel": "Viaplay / V Sport Golf",
        "times": "Torsdag-Søndag: ca. 18:00-02:00",
        "description": "MAJOR - 108. udgave af PGA Championship",
        "is_major": True
    },
    {
        "uid": "us-open-2026",
        "name": "US Open 2026",
        "start": "2026-06-18",
        "end": "2026-06-21",
        "venue": "Shinnecock Hills Golf Club",
        "location": "Southampton, New York, USA",
        "channel": "Viaplay / V Sport Golf",
        "times": "Torsdag-Søndag: ca. 17:00-02:00",
        "description": "MAJOR - 126. US Open på legendariske Shinnecock Hills",
        "is_major": True
    },
    {
        "uid": "the-open-2026",
        "name": "The Open Championship 2026",
        "start": "2026-07-16",
        "end": "2026-07-19",
        "venue": "Royal Birkdale Golf Club",
        "location": "Southport, England",
        "channel": "Viaplay / V Sport Golf",
        "times": "Torsdag-Søndag: ca. 10:00-21:00",
        "description": "MAJOR - The Open på Royal Birkdale",
        "is_major": True
    },
    # 2027 Majors
    {
        "uid": "masters-2027",
        "name": "The Masters 2027",
        "start": "2027-04-08",
        "end": "2027-04-11",
        "venue": "Augusta National Golf Club",
        "location": "Augusta, Georgia, USA",
        "channel": "Viaplay / V Sport Golf",
        "times": "Torsdag-Søndag: ca. 19:00-02:00",
        "description": "MAJOR - The Masters 2027",
        "is_major": True
    },
    {
        "uid": "ryder-cup-2027",
        "name": "Ryder Cup 2027 - 100 års jubilæum!",
        "start": "2027-09-17",
        "end": "2027-09-19",
        "venue": "Adare Manor",
        "location": "County Limerick, Irland",
        "channel": "Viaplay / V Sport Golf / TV3 Sport",
        "times": "Fredag-Søndag: ca. 13:00-22:00",
        "description": "RYDER CUP - 100 års jubilæum! Europa vs USA",
        "is_major": True
    },
    # Ryder Cup 2029
    {
        "uid": "ryder-cup-2029",
        "name": "Ryder Cup 2029",
        "start": "2029-09-28",
        "end": "2029-09-30",
        "venue": "Hazeltine National Golf Club",
        "location": "Chaska, Minnesota, USA",
        "channel": "Viaplay / V Sport Golf / TV3 Sport",
        "times": "Fredag-Søndag: ca. 14:00-23:00",
        "description": "RYDER CUP - USA er værter på Hazeltine",
        "is_major": True
    },
]

# DP World Tour events vi vil tracke (Rolex Series + store events)
DP_WORLD_TOUR_EVENTS = [
    "Dubai Desert Classic",
    "Irish Open",
    "Scottish Open",
    "BMW PGA Championship",
    "Alfred Dunhill Links",
    "DP World Tour Championship",
    "Abu Dhabi",
    "Open de France",
    "Italian Open",
    "Andalucia Masters",
]

# Danske TV-tider baseret på lokation
def get_danish_broadcast_times(location):
    """Estimerer danske sendetider baseret på turneringslokation"""
    location_lower = location.lower()
    
    if any(x in location_lower for x in ['usa', 'america', 'florida', 'california', 'texas', 'georgia', 'new york', 'pennsylvania']):
        return "Viaplay / V Sport Golf", "Torsdag-Søndag: ca. 18:00-02:00"
    elif any(x in location_lower for x in ['dubai', 'abu dhabi', 'uae', 'qatar', 'bahrain', 'saudi']):
        return "Viaplay / V Sport Golf", "Torsdag-Søndag: ca. 08:00-15:00"
    elif any(x in location_lower for x in ['australia', 'singapore', 'korea', 'japan', 'china', 'asia']):
        return "Viaplay / V Sport Golf", "Torsdag-Søndag: ca. 04:00-12:00"
    elif any(x in location_lower for x in ['south africa', 'kenya', 'mauritius']):
        return "Viaplay / V Sport Golf", "Torsdag-Søndag: ca. 10:00-16:00"
    else:  # Europa
        return "Viaplay / V Sport Golf", "Torsdag-Søndag: ca. 12:00-20:00"


def fetch_dp_world_tour_schedule():
    """
    Forsøger at hente DP World Tour kalender.
    Returnerer liste af turneringer.
    """
    tournaments = []
    
    try:
        # Prøv ESPN's DP World Tour schedule
        url = "https://www.espn.com/golf/schedule/_/tour/eur"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Parse schedule table...
            # Dette er et simpelt eksempel - kan udvides
            print(f"Hentet ESPN side: {len(response.text)} bytes")
            
    except Exception as e:
        print(f"Kunne ikke hente DP World Tour data: {e}")
    
    return tournaments


def create_ics_event(tournament):
    """Opretter en ICS event string for en turnering"""
    
    uid = tournament['uid']
    name = tournament['name']
    start = tournament['start'].replace('-', '')
    # End date er dagen efter sidste spilledag (ICS standard for heldagsevents)
    end_date = datetime.strptime(tournament['end'], '%Y-%m-%d') + timedelta(days=1)
    end = end_date.strftime('%Y%m%d')
    
    venue = tournament['venue']
    location = tournament['location']
    channel = tournament['channel']
    times = tournament['times']
    description = tournament['description']
    is_major = tournament.get('is_major', False)
    
    emoji = "⛳🏆" if is_major else "⛳"
    
    # Escape special characters for ICS
    desc_escaped = f"{description}\\n\\n📺 {channel}\\n🕐 {times}\\n📍 {venue}\\n🌍 {location}"
    
    event = f"""BEGIN:VEVENT
UID:{uid}@golf-kalender
DTSTART:{start}
DTEND:{end}
SUMMARY:{emoji} {name}
DESCRIPTION:{desc_escaped}
LOCATION:{venue}, {location}
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:I morgen: {name} på Viaplay!
END:VALARM
END:VEVENT"""
    
    return event


def generate_calendar(tournaments):
    """Genererer komplet ICS kalenderfil"""
    
    header = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Golf Notifier//DA
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:⛳ Golf TV Danmark
X-WR-CALDESC:Golf turneringer på dansk TV - PGA Championship, US Open, DP World Tour, Ryder Cup
X-WR-TIMEZONE:Europe/Copenhagen
"""
    
    events = []
    for t in tournaments:
        events.append(create_ics_event(t))
    
    footer = "\nEND:VCALENDAR"
    
    return header + "\n" + "\n\n".join(events) + footer


def main():
    print("🏌️ Golf Calendar Updater")
    print("=" * 40)
    
    # Start med de faste turneringer
    all_tournaments = FIXED_TOURNAMENTS.copy()
    print(f"✅ {len(FIXED_TOURNAMENTS)} faste turneringer (majors + Ryder Cup)")
    
    # Prøv at hente DP World Tour events
    dp_events = fetch_dp_world_tour_schedule()
    if dp_events:
        all_tournaments.extend(dp_events)
        print(f"✅ {len(dp_events)} DP World Tour events hentet")
    
    # Sorter efter dato
    all_tournaments.sort(key=lambda x: x['start'])
    
    # Fjern gamle turneringer (mere end 7 dage siden)
    cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    all_tournaments = [t for t in all_tournaments if t['end'] >= cutoff]
    
    print(f"📅 Total: {len(all_tournaments)} turneringer i kalenderen")
    
    # Generer kalenderfil
    ics_content = generate_calendar(all_tournaments)
    
    # Gem fil
    with open('golf.ics', 'w', encoding='utf-8') as f:
        f.write(ics_content)
    
    print("✅ golf.ics opdateret!")
    
    # Print næste 5 turneringer
    print("\n📅 Næste turneringer:")
    today = datetime.now().strftime('%Y-%m-%d')
    upcoming = [t for t in all_tournaments if t['start'] >= today][:5]
    for t in upcoming:
        print(f"   • {t['start']}: {t['name']}")


if __name__ == "__main__":
    main()
