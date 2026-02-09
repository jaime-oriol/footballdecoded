"""Health monitoring for footballdecoded_v2 schema.

Checks: row counts, duplicate records, missing metrics, quality scores.

Usage:
    python database_checker_v2.py                 # Full status
    python database_checker_v2.py --quick         # Row counts only
    python database_checker_v2.py --health        # Health score (0-100)
    python database_checker_v2.py --problems      # Detect issues
    python database_checker_v2.py --full          # Complete analysis
"""

import sys
import os
import pandas as pd
import logging
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LINE_WIDTH = 80


def _header(title: str):
    """Print a title with double-line separator."""
    print(title)
    print("=" * LINE_WIDTH)

def _section(title: str):
    """Print a section title with single-line separator."""
    print(title)
    print("-" * LINE_WIDTH)

def _footer():
    """Print a closing double-line separator."""
    print("=" * LINE_WIDTH)



def quick_status():
    """Print row counts for each v2 table and player breakdown by league."""
    _header("FootballDecoded v2 Quick Status")

    db = get_db_manager()

    tables = [
        ('players', 'Players'),
        ('teams', 'Teams'),
        ('understat_team_matches', 'Understat Match Stats'),
        ('understat_shots', 'Understat Shots'),
    ]

    _section("TABLE COUNTS")
    total = 0
    for table, label in tables:
        try:
            result = pd.read_sql(f"SELECT COUNT(*) as c FROM footballdecoded_v2.{table}", db.engine)
            count = result.iloc[0]['c']
            total += count
            print(f"  {label}: {count:,}")
        except Exception:
            print(f"  {label}: 0 (table missing)")

    print(f"\n  TOTAL: {total:,}")

    try:
        result = pd.read_sql("""
            SELECT league, season, COUNT(*) as players, COUNT(DISTINCT team) as teams
            FROM footballdecoded_v2.players
            GROUP BY league, season ORDER BY league, season DESC
        """, db.engine)
        if not result.empty:
            _section("PLAYERS BY LEAGUE")
            for _, row in result.iterrows():
                print(f"  {row['league']} {row['season']}: {row['players']} players, {row['teams']} teams")
    except Exception:
        pass

    _footer()
    db.close()


def detect_problems(verbose: bool = True) -> Dict[str, List]:
    """Detect duplicate records, empty metrics, and coverage gaps.

    Returns dict with 'critical', 'warning', and 'info' issue lists.
    """
    if verbose:
        _header("Problem Detection (v2)")

    db = get_db_manager()
    problems = {'critical': [], 'warning': [], 'info': []}

    try:
        # Duplicate players (same person+league+season+team)
        if verbose:
            _section("CRITICAL ISSUES")
        try:
            dupes = pd.read_sql("""
                SELECT unique_player_id, league, season, team, COUNT(*) as cnt
                FROM footballdecoded_v2.players
                GROUP BY unique_player_id, league, season, team
                HAVING COUNT(*) > 1
            """, db.engine)
            if not dupes.empty:
                problems['critical'].append({
                    'table': 'players', 'issue': 'Duplicate players',
                    'count': len(dupes), 'description': f"{len(dupes)} duplicate player records"
                })
                if verbose:
                    print(f"  CRITICAL: {len(dupes)} duplicate player records")
        except Exception:
            pass

        # Duplicate teams (same team+league+season)
        try:
            dupes = pd.read_sql("""
                SELECT unique_team_id, league, season, COUNT(*) as cnt
                FROM footballdecoded_v2.teams
                GROUP BY unique_team_id, league, season
                HAVING COUNT(*) > 1
            """, db.engine)
            if not dupes.empty:
                problems['critical'].append({
                    'table': 'teams', 'issue': 'Duplicate teams',
                    'count': len(dupes), 'description': f"{len(dupes)} duplicate team records"
                })
                if verbose:
                    print(f"  CRITICAL: {len(dupes)} duplicate team records")
        except Exception:
            pass

        if verbose and not problems['critical']:
            print("  No critical issues found")

        # Players/teams with empty FotMob metrics
        if verbose:
            _section("WARNING ISSUES")

        try:
            result = pd.read_sql("""
                SELECT COUNT(*) as c FROM footballdecoded_v2.players
                WHERE fotmob_metrics IS NULL OR fotmob_metrics = '{}'
            """, db.engine)
            cnt = result.iloc[0]['c']
            if cnt > 0:
                problems['warning'].append({
                    'table': 'players', 'issue': 'Empty FotMob metrics',
                    'count': cnt, 'description': f"{cnt} players without FotMob metrics"
                })
                if verbose:
                    print(f"  WARNING: {cnt} players without FotMob metrics")
        except Exception:
            pass

        try:
            result = pd.read_sql("""
                SELECT COUNT(*) as c FROM footballdecoded_v2.teams
                WHERE fotmob_metrics IS NULL OR fotmob_metrics = '{}'
            """, db.engine)
            cnt = result.iloc[0]['c']
            if cnt > 0:
                problems['warning'].append({
                    'table': 'teams', 'issue': 'Empty FotMob metrics',
                    'count': cnt, 'description': f"{cnt} teams without FotMob metrics"
                })
                if verbose:
                    print(f"  WARNING: {cnt} teams without FotMob metrics")
        except Exception:
            pass

        if verbose and not problems['warning']:
            print("  No warnings found")

        # Understat and Transfermarkt coverage percentages
        if verbose:
            _section("INFO")

        for col, label in [('understat_metrics', 'Understat'), ('transfermarkt_metrics', 'Transfermarkt')]:
            try:
                result = pd.read_sql(f"""
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN {col} IS NOT NULL AND {col} != '{{}}' THEN 1 END) as with_data
                    FROM footballdecoded_v2.players
                """, db.engine)
                total = result.iloc[0]['total']
                with_data = result.iloc[0]['with_data']
                if total > 0:
                    pct = with_data / total * 100
                    problems['info'].append({
                        'table': 'players', 'issue': f'{label} coverage',
                        'count': with_data, 'description': f"{label}: {with_data}/{total} ({pct:.1f}%)"
                    })
                    if verbose:
                        print(f"  {label} coverage: {with_data}/{total} players ({pct:.1f}%)")
            except Exception:
                pass

        if verbose:
            _section("DETECTION SUMMARY")
            total_problems = len(problems['critical']) + len(problems['warning'])
            if total_problems == 0:
                print("  Database is healthy!")
            else:
                print(f"  Critical: {len(problems['critical'])} | Warnings: {len(problems['warning'])}")

        _footer()
        db.close()
        return problems

    except Exception as e:
        logger.error(f"Error detecting problems: {e}")
        db.close()
        return problems


