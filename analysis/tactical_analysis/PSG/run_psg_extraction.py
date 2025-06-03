#!/usr/bin/env python3
"""
PSG Data Extraction Runner
==========================

Script principal para ejecutar la extracción completa de datos del PSG.
Diseñado para integrarse con el workflow existente de FootballDecoded.

Usage:
    python analysis/tactical_analysis/PSG/run_psg_extraction.py [options]

Author: FootballDecoded
Created: 2025-06-03
"""

import sys
import argparse
import traceback
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Local imports
from analysis.tactical_analysis.PSG.data_psg import PSGDataExtractor
from analysis.tactical_analysis.PSG.psg_config import (
    TARGET_SEASONS, TARGET_LEAGUES, PSG_LOGGING_CONFIG
)
from data._config import logger

def setup_logging():
    """Configure logging for PSG extraction."""
    import logging
    
    # Create PSG-specific logger
    psg_logger = logging.getLogger('psg_extraction')
    psg_logger.setLevel(getattr(logging, PSG_LOGGING_CONFIG['log_level']))
    
    # File handler
    log_file = Path(PSG_LOGGING_CONFIG['log_file'])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    if PSG_LOGGING_CONFIG['console_output']:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        psg_logger.addHandler(console_handler)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    psg_logger.addHandler(file_handler)
    
    return psg_logger

def extract_team_data(extractor: PSGDataExtractor, args: argparse.Namespace) -> Dict[str, Any]:
    """
    Extract team-level data based on arguments.
    
    Parameters
    ----------
    extractor : PSGDataExtractor
        Configured extractor instance
    args : argparse.Namespace
        Command line arguments
        
    Returns
    -------
    Dict[str, Any]
        Extracted team data
    """
    logger.info("🏆 Starting team data extraction...")
    
    team_data = {}
    
    if args.team_stats:
        logger.info("📊 Extracting team season statistics...")
        team_data['season_stats'] = extractor.extract_team_season_stats()
    
    if args.match_data:
        logger.info("⚽ Extracting match-by-match data...")
        team_data['match_data'] = extractor.extract_match_data()
    
    logger.info(f"✅ Team data extraction completed. Categories: {list(team_data.keys())}")
    return team_data

def extract_player_data(extractor: PSGDataExtractor, args: argparse.Namespace) -> Dict[str, Any]:
    """
    Extract player-level data based on arguments.
    
    Parameters
    ----------
    extractor : PSGDataExtractor
        Configured extractor instance
    args : argparse.Namespace
        Command line arguments
        
    Returns
    -------
    Dict[str, Any]
        Extracted player data
    """
    logger.info("👥 Starting player data extraction...")
    
    player_data = {}
    
    if args.player_stats:
        logger.info("👤 Extracting player season statistics...")
        player_data['season_stats'] = extractor.extract_player_season_stats()
    
    # Future: Add player match stats, event data, etc.
    
    logger.info(f"✅ Player data extraction completed. Categories: {list(player_data.keys())}")
    return player_data

def generate_summary_report(all_data: Dict[str, Any], extractor: PSGDataExtractor) -> Dict[str, Any]:
    """
    Generate comprehensive summary report.
    
    Parameters
    ----------
    all_data : Dict[str, Any]
        All extracted data
    extractor : PSGDataExtractor
        Extractor instance with metadata
        
    Returns
    -------
    Dict[str, Any]
        Summary report
    """
    logger.info("📋 Generating summary report...")
    
    summary = {
        'extraction_metadata': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'seasons': extractor.seasons,
            'leagues': extractor.leagues,
            'extraction_duration': None  # To be filled
        },
        'data_summary': {},
        'quality_metrics': {},
        'recommendations': []
    }
    
    # Analyze extracted data
    total_records = 0
    for category, category_data in all_data.items():
        category_summary = {}
        category_records = 0
        
        if isinstance(category_data, dict):
            for source, df in category_data.items():
                if hasattr(df, '__len__'):
                    source_records = len(df)
                    category_records += source_records
                    category_summary[source] = {
                        'records': source_records,
                        'columns': list(df.columns) if hasattr(df, 'columns') else 'N/A',
                        'seasons': list(df.index.get_level_values('season').unique()) 
                                 if hasattr(df, 'index') and 'season' in getattr(df.index, 'names', []) 
                                 else 'N/A'
                    }
        
        summary['data_summary'][category] = {
            'total_records': category_records,
            'sources': category_summary
        }
        total_records += category_records
    
    summary['data_summary']['total_records'] = total_records
    
    # Quality assessment
    if total_records > 0:
        summary['quality_metrics']['completeness'] = 'Good'
        summary['recommendations'].append("Data extraction completed successfully")
    else:
        summary['quality_metrics']['completeness'] = 'Poor'
        summary['recommendations'].append("Low data volume - verify source connections")
    
    # Add specific recommendations based on data
    if 'team_data' in all_data and all_data['team_data']:
        summary['recommendations'].append("Team data available for tactical analysis")
    
    if 'player_data' in all_data and all_data['player_data']:
        summary['recommendations'].append("Player data available for individual performance analysis")
    
    logger.info("✅ Summary report generated")
    return summary

