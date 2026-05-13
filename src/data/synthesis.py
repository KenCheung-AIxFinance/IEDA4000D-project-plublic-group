"""
Synthetic Data Generation - Main Orchestrator

Multi-method microdata synthesis from NCES aggregate tables.
Supports 5 methods: heuristic, ipf, copula, bayesian, sri
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Import synthesizers from synthesis package
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.synthesis import METHOD_MAP


def synthesize_all_methods(
    n: int = 10000,
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run all synthesis methods and save outputs.

    Parameters:
    - n: Number of synthetic records per method
    - seed: Random seed for reproducibility
    - output_dir: Output directory (default: outputs/tables)

    Returns:
    - metadata: Combined metadata for all methods
    """
    project_root = Path('.').resolve()
    if output_dir is None:
        output_dir = project_root / 'outputs' / 'tables'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load NCES data
    nces_path = project_root / 'outputs' / 'tables' / 'nces_postsecondary_tidy.csv'
    nces_df = pd.read_csv(nces_path)

    print(f"Loaded NCES data: {len(nces_df)} rows")
    print(f"Output directory: {output_dir}")

    # Combined metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'n': n,
        'seed': seed,
        'methods': {}
    }

    # Run each method
    for method_name, synthesizer_class in METHOD_MAP.items():
        print(f"\n{'='*50}")
        print(f"Synthesizing with {method_name}")
        print('='*50)

        try:
            # Create synthesizer
            synthesizer = synthesizer_class(n=n, seed=seed)

            # Run synthesis pipeline
            synthetic_df = synthesizer.run(nces_df)

            # Validate schema
            synthesizer.validate_output_schema(synthetic_df)

            # Save CSV
            output_path = output_dir / f'synthetic_students_{method_name}.csv'
            synthetic_df.to_csv(output_path, index=False)
            print(f"Saved {len(synthetic_df)} records to {output_path}")

            # Print summary statistics
            print(f"\n  Sex:     {synthetic_df['sex'].value_counts().to_dict()}")
            print(f"  SES:     {synthetic_df['ses'].value_counts().to_dict()}")
            print(f"  Calculus: {synthetic_df['calculus'].mean()*100:.1f}%")
            print(f"  STEM:    {synthetic_df['stem_major'].mean()*100:.1f}%")

            # Add to metadata
            metadata['methods'][method_name] = synthesizer.metadata

        except Exception as e:
            print(f"ERROR in {method_name}: {e}")
            metadata['methods'][method_name] = {
                'error': str(e),
                'status': 'failed'
            }

    # Save combined metadata
    metadata_path = output_dir / 'synthesis_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)

    print(f"\n{'='*50}")
    print(f"Synthesis Complete!")
    print('='*50)
    print(f"Metadata saved to: {metadata_path}")
    print(f"\nGenerated files:")
    for method_name in METHOD_MAP.keys():
        csv_path = output_dir / f'synthetic_students_{method_name}.csv'
        if csv_path.exists():
            print(f"  - {csv_path.name}")

    return metadata


def synthesize_single_method(
    method: str,
    n: int = 10000,
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run single synthesis method.

    Parameters:
    - method: Method name ('heuristic', 'ipf', 'copula', 'bayesian', 'sri')
    - n: Number of synthetic records
    - seed: Random seed
    - output_dir: Output directory

    Returns:
    - synthetic_df: Generated synthetic DataFrame
    """
    if method not in METHOD_MAP:
        raise ValueError(
            f"Unknown method: {method}. Available: {list(METHOD_MAP.keys())}"
        )

    project_root = Path('.').resolve()
    if output_dir is None:
        output_dir = project_root / 'outputs' / 'tables'

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load NCES data
    nces_path = project_root / 'outputs' / 'tables' / 'nces_postsecondary_tidy.csv'
    nces_df = pd.read_csv(nces_path)

    # Create synthesizer
    synthesizer_class = METHOD_MAP[method]
    synthesizer = synthesizer_class(n=n, seed=seed)

    # Run synthesis
    synthetic_df = synthesizer.run(nces_df)

    # Validate and save
    synthesizer.validate_output_schema(synthetic_df)
    output_path = output_dir / f'synthetic_students_{method}.csv'
    synthetic_df.to_csv(output_path, index=False)

    print(f"Generated {len(synthetic_df)} records using {method}")
    print(f"Saved to: {output_path}")

    return synthetic_df


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Synthetic data generation from NCES tables'
    )
    parser.add_argument(
        '--method',
        choices=['all', 'heuristic', 'ipf', 'copula', 'bayesian', 'sri'],
        default='all',
        help='Synthesis method to run'
    )
    parser.add_argument(
        '--n',
        type=int,
        default=10000,
        help='Number of synthetic records'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs/tables',
        help='Output directory'
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    if args.method == 'all':
        synthesize_all_methods(args.n, args.seed, output_dir)
    else:
        synthesize_single_method(args.method, args.n, args.seed, output_dir)


if __name__ == '__main__':
    main()