def calculate_health_score(verbose: bool = True) -> int:
    """Calculate 0-100 health score based on issues, quality scores, and volume."""
    if verbose:
        _header("Health Score (v2)")

    db = get_db_manager()
    score = 100
    deductions = []

    try:
        total = 0
        for table in ['players', 'teams', 'understat_team_matches', 'understat_shots']:
            try:
                result = pd.read_sql(f"SELECT COUNT(*) as c FROM footballdecoded_v2.{table}", db.engine)
                total += result.iloc[0]['c']
            except Exception:
                pass

        if total == 0:
            if verbose:
                print("  Database is empty")
            return 0

        problems = detect_problems(verbose=False)

        if problems['critical']:
            d = min(50, len(problems['critical']) * 10)
            score -= d
            deductions.append(f"Critical issues: -{d}")

        if problems['warning']:
            d = min(30, len(problems['warning']) * 5)
            score -= d
            deductions.append(f"Warnings: -{d}")
        try:
            result = pd.read_sql("""
                SELECT AVG(data_quality_score) as avg_q FROM footballdecoded_v2.players
                WHERE data_quality_score IS NOT NULL
            """, db.engine)
            avg_q = result.iloc[0]['avg_q']
            if avg_q is not None and avg_q < 0.7:
                d = int((0.7 - avg_q) * 50)
                score -= d
                deductions.append(f"Low quality: -{d}")
        except Exception:
            pass

        if total > 5000:
            score += 5
            deductions.append(f"Volume bonus: +5")

        score = max(0, min(100, score))

        if verbose:
            _section("SCORE CALCULATION")
            print("  Base: 100")
            for d in deductions:
                print(f"  {d}")

            if score >= 90:
                status = "EXCELLENT"
            elif score >= 70:
                status = "GOOD"
            elif score >= 50:
                status = "NEEDS ATTENTION"
            else:
                status = "CRITICAL"

            _section("RESULT")
            print(f"  Score: {score}/100 ({status})")

        _footer()
        db.close()
        return score

    except Exception as e:
        logger.error(f"Error calculating health: {e}")
        db.close()
        return 0


