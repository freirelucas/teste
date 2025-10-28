"""
Helper utilities for data processing and analysis.
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd


def load_config(config_path: str = "config/config.yaml") -> Dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_api_key(env_var: str = "OVERTON_API_KEY") -> Optional[str]:
    """
    Load API key from environment variable.

    Args:
        env_var: Name of the environment variable

    Returns:
        API key or None if not found
    """
    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv(env_var)


def format_time(seconds: float) -> str:
    """
    Format time duration in human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}min"
    else:
        return f"{seconds/3600:.1f}h"


def clean_doi(doi: str) -> Optional[str]:
    """
    Clean and normalize a DOI string.

    Args:
        doi: Raw DOI string

    Returns:
        Cleaned DOI or None if invalid
    """
    if not doi or not isinstance(doi, str):
        return None

    # Remove common prefixes
    doi = doi.strip()
    if doi.startswith('https://doi.org/'):
        doi = doi.replace('https://doi.org/', '')
    elif doi.startswith('http://dx.doi.org/'):
        doi = doi.replace('http://dx.doi.org/', '')
    elif doi.startswith('doi:'):
        doi = doi.replace('doi:', '')

    # Basic validation
    if '/' in doi and len(doi) > 5:
        return doi
    return None


def save_json(data: Any, filepath: str, indent: int = 2):
    """
    Save data to JSON file.

    Args:
        data: Data to save
        filepath: Output file path
        indent: JSON indentation
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_json(filepath: str) -> Any:
    """
    Load data from JSON file.

    Args:
        filepath: Input file path

    Returns:
        Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_dataframe(df: pd.DataFrame, filepath: str):
    """
    Save DataFrame to CSV file.

    Args:
        df: DataFrame to save
        filepath: Output file path
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)


def create_checkpoint(data: Dict, checkpoint_dir: str = "data/checkpoints"):
    """
    Create a checkpoint file with timestamp.

    Args:
        data: Data to checkpoint
        checkpoint_dir: Directory for checkpoint files

    Returns:
        Path to checkpoint file
    """
    Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_path = f"{checkpoint_dir}/checkpoint_{timestamp}.json"
    save_json(data, checkpoint_path)
    return checkpoint_path


def load_latest_checkpoint(checkpoint_dir: str = "data/checkpoints") -> Optional[Dict]:
    """
    Load the most recent checkpoint file.

    Args:
        checkpoint_dir: Directory containing checkpoint files

    Returns:
        Checkpoint data or None if no checkpoints found
    """
    checkpoint_path = Path(checkpoint_dir)
    if not checkpoint_path.exists():
        return None

    checkpoint_files = list(checkpoint_path.glob("checkpoint_*.json"))
    if not checkpoint_files:
        return None

    latest_file = max(checkpoint_files, key=lambda p: p.stat().st_mtime)
    return load_json(str(latest_file))


def extract_dois_from_policy_docs(policy_docs: List[Dict]) -> List[str]:
    """
    Extract unique DOIs cited in policy documents.

    Args:
        policy_docs: List of policy document dictionaries

    Returns:
        List of unique DOIs
    """
    dois = set()

    for doc in policy_docs:
        # Extract from 'cites' field
        cites = doc.get('cites', {})
        if isinstance(cites, dict):
            scholarly_cites = cites.get('scholarly', [])
            if isinstance(scholarly_cites, list):
                for cite in scholarly_cites:
                    if isinstance(cite, dict):
                        doi = cite.get('doi')
                        if doi:
                            cleaned_doi = clean_doi(doi)
                            if cleaned_doi:
                                dois.add(cleaned_doi)

    return sorted(list(dois))


class ProgressTracker:
    """Track progress of long-running operations."""

    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items
            description: Description of the operation
        """
        self.total = total
        self.description = description
        self.processed = 0
        self.start_time = datetime.now()

    def update(self, increment: int = 1):
        """
        Update progress.

        Args:
            increment: Number of items processed
        """
        self.processed += increment
        elapsed = (datetime.now() - self.start_time).total_seconds()

        if self.processed > 0:
            rate = self.processed / elapsed
            remaining = (self.total - self.processed) / rate if rate > 0 else 0

            print(
                f"  {self.description}: {self.processed}/{self.total} "
                f"({100*self.processed/self.total:.1f}%) | "
                f"Elapsed: {format_time(elapsed)} | "
                f"Remaining: {format_time(remaining)}"
            )

    def complete(self):
        """Mark operation as complete."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"✓ {self.description} complete: {self.processed}/{self.total} in {format_time(elapsed)}")
