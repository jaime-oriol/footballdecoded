#!/usr/bin/env python3
# ====================================================================
# FootballDecoded - COMPLETE Database Health Check
# ====================================================================
# Comprehensive analysis of ALL data integrity, constraints, and issues
# ====================================================================

import sys
import os
import pandas as pd
import json
from typing import Dict, List
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import get_db_manager

class DatabaseHealthChecker:
    """Complete database health checker for FootballDecoded."""
    
    def __init__(self):
        self.db = get_db_manager()
        self.issues = []
        self.stats = {}
    
    def run_complete_check(self) -> Dict:
        """Run ALL health checks and return comprehensive report."""
        
        print("🏥 FootballDecoded - COMPLETE Database Health Check")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Basic connectivity and schema check
        self._check_basic_connectivity()
        
        # 2. Table structure and existence
        self._check_table_structure()
        
        # 3. Data integrity constraints
        self._check_data_integrity()
        
        # 4. Data quality and completeness
        self._check_data_quality()
        
        # 5. Index and performance health
        self._check_performance_health()
        
        # 6. Data consistency between sources
        self._check_data_consistency()
        
        # 7. JSON field validation
        self._check_json_fields()
        
        # 8. Constraint violations and warnings
        self._check_constraint_violations()
        
        # Generate final report
        return self._generate_final_report()
    
    def _check_basic_connectivity(self):
        """Check basic database connectivity and schema."""
        print("🔌 1. BASIC CONNECTIVITY & SCHEMA")
        print("-" * 40)
        
        try:
            # Test connection
            result = pd.read_sql("SELECT current_database(), current_user, version()", self.db.engine)
            print(f"   ✅ Connected to: {result.iloc[0]['current_database']}")
            print(f"   👤 User: {result.iloc[0]['current_user']}")
            print(f"   🐘 Version: {result.iloc[0]['version'][:50]}...")
            
            # Check schema exists
            schema_check = pd.read_sql("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'footballdecoded'
            """, self.db.engine)
            
            if not schema_check.empty:
                print(f"   ✅ Schema 'footballdecoded' exists")
            else:
                self.issues.append("❌ Schema 'footballdecoded' does not exist")
                
        except Exception as e:
            self.issues.append(f"❌ Database connectivity failed: {e}")
        
        print()
    
    def _check_table_structure(self):
        """Check all required tables exist with correct structure."""
        print("🗂️  2. TABLE STRUCTURE & EXISTENCE")
        print("-" * 40)
        
        expected_tables = [
            'players_domestic',
            'players_european', 
            'teams_domestic',
            'teams_european'
        ]
        
        try:
            # Get all tables in footballdecoded schema
            existing_tables = pd.read_sql("""
                SELECT table_name, 
                       pg_size_pretty(pg_total_relation_size('footballdecoded.' || table_name)) as size
                FROM information_schema.tables 
                WHERE table_schema = 'footballdecoded'
                ORDER BY table_name
            """, self.db.engine)
            
            print(f"   📋 Found {len(existing_tables)} tables:")
            for _, table in existing_tables.iterrows():
                print(f"      • {table['table_name']} ({table['size']})")
            
            # Check expected tables
            existing_table_names = existing_tables['table_name'].tolist()
            for table in expected_tables:
                if table in existing_table_names:
                    print(f"   ✅ {table}")
                else:
                    self.issues.append(f"❌ Missing table: {table}")
            
            self.stats['tables_found'] = len(existing_tables)
            
        except Exception as e:
            self.issues.append(f"❌ Table structure check failed: {e}")
        
        print()
    
    def _check_data_integrity(self):
        """Check critical data integrity constraints."""
        print("🔒 3. DATA INTEGRITY CONSTRAINTS")
        print("-" * 40)
        
        integrity_checks = [
            # Check NOT NULL constraints
            {
                'name': 'NOT NULL violations',
                'query': """
                    SELECT 'players_domestic' as table_name, 
                           SUM(CASE WHEN player_name IS NULL THEN 1 ELSE 0 END) as null_player_name,
                           SUM(CASE WHEN normalized_name IS NULL THEN 1 ELSE 0 END) as null_normalized_name,
                           SUM(CASE WHEN league IS NULL THEN 1 ELSE 0 END) as null_league,
                           SUM(CASE WHEN season IS NULL THEN 1 ELSE 0 END) as null_season,
                           SUM(CASE WHEN team IS NULL THEN 1 ELSE 0 END) as null_team
                    FROM footballdecoded.players_domestic
                    UNION ALL
                    SELECT 'teams_domestic' as table_name,
                           SUM(CASE WHEN team_name IS NULL THEN 1 ELSE 0 END) as null_team_name,
                           SUM(CASE WHEN normalized_name IS NULL THEN 1 ELSE 0 END) as null_normalized_name,
                           SUM(CASE WHEN league IS NULL THEN 1 ELSE 0 END) as null_league,
                           SUM(CASE WHEN season IS NULL THEN 1 ELSE 0 END) as null_season,
                           0 as null_team
                    FROM footballdecoded.teams_domestic
                """
            },
            
            # Check duplicate violations
            {
                'name': 'Duplicate records',
                'query': """
                    WITH player_dups AS (
                        SELECT normalized_name, age, nationality, league, season, team, COUNT(*) as cnt
                        FROM footballdecoded.players_domestic 
                        GROUP BY normalized_name, age, nationality, league, season, team
                        HAVING COUNT(*) > 1
                    ),
                    team_dups AS (
                        SELECT normalized_name, league, season, COUNT(*) as cnt
                        FROM footballdecoded.teams_domestic
                        GROUP BY normalized_name, league, season  
                        HAVING COUNT(*) > 1
                    )
                    SELECT 'players_domestic' as table_name, COUNT(*) as duplicate_groups, SUM(cnt) as total_duplicates
                    FROM player_dups
                    UNION ALL
                    SELECT 'teams_domestic' as table_name, COUNT(*) as duplicate_groups, SUM(cnt) as total_duplicates  
                    FROM team_dups
                """
            }
        ]
        
        for check in integrity_checks:
            try:
                result = pd.read_sql(check['query'], self.db.engine)
                print(f"   🔍 {check['name']}:")
                
                for _, row in result.iterrows():
                    if check['name'] == 'NOT NULL violations':
                        null_count = sum([row[col] for col in row.index if col.startswith('null_')])
                        if null_count > 0:
                            self.issues.append(f"❌ {row['table_name']}: {null_count} NULL violations")
                            print(f"      ❌ {row['table_name']}: {null_count} NULL violations")
                        else:
                            print(f"      ✅ {row['table_name']}: No NULL violations")
                    
                    elif check['name'] == 'Duplicate records':
                        if row['duplicate_groups'] > 0:
                            self.issues.append(f"❌ {row['table_name']}: {row['duplicate_groups']} duplicate groups")
                            print(f"      ❌ {row['table_name']}: {row['duplicate_groups']} duplicate groups")
                        else:
                            print(f"      ✅ {row['table_name']}: No duplicates")
                            
            except Exception as e:
                self.issues.append(f"❌ {check['name']} check failed: {e}")
        
        print()
    
    def _check_data_quality(self):
        """Check data quality scores and completeness."""
        print("📊 4. DATA QUALITY & COMPLETENESS")
        print("-" * 40)
        
        quality_checks = [
            # Data quality scores
            {
                'name': 'Quality scores',
                'query': """
                    SELECT 'players_domestic' as table_name,
                           COUNT(*) as total_records,
                           ROUND(AVG(data_quality_score), 3) as avg_quality,
                           COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END) as low_quality,
                           COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END) as with_warnings
                    FROM footballdecoded.players_domestic
                    UNION ALL
                    SELECT 'teams_domestic' as table_name,
                           COUNT(*) as total_records,
                           ROUND(AVG(data_quality_score), 3) as avg_quality,
                           COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END) as low_quality,
                           COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END) as with_warnings
                    FROM footballdecoded.teams_domestic
                """
            },
            
            # Data completeness
            {
                'name': 'Data completeness',
                'query': """
                    SELECT 'players_domestic' as table_name,
                           COUNT(*) as total,
                           COUNT(CASE WHEN fbref_metrics IS NOT NULL THEN 1 END) as with_fbref,
                           COUNT(CASE WHEN understat_metrics IS NOT NULL THEN 1 END) as with_understat,
                           COUNT(CASE WHEN fbref_metrics IS NOT NULL AND understat_metrics IS NOT NULL THEN 1 END) as with_both
                    FROM footballdecoded.players_domestic
                    UNION ALL
                    SELECT 'teams_domestic' as table_name,
                           COUNT(*) as total,
                           COUNT(CASE WHEN fbref_metrics IS NOT NULL THEN 1 END) as with_fbref,
                           COUNT(CASE WHEN understat_metrics IS NOT NULL THEN 1 END) as with_understat,
                           COUNT(CASE WHEN fbref_metrics IS NOT NULL AND understat_metrics IS NOT NULL THEN 1 END) as with_both
                    FROM footballdecoded.teams_domestic
                """
            }
        ]
        
        for check in quality_checks:
            try:
                result = pd.read_sql(check['query'], self.db.engine)
                print(f"   📈 {check['name']}:")
                
                for _, row in result.iterrows():
                    if check['name'] == 'Quality scores':
                        print(f"      📋 {row['table_name']}: {row['total_records']} records")
                        print(f"         💯 Avg quality: {row['avg_quality']}")
                        print(f"         ⚠️  Low quality: {row['low_quality']} ({row['low_quality']/row['total_records']*100:.1f}%)")
                        print(f"         ⚠️  With warnings: {row['with_warnings']} ({row['with_warnings']/row['total_records']*100:.1f}%)")
                        
                        self.stats[f"{row['table_name']}_total"] = row['total_records']
                        self.stats[f"{row['table_name']}_avg_quality"] = row['avg_quality']
                        
                        if row['avg_quality'] < 0.8:
                            self.issues.append(f"⚠️ {row['table_name']}: Low average quality score ({row['avg_quality']})")
                    
                    elif check['name'] == 'Data completeness':
                        fbref_pct = row['with_fbref'] / row['total'] * 100
                        understat_pct = row['with_understat'] / row['total'] * 100
                        both_pct = row['with_both'] / row['total'] * 100
                        
                        print(f"      📋 {row['table_name']} completeness:")
                        print(f"         🔵 FBref: {row['with_fbref']}/{row['total']} ({fbref_pct:.1f}%)")
                        print(f"         🟠 Understat: {row['with_understat']}/{row['total']} ({understat_pct:.1f}%)")
                        print(f"         🟢 Both sources: {row['with_both']}/{row['total']} ({both_pct:.1f}%)")
                        
                        if fbref_pct < 95:
                            self.issues.append(f"⚠️ {row['table_name']}: Low FBref coverage ({fbref_pct:.1f}%)")
                        if understat_pct < 50:  # Understat has less coverage
                            self.issues.append(f"⚠️ {row['table_name']}: Low Understat coverage ({understat_pct:.1f}%)")
                
            except Exception as e:
                self.issues.append(f"❌ {check['name']} check failed: {e}")
        
        print()
    
    def _check_performance_health(self):
        """Check database performance indicators."""
        print("⚡ 5. PERFORMANCE HEALTH")
        print("-" * 40)
        
        try:
            # Table sizes and bloat
            table_stats = pd.read_sql("""
                SELECT schemaname,
                       tablename,
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                       pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
                FROM pg_tables 
                WHERE schemaname = 'footballdecoded'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """, self.db.engine)
            
            print("   📏 Table sizes:")
            for _, row in table_stats.iterrows():
                print(f"      📋 {row['tablename']}: {row['total_size']} (table: {row['table_size']}, indexes: {row['index_size']})")
            
            # Index usage
            index_stats = pd.read_sql("""
                SELECT schemaname,
                       relname as tablename,
                       indexrelname as indexname,
                       idx_scan,
                       pg_size_pretty(pg_relation_size(i.indexrelid)) as index_size
                FROM pg_stat_user_indexes pgsui
                JOIN pg_index i ON pgsui.indexrelid = i.indexrelid
                WHERE schemaname = 'footballdecoded'
                ORDER BY idx_scan DESC
            """, self.db.engine)
            
            print(f"   📇 Index usage (top 10):")
            for _, row in index_stats.head(10).iterrows():
                print(f"      🔍 {row['indexname']}: {row['idx_scan']} scans ({row['index_size']})")
            
            # Unused indexes
            unused_indexes = index_stats[index_stats['idx_scan'] < 10]
            if not unused_indexes.empty:
                print(f"   ⚠️  Potentially unused indexes ({len(unused_indexes)}):")
                for _, row in unused_indexes.iterrows():
                    print(f"      ❓ {row['indexname']}: {row['idx_scan']} scans ({row['index_size']})")
                    self.issues.append(f"⚠️ Potentially unused index: {row['indexname']} ({row['idx_scan']} scans)")
            
        except Exception as e:
            self.issues.append(f"❌ Performance health check failed: {e}")
        
        print()
    
    def _check_data_consistency(self):
        """Check consistency between data sources and seasons."""
        print("🔗 6. DATA CONSISTENCY")
        print("-" * 40)
        
        try:
            # Season distribution
            season_dist = pd.read_sql("""
                SELECT 'players_domestic' as table_name, league, season, COUNT(*) as count
                FROM footballdecoded.players_domestic
                GROUP BY league, season
                UNION ALL
                SELECT 'teams_domestic' as table_name, league, season, COUNT(*) as count
                FROM footballdecoded.teams_domestic
                GROUP BY league, season
                ORDER BY table_name, league, season
            """, self.db.engine)
            
            print("   📅 Season distribution:")
            current_table = None
            for _, row in season_dist.iterrows():
                if row['table_name'] != current_table:
                    current_table = row['table_name']
                    print(f"      📋 {current_table}:")
                print(f"         🏆 {row['league']} {row['season']}: {row['count']} records")
            
            # Check team consistency between players and teams tables
            team_consistency = pd.read_sql("""
                WITH player_teams AS (
                    SELECT DISTINCT league, season, team
                    FROM footballdecoded.players_domestic
                ),
                team_teams AS (
                    SELECT DISTINCT league, season, team_name as team
                    FROM footballdecoded.teams_domestic
                )
                SELECT 
                    COALESCE(pt.league, tt.league) as league,
                    COALESCE(pt.season, tt.season) as season,
                    COALESCE(pt.team, tt.team) as team,
                    CASE WHEN pt.team IS NOT NULL THEN 1 ELSE 0 END as in_players,
                    CASE WHEN tt.team IS NOT NULL THEN 1 ELSE 0 END as in_teams
                FROM player_teams pt
                FULL OUTER JOIN team_teams tt ON pt.league = tt.league AND pt.season = tt.season AND pt.team = tt.team
                WHERE pt.team IS NULL OR tt.team IS NULL
                ORDER BY league, season, team
            """, self.db.engine)
            
            if not team_consistency.empty:
                print(f"   ⚠️  Team consistency issues ({len(team_consistency)}):")
                for _, row in team_consistency.iterrows():
                    if row['in_players'] == 0:
                        print(f"      ❌ Team in teams table but not in players: {row['team']} ({row['league']} {row['season']})")
                        self.issues.append(f"❌ Team missing from players: {row['team']} ({row['league']} {row['season']})")
                    if row['in_teams'] == 0:
                        print(f"      ❌ Team in players table but not in teams: {row['team']} ({row['league']} {row['season']})")
                        self.issues.append(f"❌ Team missing from teams: {row['team']} ({row['league']} {row['season']})")
            else:
                print("   ✅ Team consistency: All teams match between players and teams tables")
            
        except Exception as e:
            self.issues.append(f"❌ Data consistency check failed: {e}")
        
        print()
    
    def _check_json_fields(self):
        """Check JSON field validity and structure."""
        print("📄 7. JSON FIELD VALIDATION")
        print("-" * 40)
        
        json_checks = [
            {
                'table': 'players_domestic',
                'fields': ['fbref_metrics', 'understat_metrics']
            },
            {
                'table': 'teams_domestic', 
                'fields': ['fbref_metrics', 'understat_metrics']
            }
        ]
        
        for check in json_checks:
            try:
                for field in check['fields']:
                    # Check JSON validity
                    result = pd.read_sql(f"""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN {field} IS NOT NULL THEN 1 END) as not_null,
                            COUNT(CASE WHEN {field} IS NOT NULL AND jsonb_typeof({field}) = 'object' THEN 1 END) as valid_json
                        FROM footballdecoded.{check['table']}
                    """, self.db.engine)
                    
                    row = result.iloc[0]
                    valid_pct = row['valid_json'] / row['not_null'] * 100 if row['not_null'] > 0 else 0
                    
                    print(f"   📄 {check['table']}.{field}:")
                    print(f"      📊 Total: {row['total']}, Not null: {row['not_null']}, Valid JSON: {row['valid_json']} ({valid_pct:.1f}%)")
                    
                    if valid_pct < 100 and row['not_null'] > 0:
                        self.issues.append(f"❌ {check['table']}.{field}: {row['not_null'] - row['valid_json']} invalid JSON records")
                    
                    # Sample JSON structure
                    if row['valid_json'] > 0:
                        sample = pd.read_sql(f"""
                            SELECT json_object_keys({field}) as keys
                            FROM footballdecoded.{check['table']}
                            WHERE {field} IS NOT NULL
                            LIMIT 1
                        """, self.db.engine)
                        
                        key_count = len(sample)
                        print(f"      🔑 Sample keys: {key_count} fields")
                        if key_count == 0:
                            self.issues.append(f"⚠️ {check['table']}.{field}: Empty JSON objects")
                            
            except Exception as e:
                self.issues.append(f"❌ JSON validation failed for {check['table']}: {e}")
        
        print()
    
    def _check_constraint_violations(self):
        """Check for any constraint violations or edge cases."""
        print("⚠️  8. CONSTRAINT VIOLATIONS & WARNINGS")
        print("-" * 40)
        
        try:
            # Check age ranges
            age_check = pd.read_sql("""
                SELECT 
                    MIN(age) as min_age,
                    MAX(age) as max_age,
                    COUNT(CASE WHEN age < 15 OR age > 50 THEN 1 END) as invalid_ages
                FROM footballdecoded.players_domestic
                WHERE age IS NOT NULL
            """, self.db.engine)
            
            if not age_check.empty:
                row = age_check.iloc[0]
                print(f"   👶 Age range: {row['min_age']} - {row['max_age']} years")
                if row['invalid_ages'] > 0:
                    self.issues.append(f"❌ {row['invalid_ages']} players with invalid ages (< 15 or > 50)")
                    print(f"      ❌ {row['invalid_ages']} invalid ages")
                else:
                    print(f"      ✅ All ages within valid range")
            
            # Check for extremely high metric values (potential data errors)
            metric_check = pd.read_sql("""
                SELECT 
                    COUNT(CASE WHEN (fbref_metrics->>'goals')::numeric > 100 THEN 1 END) as extreme_goals,
                    COUNT(CASE WHEN (fbref_metrics->>'minutes_played')::numeric > 5000 THEN 1 END) as extreme_minutes
                FROM footballdecoded.players_domestic
                WHERE fbref_metrics IS NOT NULL
            """, self.db.engine)
            
            if not metric_check.empty:
                row = metric_check.iloc[0]
                if row['extreme_goals'] > 0:
                    self.issues.append(f"⚠️ {row['extreme_goals']} players with >100 goals (check data)")
                if row['extreme_minutes'] > 0:
                    self.issues.append(f"⚠️ {row['extreme_minutes']} players with >5000 minutes (check data)")
            
            # Check data freshness
            freshness_check = pd.read_sql("""
                SELECT 
                    MIN(created_at) as oldest_record,
                    MAX(created_at) as newest_record,
                    COUNT(CASE WHEN created_at < NOW() - INTERVAL '7 days' THEN 1 END) as old_records
                FROM footballdecoded.players_domestic
            """, self.db.engine)
            
            if not freshness_check.empty:
                row = freshness_check.iloc[0]
                print(f"   📅 Data freshness:")
                print(f"      🕐 Oldest: {row['oldest_record']}")
                print(f"      🕐 Newest: {row['newest_record']}")
                print(f"      📊 Records older than 7 days: {row['old_records']}")
            
        except Exception as e:
            self.issues.append(f"❌ Constraint violation check failed: {e}")
        
        print()
    
    def _generate_final_report(self) -> Dict:
        """Generate comprehensive final report."""
        print("📋 FINAL HEALTH REPORT")
        print("=" * 60)
        
        # Summary stats
        total_issues = len(self.issues)
        critical_issues = len([i for i in self.issues if i.startswith('❌')])
        warnings = len([i for i in self.issues if i.startswith('⚠️')])
        
        print(f"📊 SUMMARY STATISTICS:")
        print(f"   🏥 Overall Health: {'🟢 HEALTHY' if total_issues == 0 else '🟡 ISSUES FOUND' if critical_issues == 0 else '🔴 CRITICAL ISSUES'}")
        print(f"   📊 Total Issues: {total_issues}")
        print(f"   🚨 Critical: {critical_issues}")
        print(f"   ⚠️  Warnings: {warnings}")
        print()
        
        if self.stats:
            print(f"📈 DATA STATISTICS:")
            for key, value in self.stats.items():
                print(f"   📊 {key}: {value}")
            print()
        
        if self.issues:
            print(f"🚨 ISSUES FOUND ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i:2d}. {issue}")
        else:
            print("🎉 NO ISSUES FOUND - Database is healthy!")
        
        print()
        print(f"✅ Health check completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Return structured report
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'healthy' if total_issues == 0 else 'issues' if critical_issues == 0 else 'critical',
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'warnings': warnings,
            'stats': self.stats,
            'issues': self.issues
        }

def main():
    """Run complete database health check."""
    try:
        checker = DatabaseHealthChecker()
        report = checker.run_complete_check()
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"database_health_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed report saved to: {report_file}")
        
        # Return exit code based on health
        if report['critical_issues'] > 0:
            sys.exit(1)  # Critical issues
        elif report['total_issues'] > 0:
            sys.exit(2)  # Warnings only
        else:
            sys.exit(0)  # All good
            
    except Exception as e:
        print(f"💥 Health check failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()