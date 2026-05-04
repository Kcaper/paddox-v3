import time

import requests
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from f1data.models import (
    Circuit, Constructor, ConstructorChampionshipStanding, Driver,
    DriverChampionshipStanding, Race, RaceEntry, Season,
)

BASE_URL = "https://api.jolpi.ca/ergast/f1"


class Command(BaseCommand):
    help = "Sync F1 season data from the Jolpica API"

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, default=2025)
        parser.add_argument(
            "--results-only",
            action="store_true",
            help="Only sync race results and standings (skip calendar/drivers/constructors)",
        )

    def handle(self, *args, **options):
        year = options["year"]
        self.stdout.write(f"Syncing {year} F1 season...")

        season = self._sync_season(year)

        if not options["results_only"]:
            self._sync_constructors(year)
            self._sync_drivers(year)
            self._sync_calendar(year, season)

        self._sync_results(year, season)
        self._sync_standings(year, season)

        self.stdout.write(self.style.SUCCESS(f"Done syncing {year} season."))

    # ------------------------------------------------------------------ helpers

    def _get(self, path, **params):
        url = f"{BASE_URL}{path}"
        time.sleep(0.35)  # Jolpica rate limit ~4 req/s
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 429:
            self.stdout.write("  Rate limited — sleeping 10s...")
            time.sleep(10)
            resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()["MRData"]

    def _get_all(self, path, table_key, item_key):
        limit = 100
        offset = 0
        results = []
        while True:
            data = self._get(path, limit=limit, offset=offset)
            items = data[table_key][item_key]
            results.extend(items)
            if offset + limit >= int(data["total"]):
                break
            offset += limit
        return results

    def _parse_dt(self, date_str, time_str):
        if not date_str or not time_str:
            return None
        return datetime.fromisoformat(f"{date_str}T{time_str.rstrip('Z')}+00:00")

    # ------------------------------------------------------------------ syncs

    def _sync_season(self, year):
        season, created = Season.objects.update_or_create(
            year=year,
            defaults={"is_active": True},
        )
        Season.objects.exclude(year=year).update(is_active=False)
        self.stdout.write(f"  {'Created' if created else 'Updated'} season {year}")
        return season

    def _sync_constructors(self, year):
        items = self._get_all(f"/{year}/constructors.json", "ConstructorTable", "Constructors")
        for c in items:
            Constructor.objects.update_or_create(
                ref=c["constructorId"],
                defaults={
                    "name": c["name"],
                    "nationality": c.get("nationality", ""),
                    "is_on_grid": True,
                },
            )
        self.stdout.write(f"  Synced {len(items)} constructors")

    def _sync_drivers(self, year):
        drivers = self._get_all(f"/{year}/drivers.json", "DriverTable", "Drivers")

        # Build driver → constructor map from current standings
        constructor_map = {}
        try:
            data = self._get(f"/{year}/driverStandings.json")
            for s in data["StandingsTable"]["StandingsLists"][0]["DriverStandings"]:
                if s["Constructors"]:
                    constructor_map[s["Driver"]["driverId"]] = s["Constructors"][0]["constructorId"]
        except (KeyError, IndexError):
            pass

        for d in drivers:
            constructor = None
            constructor_ref = constructor_map.get(d["driverId"])
            if constructor_ref:
                constructor = Constructor.objects.filter(ref=constructor_ref).first()

            number = d.get("permanentNumber")
            Driver.objects.update_or_create(
                ref=d["driverId"],
                defaults={
                    "first_name": d["givenName"],
                    "last_name": d["familyName"],
                    "number": int(number) if number else None,
                    "abbreviation": d.get("code", ""),
                    "nationality": d.get("nationality", ""),
                    "constructor": constructor,
                    "is_on_grid": True,
                },
            )

        self.stdout.write(f"  Synced {len(drivers)} drivers")

    def _sync_calendar(self, year, season):
        races_data = self._get_all(f"/{year}/races.json", "RaceTable", "Races")

        for r in races_data:
            circ = r["Circuit"]
            loc = circ["Location"]
            circuit, _ = Circuit.objects.update_or_create(
                ref=circ["circuitId"],
                defaults={
                    "name": circ["circuitName"],
                    "country": loc["country"],
                    "city": loc.get("locality", ""),
                },
            )

            fp1 = r.get("FirstPractice", {})
            fp2 = r.get("SecondPractice", {})
            fp3 = r.get("ThirdPractice", {})
            sq = r.get("SprintQualifying", {})
            sprint = r.get("Sprint", {})
            quali = r.get("Qualifying", {})

            Race.objects.update_or_create(
                season=season,
                round=int(r["round"]),
                defaults={
                    "name": r["raceName"],
                    "circuit": circuit,
                    "is_sprint_weekend": "Sprint" in r,
                    "fp1_at": self._parse_dt(fp1.get("date"), fp1.get("time")),
                    "fp2_at": self._parse_dt(fp2.get("date"), fp2.get("time")),
                    "fp3_at": self._parse_dt(fp3.get("date"), fp3.get("time")),
                    "sprint_quali_at": self._parse_dt(sq.get("date"), sq.get("time")),
                    "sprint_at": self._parse_dt(sprint.get("date"), sprint.get("time")),
                    "quali_at": self._parse_dt(quali.get("date"), quali.get("time")),
                    "race_at": self._parse_dt(r["date"], r.get("time")),
                },
            )

        self.stdout.write(f"  Synced {len(races_data)} races")

    def _sync_results(self, year, season):
        now = datetime.now(timezone.utc)
        races = Race.objects.filter(season=season).order_by("round")
        synced = 0

        for race in races:
            if not race.race_at or race.race_at > now:
                continue

            data = self._get(f"/{year}/{race.round}/results.json")
            race_list = data["RaceTable"]["Races"]
            if not race_list:
                continue
            results = race_list[0].get("Results", [])

            # Qualifying → grid positions
            grid_map = {}
            try:
                q_data = self._get(f"/{year}/{race.round}/qualifying.json")
                q_races = q_data["RaceTable"]["Races"]
                if q_races:
                    for q in q_races[0].get("QualifyingResults", []):
                        grid_map[q["Driver"]["driverId"]] = int(q["position"])
            except Exception:
                pass

            # Find fastest lap holder
            fastest_lap_driver_id = None
            for result in results:
                if result.get("FastestLap", {}).get("rank") == "1":
                    fastest_lap_driver_id = result["Driver"]["driverId"]
                    break

            for result in results:
                driver_data = result["Driver"]
                driver_id = driver_data["driverId"]
                constructor_id = result["Constructor"]["constructorId"]

                number = driver_data.get("permanentNumber")
                driver, _ = Driver.objects.get_or_create(
                    ref=driver_id,
                    defaults={
                        "first_name": driver_data["givenName"],
                        "last_name": driver_data["familyName"],
                        "number": int(number) if number else None,
                        "abbreviation": driver_data.get("code", ""),
                        "nationality": driver_data.get("nationality", ""),
                        "is_on_grid": True,
                    },
                )
                constructor = Constructor.objects.filter(ref=constructor_id).first()

                pos_text = result.get("positionText", "")
                finish_position = int(pos_text) if pos_text.isdigit() else None

                RaceEntry.objects.update_or_create(
                    race=race,
                    driver=driver,
                    defaults={
                        "constructor": constructor,
                        "grid_position": grid_map.get(driver_id),
                        "finish_position": finish_position,
                        "is_fastest_lap": driver_id == fastest_lap_driver_id,
                        "is_confirmed": True,
                    },
                )

            race.is_complete = True
            race.save(update_fields=["is_complete"])
            synced += 1

        self.stdout.write(f"  Synced results for {synced} races")

    def _sync_standings(self, year, season):
        races = Race.objects.filter(season=season, is_complete=True).order_by("round")

        for race in races:
            try:
                d_data = self._get(f"/{year}/{race.round}/driverStandings.json")
                standings_lists = d_data["StandingsTable"]["StandingsLists"]
                if standings_lists:
                    for s in standings_lists[0]["DriverStandings"]:
                        if "position" not in s:
                            continue  # positionText="-" means 0 pts, no ranked position yet
                        driver = Driver.objects.filter(ref=s["Driver"]["driverId"]).first()
                        if driver:
                            DriverChampionshipStanding.objects.update_or_create(
                                race=race,
                                driver=driver,
                                defaults={
                                    "position": int(s["position"]),
                                    "points": float(s["points"]),
                                },
                            )
            except Exception as e:
                self.stdout.write(f"  Warning: driver standings round {race.round}: {e}")

            try:
                c_data = self._get(f"/{year}/{race.round}/constructorStandings.json")
                standings_lists = c_data["StandingsTable"]["StandingsLists"]
                if standings_lists:
                    for s in standings_lists[0]["ConstructorStandings"]:
                        if "position" not in s:
                            continue
                        constructor = Constructor.objects.filter(ref=s["Constructor"]["constructorId"]).first()
                        if constructor:
                            ConstructorChampionshipStanding.objects.update_or_create(
                                race=race,
                                constructor=constructor,
                                defaults={
                                    "position": int(s["position"]),
                                    "points": float(s["points"]),
                                },
                            )
            except Exception as e:
                self.stdout.write(f"  Warning: constructor standings round {race.round}: {e}")

        self.stdout.write(f"  Synced standings for {races.count()} races")
