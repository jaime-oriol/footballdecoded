#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Any
from collections import Counter
import ast

class MatchDataAnalyzerV2:
    def __init__(self):
        self.events = None
        self.players = None
        self.zones = None
        self.line_width = 80
        
    def load_data(self) -> bool:
        """Load all CSV files with validation."""
        try:
            self.events = pd.read_csv('viz/data/events.csv')
            self.players = pd.read_csv('viz/data/players.csv')
            self.zones = pd.read_csv('viz/data/zones.csv')
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def header(self, title: str):
        print(f"\n{title}")
        print("═" * self.line_width)
    
    def section(self, title: str):
        print(f"\n{title}")
        print("─" * 50)
    
    def analyze_all(self):
        """Execute complete analysis pipeline."""
        if not self.load_data():
            return
        
        self.header("FOOTBALLDECODED MATCH DATA MEGA ANALYSIS V2.0")
        self._basic_overview()
        self._analyze_events_ultra_deep()
        self._analyze_spatial_patterns()
        self._analyze_temporal_patterns()
        self._analyze_tactical_patterns()
        self._analyze_players_detailed()
        self._analyze_zones_detailed()
        self._cross_validation_advanced()
        self._data_quality_advanced()
        self._performance_insights()
        self._database_recommendations_v2()
    
    def _basic_overview(self):
        """Enhanced dimensional analysis."""
        self.section("DIMENSIONAL OVERVIEW")
        
        files = {
            'events': self.events,
            'players': self.players,
            'zones': self.zones
        }
        
        total_cells = 0
        for name, df in files.items():
            memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
            cells = len(df) * len(df.columns)
            total_cells += cells
            null_cells = df.isnull().sum().sum()
            null_pct = (null_cells / cells) * 100
            print(f"├─ {name}.csv: {len(df):,} rows × {len(df.columns)} cols | {memory_mb:.2f}MB | {null_pct:.1f}% null")
        
        total_memory = sum(df.memory_usage(deep=True).sum() for df in files.values()) / 1024 / 1024
        print(f"└─ Total dataset: {total_memory:.2f}MB | {total_cells:,} data points")
    
    def _analyze_events_ultra_deep(self):
        """Ultra deep analysis of events.csv."""
        self.header("EVENTS.CSV ULTRA-DEEP ANALYSIS (1798 × 50)")
        
        # Complete column analysis
        self.section("COMPLETE COLUMN INVENTORY")
        for i, col in enumerate(self.events.columns, 1):
            dtype = str(self.events[col].dtype)
            nulls = self.events[col].isnull().sum()
            null_pct = (nulls / len(self.events)) * 100
            unique_vals = self.events[col].nunique()
            
            # Sample values
            sample_vals = self.events[col].dropna().head(3).tolist()
            sample_str = str(sample_vals)[:50] + "..." if len(str(sample_vals)) > 50 else str(sample_vals)
            
            print(f"├─ {i:2d}. {col:<20} | {dtype:<10} | {null_pct:5.1f}% null | {unique_vals:4d} unique | {sample_str}")
        
        # Event type deep dive
        self.section("EVENT TYPES DEEP ANALYSIS")
        event_analysis = self.events.groupby('event_type').agg({
            'type': 'count',
            'is_successful': ['sum', 'mean'],
            'xthreat_gen': 'sum',
            'minute': ['min', 'max', 'mean']
        }).round(3)
        
        event_analysis.columns = ['count', 'successful', 'success_rate', 'total_xthreat', 'min_minute', 'max_minute', 'avg_minute']
        event_analysis = event_analysis.sort_values('count', ascending=False)
        
        print("Top 10 event types with full metrics:")
        for i, (event_type, row) in enumerate(event_analysis.head(10).iterrows(), 1):
            print(f"├─ {i:2d}. {event_type:<15} | {row['count']:4.0f} events | {row['success_rate']:.1%} success | xT: {row['total_xthreat']:.3f}")
        
        # Null pattern analysis
        self.section("NULL PATTERN ANALYSIS")
        high_null_cols = []
        for col in self.events.columns:
            null_pct = (self.events[col].isnull().sum() / len(self.events)) * 100
            if null_pct > 50:
                high_null_cols.append((col, null_pct))
        
        print("Columns with >50% nulls (expected for specialized events):")
        for col, pct in sorted(high_null_cols, key=lambda x: x[1], reverse=True):
            # Analyze when this column has values
            non_null_events = self.events[self.events[col].notnull()]
            if len(non_null_events) > 0:
                context_events = non_null_events['event_type'].value_counts().head(3)
                context_str = ", ".join([f"{k}({v})" for k, v in context_events.items()])
                print(f"├─ {col:<20} {pct:5.1f}% null | Appears in: {context_str}")
        
        # Qualifiers analysis
        self.section("QUALIFIERS ANALYSIS")
        if 'qualifiers' in self.events.columns:
            non_empty_qualifiers = self.events[self.events['qualifiers'].notna()]
            print(f"├─ Events with qualifiers: {len(non_empty_qualifiers)} ({len(non_empty_qualifiers)/len(self.events)*100:.1f}%)")
            
            # Parse qualifiers to see patterns
            qualifier_types = []
            for qual_str in non_empty_qualifiers['qualifiers'].head(50):
                try:
                    if isinstance(qual_str, str) and qual_str.strip() and qual_str != '[]':
                        qualifiers = ast.literal_eval(qual_str)
                        for q in qualifiers:
                            if isinstance(q, dict) and 'type' in q:
                                qualifier_types.append(q['type'].get('displayName', 'Unknown'))
                except:
                    continue
            
            if qualifier_types:
                qual_counts = Counter(qualifier_types).most_common(10)
                print("├─ Most common qualifier types:")
                for qual, count in qual_counts:
                    print(f"   {qual}: {count}")
    
    def _analyze_spatial_patterns(self):
        """Deep spatial analysis."""
        self.header("SPATIAL PATTERNS ANALYSIS")
        
        # Field coverage analysis
        self.section("FIELD COVERAGE BY TEAM")
        for team in self.events['team'].unique():
            if pd.notna(team):
                team_events = self.events[self.events['team'] == team]
                
                x_coverage = (team_events['x'].max() - team_events['x'].min()) / 100 * 105  # Convert to meters
                y_coverage = (team_events['y'].max() - team_events['y'].min()) / 100 * 68
                
                avg_x = team_events['x'].mean()
                avg_y = team_events['y'].mean()
                
                # Attacking vs defensive bias
                attacking_events = len(team_events[team_events['x'] > 50])
                defensive_events = len(team_events[team_events['x'] <= 50])
                attack_bias = attacking_events / (attacking_events + defensive_events) * 100
                
                print(f"├─ {team}:")
                print(f"   Field coverage: {x_coverage:.1f}m × {y_coverage:.1f}m")
                print(f"   Average position: ({avg_x:.1f}, {avg_y:.1f})")
                print(f"   Attack bias: {attack_bias:.1f}% (>50% = more attacking)")
        
        # Zone intensity mapping
        self.section("ZONE INTENSITY MAPPING (18-zone system)")
        zone_matrix = np.zeros((3, 6))  # 3 rows, 6 columns for 18 zones
        
        for zone_id in range(1, 19):
            zone_events = len(self.events[self.events['zone_id'] == zone_id])
            row = (zone_id - 1) // 6
            col = (zone_id - 1) % 6
            zone_matrix[row, col] = zone_events
        
        print("Zone event density (Y-axis: top to bottom, X-axis: left to right):")
        for row in range(3):
            row_str = ""
            for col in range(6):
                zone_id = row * 6 + col + 1
                events_count = int(zone_matrix[row, col])
                row_str += f"{zone_id:2d}({events_count:3d}) "
            print(f"├─ {row_str}")
        
        # Progressive action zones
        progressive_events = self.events[self.events['is_progressive_real'] == True]
        if len(progressive_events) > 0:
            prog_zones = progressive_events['zone_id'].value_counts().sort_index()
            print(f"\n├─ Progressive actions by zone: {dict(prog_zones.head())}")
        
        # Distance analysis
        self.section("DISTANCE ANALYSIS")
        distance_cols = ['distance_to_goal', 'pass_distance']
        for col in distance_cols:
            if col in self.events.columns:
                dist_data = self.events[col].dropna()
                if len(dist_data) > 0:
                    percentiles = dist_data.quantile([0.1, 0.25, 0.5, 0.75, 0.9])
                    print(f"├─ {col}: P10={percentiles[0.1]:.1f} P25={percentiles[0.25]:.1f} P50={percentiles[0.5]:.1f} P75={percentiles[0.75]:.1f} P90={percentiles[0.9]:.1f}")
    
    def _analyze_temporal_patterns(self):
        """Deep temporal analysis."""
        self.header("TEMPORAL PATTERNS ANALYSIS")
        
        # Period breakdown
        self.section("PERIOD ANALYSIS")
        period_stats = self.events.groupby('period').agg({
            'minute': 'count',
            'is_successful': 'mean',
            'xthreat_gen': 'sum'
        }).round(3)
        
        for period, stats in period_stats.iterrows():
            if pd.notna(period):
                events_count = stats['minute']
                success_rate = stats['is_successful'] * 100
                xthreat_sum = stats['xthreat_gen']
                print(f"├─ {period}: {events_count} events | {success_rate:.1f}% success | xT: {xthreat_sum:.3f}")
        
        # Game phases analysis
        self.section("GAME PHASES INTENSITY")
        
        # Define phases
        phases = [
            ("Opening", 0, 15),
            ("First Half Build", 15, 30),
            ("First Half End", 30, 45),
            ("Second Half Start", 45, 60),
            ("Second Half Build", 60, 75),
            ("Final Push", 75, 94)
        ]
        
        for phase_name, start_min, end_min in phases:
            phase_events = self.events[(self.events['minute'] >= start_min) & (self.events['minute'] < end_min)]
            if len(phase_events) > 0:
                events_per_min = len(phase_events) / (end_min - start_min)
                success_rate = phase_events['is_successful'].mean() * 100
                xthreat_per_min = phase_events['xthreat_gen'].sum() / (end_min - start_min)
                print(f"├─ {phase_name:<18} | {events_per_min:4.1f} events/min | {success_rate:5.1f}% success | {xthreat_per_min:.3f} xT/min")
        
        # Key moments identification
        self.section("KEY MOMENTS IDENTIFICATION")
        
        # Goals
        goals = self.events[self.events['is_goal'] == 'True']
        if len(goals) > 0:
            print(f"├─ Goals scored at minutes: {sorted(goals['minute'].tolist())}")
        
        # High xThreat moments
        high_xthreat = self.events[self.events['xthreat_gen'] > 0.1]
        if len(high_xthreat) > 0:
            xt_moments = high_xthreat.nlargest(5, 'xthreat_gen')[['minute', 'player', 'event_type', 'xthreat_gen']]
            print("├─ Top 5 xThreat moments:")
            for _, moment in xt_moments.iterrows():
                print(f"   Min {moment['minute']:.0f}: {moment['player']} ({moment['event_type']}) - {moment['xthreat_gen']:.3f}")
    
    def _analyze_tactical_patterns(self):
        """Tactical pattern analysis."""
        self.header("TACTICAL PATTERNS ANALYSIS")
        
        # Possession style analysis
        self.section("POSSESSION STYLE BY TEAM")
        for team in self.events['team'].unique():
            if pd.notna(team):
                team_events = self.events[self.events['team'] == team]
                
                # Pass characteristics
                passes = team_events[team_events['event_type'] == 'Pass']
                if len(passes) > 0:
                    short_passes = len(passes[passes['pass_distance'] <= 15])
                    medium_passes = len(passes[(passes['pass_distance'] > 15) & (passes['pass_distance'] <= 30)])
                    long_passes = len(passes[passes['pass_distance'] > 30])
                    
                    pass_success = passes['is_successful'].mean() * 100
                    avg_pass_length = passes['pass_distance'].mean()
                    
                    print(f"├─ {team} passing:")
                    print(f"   Style: {short_passes} short, {medium_passes} medium, {long_passes} long")
                    print(f"   Success: {pass_success:.1f}% | Avg length: {avg_pass_length:.1f}m")
                
                # Carries vs Passes
                carries = len(team_events[team_events['event_type'] == 'Carry'])
                passes = len(team_events[team_events['event_type'] == 'Pass'])
                carry_ratio = carries / (carries + passes) * 100 if (carries + passes) > 0 else 0
                print(f"   Ball progression: {carry_ratio:.1f}% carries, {100-carry_ratio:.1f}% passes")
        
        # Build-up patterns
        self.section("BUILD-UP PATTERNS")
        
        # Progressive actions analysis
        progressive_events = self.events[self.events['is_progressive_real'] == True]
        if len(progressive_events) > 0:
            prog_by_type = progressive_events['event_type'].value_counts()
            prog_by_team = progressive_events['team'].value_counts()
            
            print("├─ Progressive actions by type:")
            for event_type, count in prog_by_type.items():
                print(f"   {event_type}: {count}")
            
            print("├─ Progressive actions by team:")
            for team, count in prog_by_team.items():
                if pd.notna(team):
                    print(f"   {team}: {count}")
        
        # Transition analysis
        possession_lengths = self.events['possession_id'].value_counts()
        short_possessions = len(possession_lengths[possession_lengths <= 3])
        medium_possessions = len(possession_lengths[(possession_lengths > 3) & (possession_lengths <= 10)])
        long_possessions = len(possession_lengths[possession_lengths > 10])
        
        print(f"\n├─ Possession styles:")
        print(f"   Short (≤3 events): {short_possessions} possessions")
        print(f"   Medium (4-10 events): {medium_possessions} possessions")
        print(f"   Long (>10 events): {long_possessions} possessions")
    
    def _analyze_players_detailed(self):
        """Enhanced player analysis."""
        self.header("PLAYERS DETAILED ANALYSIS (32 × 9)")
        
        # Performance distribution
        self.section("PERFORMANCE DISTRIBUTION")
        metrics = ['xthreat_total', 'progressive_passes', 'progressive_carries', 'pre_assists']
        
        for metric in metrics:
            data = self.players[metric]
            q25, q50, q75 = data.quantile([0.25, 0.5, 0.75])
            top_performers = len(data[data > q75])
            
            print(f"├─ {metric}:")
            print(f"   Q25: {q25:.2f} | Median: {q50:.2f} | Q75: {q75:.2f} | Top 25%: {top_performers} players")
        
        # Position clusters based on avg_x, avg_y
        self.section("POSITION CLUSTERS")
        
        # Defenders (low x)
        defenders = self.players[self.players['avg_x'] < 30]
        midfielders = self.players[(self.players['avg_x'] >= 30) & (self.players['avg_x'] < 55)]
        attackers = self.players[self.players['avg_x'] >= 55]
        
        print(f"├─ Positional distribution:")
        print(f"   Defenders (x<30): {len(defenders)} players | Avg xT: {defenders['xthreat_total'].mean():.2f}")
        print(f"   Midfielders (30≤x<55): {len(midfielders)} players | Avg xT: {midfielders['xthreat_total'].mean():.2f}")
        print(f"   Attackers (x≥55): {len(attackers)} players | Avg xT: {attackers['xthreat_total'].mean():.2f}")
        
        # Player efficiency analysis
        self.section("PLAYER EFFICIENCY")
        
        # xThreat per minute
        self.players['xt_per_minute'] = self.players['xthreat_total'] / (self.players['minutes'] + 1)  # +1 to avoid division by zero
        
        # Progressive actions per minute
        self.players['prog_per_minute'] = (self.players['progressive_passes'] + self.players['progressive_carries']) / (self.players['minutes'] + 1)
        
        top_xt_efficiency = self.players.nlargest(5, 'xt_per_minute')[['player', 'team', 'minutes', 'xt_per_minute']]
        print("├─ Top 5 xThreat efficiency (xT per minute):")
        for _, player in top_xt_efficiency.iterrows():
            print(f"   {player['player']} ({player['team']}): {player['xt_per_minute']:.4f} | {player['minutes']:.0f}min")
        
        top_prog_efficiency = self.players.nlargest(5, 'prog_per_minute')[['player', 'team', 'minutes', 'prog_per_minute']]
        print("├─ Top 5 Progressive efficiency (prog/minute):")
        for _, player in top_prog_efficiency.iterrows():
            print(f"   {player['player']} ({player['team']}): {player['prog_per_minute']:.4f} | {player['minutes']:.0f}min")
    
    def _analyze_zones_detailed(self):
        """Enhanced zones analysis."""
        self.header("ZONES DETAILED ANALYSIS (36 × 5)")
        
        # Zone efficiency analysis
        self.section("ZONE EFFICIENCY ANALYSIS")
        
        # xThreat per event by zone
        self.zones['xt_per_event'] = self.zones['xthreat_total'] / (self.zones['events_count'] + 1)
        
        # Most efficient zones
        top_efficient_zones = self.zones.nlargest(5, 'xt_per_event')
        print("├─ Most efficient zones (xT per event):")
        for _, zone in top_efficient_zones.iterrows():
            print(f"   Zone {zone['zone_id']} ({zone['team']}): {zone['xt_per_event']:.4f} | {zone['events_count']} events")
        
        # Territorial dominance
        self.section("TERRITORIAL DOMINANCE")
        
        for team in self.zones['team'].unique():
            team_zones = self.zones[self.zones['team'] == team]
            total_events = team_zones['events_count'].sum()
            total_xthreat = team_zones['xthreat_total'].sum()
            dominant_zones = len(team_zones[team_zones['possession_pct'] > 60])
            
            print(f"├─ {team}:")
            print(f"   Total events: {total_events} | Total xThreat: {total_xthreat:.3f}")
            print(f"   Dominant zones (>60% possession): {dominant_zones}/18")
        
        # Zone comparison between teams
        self.section("ZONE-BY-ZONE COMPARISON")
        
        team1_zones = self.zones[self.zones['team'] == self.zones['team'].iloc[0]].set_index('zone_id')
        team2_zones = self.zones[self.zones['team'] == self.zones['team'].iloc[-1]].set_index('zone_id')
        
        print("├─ Zone possession comparison (Team1 vs Team2):")
        for zone_id in range(1, 19):
            if zone_id in team1_zones.index and zone_id in team2_zones.index:
                poss1 = team1_zones.loc[zone_id, 'possession_pct']
                poss2 = team2_zones.loc[zone_id, 'possession_pct']
                winner = "T1" if poss1 > poss2 else "T2"
                print(f"   Zone {zone_id:2d}: {poss1:5.1f}% vs {poss2:5.1f}% ({winner})")
    
    def _cross_validation_advanced(self):
        """Advanced cross-validation."""
        self.header("ADVANCED CROSS-VALIDATION")
        
        # Data consistency checks
        self.section("DATA CONSISTENCY VALIDATION")
        
        # Validate aggregations
        events_xthreat_total = self.events['xthreat_gen'].sum()
        players_xthreat_total = self.players['xthreat_total'].sum()
        zones_xthreat_total = self.zones['xthreat_total'].sum()
        
        print(f"├─ xThreat total consistency:")
        print(f"   Events total: {events_xthreat_total:.6f}")
        print(f"   Players total: {players_xthreat_total:.6f}")
        print(f"   Zones total: {zones_xthreat_total:.6f}")
        
        xthreat_diff = abs(events_xthreat_total - players_xthreat_total)
        consistency_check = "✓ PASS" if xthreat_diff < 0.001 else "✗ FAIL"
        print(f"   Consistency: {consistency_check} (diff: {xthreat_diff:.6f})")
        
        # Event count validation
        total_events_in_events = len(self.events)
        total_events_in_zones = self.zones['events_count'].sum()
        
        print(f"\n├─ Event count consistency:")
        print(f"   Events DataFrame: {total_events_in_events}")
        print(f"   Zones aggregation: {total_events_in_zones}")
        print(f"   Consistency: {'✓ PASS' if total_events_in_events == total_events_in_zones else '✗ FAIL'}")
        
        # Player minutes validation
        self.section("LOGICAL VALIDATIONS")
        
        # Players with extreme values
        high_minute_players = self.players[self.players['minutes'] > 95]
        if len(high_minute_players) > 0:
            print(f"├─ Players with >95 minutes: {len(high_minute_players)} (check for data issues)")
        
        zero_minute_players = self.players[self.players['minutes'] == 0]
        if len(zero_minute_players) > 0:
            print(f"├─ Players with 0 minutes: {len(zero_minute_players)} (substitutions/bench)")
        
        # Events outside field
        out_of_bounds = self.events[
            (self.events['x'] < 0) | (self.events['x'] > 100) |
            (self.events['y'] < 0) | (self.events['y'] > 100)
        ]
        print(f"├─ Events outside field bounds: {len(out_of_bounds)}")
        
        # Impossible event combinations
        impossible_events = self.events[
            (self.events['event_type'] == 'Pass') & 
            (self.events['pass_distance'].isna()) &
            (self.events['end_x'].notna())
        ]
        print(f"└─ Impossible combinations: {len(impossible_events)} (passes without distance but with end coords)")
    
    def _data_quality_advanced(self):
        """Advanced data quality analysis."""
        self.header("ADVANCED DATA QUALITY ANALYSIS")
        
        # Outlier detection
        self.section("OUTLIER DETECTION")
        
        numeric_cols = self.events.select_dtypes(include=[np.number]).columns
        outliers_summary = []
        
        for col in numeric_cols:
            if col in ['x', 'y', 'end_x', 'end_y', 'minute', 'second']:  # Skip coordinate and time columns
                continue
                
            data = self.events[col].dropna()
            if len(data) > 0:
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = data[(data < lower_bound) | (data > upper_bound)]
                if len(outliers) > 0:
                    outliers_summary.append((col, len(outliers), outliers.min(), outliers.max()))
        
        if outliers_summary:
            print("├─ Statistical outliers detected:")
            for col, count, min_val, max_val in outliers_summary:
                print(f"   {col}: {count} outliers | Range: [{min_val:.3f}, {max_val:.3f}]")
        else:
            print("├─ No statistical outliers detected in main metrics")
        
        # Data type consistency
        self.section("DATA TYPE CONSISTENCY")
        
        # Check for mixed types in supposedly numeric columns
        mixed_type_issues = []
        for col in self.events.columns:
            if 'id' in col.lower() or col in ['minute', 'second', 'x', 'y', 'end_x', 'end_y']:
                non_numeric = self.events[col].apply(lambda x: not pd.isna(x) and not isinstance(x, (int, float)))
                if non_numeric.any():
                    mixed_type_issues.append((col, non_numeric.sum()))
        
        if mixed_type_issues:
            print("├─ Mixed type issues:")
            for col, count in mixed_type_issues:
                print(f"   {col}: {count} non-numeric values")
        else:
            print("├─ No mixed type issues detected")
        
        # Duplicate detection
        duplicate_events = self.events.duplicated().sum()
        duplicate_players = self.players.duplicated().sum()
        duplicate_zones = self.zones.duplicated().sum()
        
        print(f"\n├─ Duplicate rows:")
        print(f"   Events: {duplicate_events} | Players: {duplicate_players} | Zones: {duplicate_zones}")
    
    def _performance_insights(self):
        """Performance insights and match story."""
        self.header("PERFORMANCE INSIGHTS & MATCH STORY")
        
        # Match narrative
        self.section("MATCH NARRATIVE")
        
        teams = list(self.events['team'].dropna().unique())
        if len(teams) >= 2:
            team1, team2 = teams[0], teams[1]
            
            # Possession stats
            team1_events = len(self.events[self.events['team'] == team1])
            team2_events = len(self.events[self.events['team'] == team2])
            total_events = team1_events + team2_events
            
            possession1 = team1_events / total_events * 100
            possession2 = team2_events / total_events * 100
            
            print(f"├─ Possession: {team1} {possession1:.1f}% - {possession2:.1f}% {team2}")
            
            # xThreat comparison
            xt1 = self.events[self.events['team'] == team1]['xthreat_gen'].sum()
            xt2 = self.events[self.events['team'] == team2]['xthreat_gen'].sum()
            
            print(f"├─ xThreat generated: {team1} {xt1:.3f} - {xt2:.3f} {team2}")
            
            # Progressive actions
            prog1 = len(self.events[(self.events['team'] == team1) & (self.events['is_progressive_real'] == True)])
            prog2 = len(self.events[(self.events['team'] == team2) & (self.events['is_progressive_real'] == True)])
            
            print(f"├─ Progressive actions: {team1} {prog1} - {prog2} {team2}")
            
            # Success rates
            success1 = self.events[self.events['team'] == team1]['is_successful'].mean() * 100
            success2 = self.events[self.events['team'] == team2]['is_successful'].mean() * 100
            
            print(f"└─ Success rate: {team1} {success1:.1f}% - {success2:.1f}% {team2}")
        
        # Key players impact
        self.section("KEY PLAYERS IMPACT")
        
        # Most influential players (combination of metrics)
        self.players['influence_score'] = (
            self.players['xthreat_total'] * 0.4 +
            self.players['progressive_passes'] * 0.05 +
            self.players['progressive_carries'] * 0.1 +
            self.players['pre_assists'] * 0.2
        )
        
        top_influencers = self.players.nlargest(5, 'influence_score')
        print("├─ Most influential players (composite score):")
        for i, (_, player) in enumerate(top_influencers.iterrows(), 1):
            print(f"   {i}. {player['player']} ({player['team']}): {player['influence_score']:.3f}")
            print(f"      xT: {player['xthreat_total']:.3f} | Prog: {player['progressive_passes']+player['progressive_carries']} | Pre-ast: {player['pre_assists']}")
    
    def _database_recommendations_v2(self):
        """Enhanced database recommendations."""
        self.header("DATABASE RECOMMENDATIONS V2.0")
        
        print("COMPLETE EVENTS TABLE SCHEMA:")
        
        # Detailed column analysis for DB design
        db_recommendations = []
        
        for col in self.events.columns:
            dtype = str(self.events[col].dtype)
            null_pct = self.events[col].isnull().sum() / len(self.events) * 100
            unique_vals = self.events[col].nunique()
            
            # Recommend appropriate DB type
            if 'int' in dtype:
                if unique_vals < 100:
                    db_type = 'SMALLINT'
                else:
                    db_type = 'INTEGER'
            elif 'float' in dtype:
                if col in ['x', 'y', 'end_x', 'end_y']:
                    db_type = 'DECIMAL(5,2)'
                elif 'xthreat' in col:
                    db_type = 'DECIMAL(8,6)'
                elif 'xg' in col:
                    db_type = 'DECIMAL(6,4)'
                else:
                    db_type = 'DECIMAL(10,4)'
            elif 'bool' in dtype:
                db_type = 'BOOLEAN'
            else:  # object/string
                max_length = self.events[col].astype(str).str.len().max() if not self.events[col].isnull().all() else 50
                if max_length <= 20:
                    db_type = 'VARCHAR(20)'
                elif max_length <= 50:
                    db_type = 'VARCHAR(50)'
                elif max_length <= 100:
                    db_type = 'VARCHAR(100)'
                else:
                    db_type = 'TEXT'
            
            nullable = "NULL" if null_pct > 0 else "NOT NULL"
            db_recommendations.append((col, db_type, nullable, null_pct, unique_vals))
        
        # Print schema with detailed info
        for col, db_type, nullable, null_pct, unique_vals in db_recommendations:
            print(f"├─ {col:<20} {db_type:<15} {nullable:<8} | {null_pct:5.1f}% null | {unique_vals:4d} unique")
        
        print("\nENHANCED INDEX STRATEGY:")
        indexes = [
            "-- Core performance indexes",
            "CREATE INDEX idx_events_team_minute ON events(team, minute);",
            "CREATE INDEX idx_events_player_team ON events(player, team);",
            "CREATE INDEX idx_events_type_outcome ON events(event_type, outcome_type);",
            "CREATE INDEX idx_events_possession ON events(possession_id);",
            "CREATE INDEX idx_events_zone_team ON events(zone_id, team);",
            "",
            "-- Spatial analysis indexes",
            "CREATE INDEX idx_events_spatial ON events(x, y);",
            "CREATE INDEX idx_events_spatial_end ON events(end_x, end_y);",
            "",
            "-- Advanced metrics indexes",
            "CREATE INDEX idx_events_xthreat ON events(xthreat_gen) WHERE xthreat_gen > 0;",
            "CREATE INDEX idx_events_progressive ON events(is_progressive_real) WHERE is_progressive_real = true;",
            "CREATE INDEX idx_events_xg ON events(xg) WHERE xg IS NOT NULL;",
            "",
            "-- Performance optimization",
            "CREATE INDEX idx_events_successful ON events(is_successful, event_type);",
            "CREATE INDEX idx_events_period_minute ON events(period, minute);",
        ]
        
        for idx in indexes:
            if idx.startswith("--") or idx == "":
                print(f"{idx}")
            else:
                print(f"├─ {idx}")
        
        # Storage estimation
        estimated_size_per_match = len(self.events) * 120  # bytes per row estimate
        print(f"\n├─ Storage estimation:")
        print(f"   Per match: ~{estimated_size_per_match/1024:.1f}KB")
        print(f"   Per season (380 matches): ~{estimated_size_per_match*380/1024/1024:.1f}MB")
        print(f"   With indexes (+50%): ~{estimated_size_per_match*380*1.5/1024/1024:.1f}MB")
        
        print(f"\n└─ Recommended partitioning: BY team OR BY match_date for large datasets")

def main():
    analyzer = MatchDataAnalyzerV2()
    analyzer.analyze_all()

if __name__ == "__main__":
    main()
    