def save_results(all_data: Dict[str, Any], summary: Dict[str, Any], extractor: PSGDataExtractor):
    """
    Save extraction results to files.
    
    Parameters
    ----------
    all_data : Dict[str, Any]
        All extracted data
    summary : Dict[str, Any]
        Summary report
    extractor : PSGDataExtractor
        Extractor instance with data directory
    """
    logger.info("💾 Saving extraction results...")
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    # Save summary report
    import json
    summary_path = extractor.data_dir / "processed" / f"extraction_summary_{timestamp}.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📋 Summary saved to: {summary_path}")
    
    # Save data status file
    status = {
        'extraction_completed': True,
        'timestamp': timestamp,
        'total_records': summary['data_summary']['total_records'],
        'categories': list(all_data.keys())
    }
    
    status_path = extractor.data_dir / "processed" / "extraction_status.json"
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)
    
    logger.info("✅ Results saved successfully")

def main():
    """Main execution function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Extract comprehensive PSG data for tactical analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Extract all data
    python run_psg_extraction.py --all
    
    # Extract only team stats
    python run_psg_extraction.py --team-stats
    
    # Extract specific seasons
    python run_psg_extraction.py --seasons 2023-24 2024-25 --all
    
    # Custom leagues and verbose output
    python run_psg_extraction.py --leagues "FRA-Ligue 1" --verbose --all
        """
    )
    
    # Data selection arguments
    parser.add_argument(
        '--all', 
        action='store_true',
        help='Extract all available data (team stats, player stats, match data)'
    )
    
    parser.add_argument(
        '--team-stats',
        action='store_true',
        help='Extract team season statistics'
    )
    
    parser.add_argument(
        '--player-stats',
        action='store_true',
        help='Extract player season statistics'
    )
    
    parser.add_argument(
        '--match-data',
        action='store_true',
        help='Extract match-by-match data'
    )
    
    # Configuration arguments
    parser.add_argument(
        '--seasons',
        nargs='+',
        default=TARGET_SEASONS,
        help=f'Seasons to extract (default: {TARGET_SEASONS})'
    )
    
    parser.add_argument(
        '--leagues',
        nargs='+',
        default=TARGET_LEAGUES,
        help=f'Leagues to include (default: {TARGET_LEAGUES})'
    )
    
    # Execution arguments
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable data caching (force fresh downloads)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be extracted without actually doing it'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    psg_logger = setup_logging()
    
    # Handle --all flag
    if args.all:
        args.team_stats = True
        args.player_stats = True
        args.match_data = True
    
    # Validate at least one extraction type is selected
    if not any([args.team_stats, args.player_stats, args.match_data]):
        parser.error("Must specify at least one extraction type (--team-stats, --player-stats, --match-data, or --all)")
    
    # Show extraction plan if dry run
    if args.dry_run:
        logger.info("🔍 DRY RUN - Extraction Plan:")
        logger.info(f"  Seasons: {args.seasons}")
        logger.info(f"  Leagues: {args.leagues}")
        logger.info(f"  Team Stats: {args.team_stats}")
        logger.info(f"  Player Stats: {args.player_stats}")
        logger.info(f"  Match Data: {args.match_data}")
        logger.info("  Use --verbose for detailed output")
        return
    
    start_time = datetime.now(timezone.utc)
    
    try:
        logger.info("🚀 PSG Data Extraction Starting...")
        logger.info(f"📅 Target seasons: {args.seasons}")
        logger.info(f"🏆 Target leagues: {args.leagues}")
        
        # Initialize extractor
        extractor = PSGDataExtractor(
            seasons=args.seasons,
            leagues=args.leagues
        )
        
        # Extract data based on arguments
        all_data = {}
        
        if args.team_stats or args.match_data:
            team_data = extract_team_data(extractor, args)
            all_data.update({'team_data': team_data})
        
        if args.player_stats:
            player_data = extract_player_data(extractor, args)
            all_data.update({'player_data': player_data})
        
        # Generate summary and save results
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        summary = generate_summary_report(all_data, extractor)
        summary['extraction_metadata']['extraction_duration'] = f"{duration:.2f} seconds"
        
        save_results(all_data, summary, extractor)
        
        # Final report
        logger.info("🎉 PSG Data Extraction Completed Successfully!")
        logger.info(f"⏱️  Total duration: {duration:.2f} seconds")
        logger.info(f"📊 Total records extracted: {summary['data_summary']['total_records']}")
        logger.info(f"📁 Data saved to: {extractor.data_dir}")
        
        return all_data
        
    except Exception as e:
        logger.error("❌ PSG Data Extraction Failed!")
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()