def check_database_status(verbose: bool = True) -> Dict:
    """Full status report: players, teams, matches, shots grouped by league/season.

    Returns dict of DataFrames keyed by 'players', 'teams', 'matches', 'shots'.
    """
    if verbose:
        _header("FootballDecoded v2 Database Status")

    db = get_db_manager()
    results = {}

    try:
        try:
            players = pd.read_sql("""
                SELECT league, season, COUNT(*) as total,
                       COUNT(CASE WHEN understat_metrics IS NOT NULL AND understat_metrics != '{}' THEN 1 END) as with_understat,
                       COUNT(CASE WHEN transfermarkt_metrics IS NOT NULL AND transfermarkt_metrics != '{}' THEN 1 END) as with_tm,
                       COUNT(DISTINCT team) as teams,
                       AVG(data_quality_score) as avg_quality
                FROM footballdecoded_v2.players
                GROUP BY league, season ORDER BY league, season DESC
            """, db.engine)
            results['players'] = players

            if verbose and not players.empty:
                _section("PLAYERS")
                for _, row in players.iterrows():
                    us_pct = (row['with_understat'] / row['total'] * 100) if row['total'] > 0 else 0
                    tm_pct = (row['with_tm'] / row['total'] * 100) if row['total'] > 0 else 0
                    print(f"  {row['league']} {row['season']}: {row['total']} players | {row['teams']} teams | US: {us_pct:.0f}% | TM: {tm_pct:.0f}% | Q: {row['avg_quality']:.2f}")
                print()
        except Exception:
            results['players'] = pd.DataFrame()

        try:
            teams = pd.read_sql("""
                SELECT league, season, COUNT(*) as total,
                       COUNT(CASE WHEN understat_metrics IS NOT NULL AND understat_metrics != '{}' THEN 1 END) as with_understat,
                       COUNT(CASE WHEN understat_advanced IS NOT NULL AND understat_advanced != '{}' THEN 1 END) as with_advanced
                FROM footballdecoded_v2.teams
                GROUP BY league, season ORDER BY league, season DESC
            """, db.engine)
            results['teams'] = teams

            if verbose and not teams.empty:
                _section("TEAMS")
                for _, row in teams.iterrows():
                    us_pct = (row['with_understat'] / row['total'] * 100) if row['total'] > 0 else 0
                    adv_pct = (row['with_advanced'] / row['total'] * 100) if row['total'] > 0 else 0
                    print(f"  {row['league']} {row['season']}: {row['total']} teams | US: {us_pct:.0f}% | Adv: {adv_pct:.0f}%")
                print()
        except Exception:
            results['teams'] = pd.DataFrame()

        try:
            matches = pd.read_sql("""
                SELECT league, season, COUNT(*) as total, COUNT(DISTINCT match_id) as unique_matches
                FROM footballdecoded_v2.understat_team_matches
                GROUP BY league, season ORDER BY league, season DESC
            """, db.engine)
            results['matches'] = matches

            if verbose and not matches.empty:
                _section("UNDERSTAT MATCH STATS")
                for _, row in matches.iterrows():
                    print(f"  {row['league']} {row['season']}: {row['total']} records ({row['unique_matches']} matches)")
                print()
        except Exception:
            results['matches'] = pd.DataFrame()

        try:
            shots = pd.read_sql("""
                SELECT league, season, COUNT(*) as total, COUNT(DISTINCT match_id) as matches
                FROM footballdecoded_v2.understat_shots
                GROUP BY league, season ORDER BY league, season DESC
            """, db.engine)
            results['shots'] = shots

            if verbose and not shots.empty:
                _section("UNDERSTAT SHOTS")
                for _, row in shots.iterrows():
                    print(f"  {row['league']} {row['season']}: {row['total']} shots ({row['matches']} matches)")
                print()
        except Exception:
            results['shots'] = pd.DataFrame()

        if verbose:
            _section("TOTALS")
            for key in ['players', 'teams', 'matches', 'shots']:
                df = results.get(key, pd.DataFrame())
                total = df['total'].sum() if not df.empty else 0
                print(f"  {key.title()}: {total:,}")

        _footer()
        db.close()
        return results

    except Exception as e:
        if verbose:
            print(f"Error: {e}")
        db.close()
        return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == '--quick':
            quick_status()
        elif cmd == '--health':
            score = calculate_health_score()
            print(f"\nHealth Score: {score}/100")
        elif cmd == '--problems':
            detect_problems()
        elif cmd == '--full':
            check_database_status()
            print()
            detect_problems()
            print()
            calculate_health_score()
        else:
            print("Usage: python database_checker_v2.py [--quick|--health|--problems|--full]")
    else:
        check_database_status()
