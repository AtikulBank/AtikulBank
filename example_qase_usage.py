#!/usr/bin/env python3
"""
Example usage of Quantum-Algebraic Symmetry Engine (QASE)
for XAUUSD market analysis.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Import QASE
from xauusd_qase import QuantumAlgebraicSymmetryEngine, PrimeUtilities

def generate_synthetic_xauusd_data(days=30):
    """Generate synthetic XAUUSD price data."""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=days*24, freq='h')
    
    # Simulate gold price movements
    base_price = 2000.0
    returns = np.random.normal(0, 0.002, len(dates))  # 0.2% hourly volatility
    prices = base_price * np.cumprod(1 + returns)
    
    # Create OHLCV data
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.uniform(-0.001, 0.001, len(dates))),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.003, len(dates)))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.003, len(dates)))),
        'close': prices,
        'volume': np.random.randint(1000, 10000, len(dates))
    })
    
    return data

def generate_synthetic_order_book():
    """Generate synthetic order book data."""
    np.random.seed(42)
    
    # Generate bid/ask levels
    base_price = 2000.0
    n_levels = 20
    
    # Bid levels (buy orders)
    bid_prices = base_price - np.arange(0.1, 0.1 * n_levels + 0.1, 0.1)
    bid_volumes = np.random.randint(10, 1000, n_levels)
    
    # Ask levels (sell orders)
    ask_prices = base_price + np.arange(0.1, 0.1 * n_levels + 0.1, 0.1)
    ask_volumes = np.random.randint(10, 1000, n_levels)
    
    # Combine into order book DataFrame
    order_book = pd.DataFrame({
        'price': np.concatenate([bid_prices, ask_prices]),
        'volume': np.concatenate([bid_volumes, ask_volumes]),
        'side': ['buy'] * n_levels + ['sell'] * n_levels
    })
    
    return order_book

def main():
    print("=" * 70)
    print("QUANTUM-ALGEBRAIC SYMMETRY ENGINE (QASE) - EXAMPLE USAGE")
    print("=" * 70)
    print()
    
    # Generate synthetic data
    print("1. Generating synthetic XAUUSD data...")
    price_data = generate_synthetic_xauusd_data(days=7)
    order_book = generate_synthetic_order_book()
    print(f"   - Price data: {len(price_data)} bars")
    print(f"   - Order book: {len(order_book)} levels")
    
    # Initialize QASE
    print("\n2. Initializing QASE engine...")
    qase = QuantumAlgebraicSymmetryEngine({
        'iutt_window': 100,
        'iutt_deformation': 0.5,
        'prime_range': (2, 31),
        'hbar': 1.0,
        'dimension': 10
    })
    
    # Set market state
    qase.update_market_state(
        regime="normal",
        volatility=0.02,
        liquidity=0.8,
        chaos_level="LOW"
    )
    print("   - Market state: normal regime, 2% volatility")
    
    # Perform full analysis
    print("\n3. Performing QASE analysis...")
    results = qase.full_analysis(
        price_data=price_data,
        order_book=order_book,
        macro_data=price_data[['close']]
    )
    
    # Display results
    print("\n4. Analysis Results:")
    print("-" * 50)
    
    # IUTT Results
    iutt = results.get("engines", {}).get("iutt", {})
    if "equilibrium_point" in iutt:
        eq = iutt["equilibrium_point"]
        print(f"IUTT Alignment:")
        print(f"  - Teichmüller Distance: {iutt.get('teichmuller_distance', 0):.4f}")
        print(f"  - Equilibrium Price: ${eq.get('price', 0):.2f}")
        print(f"  - Confidence: {eq.get('confidence', 0):.3f}")
    
    # p-adic Results
    padic = results.get("engines", {}).get("padic", {})
    if "langlands_signal" in padic:
        langlands = padic["langlands_signal"]
        print(f"\np-adic Quantum:")
        print(f"  - Prime Divisibility Score: {padic.get('prime_divisibility_score', 0):.2f}")
        print(f"  - Langlands Signal: {langlands.get('signal', 0):.3f}")
        print(f"  - Confidence: {langlands.get('confidence', 0):.3f}")
    
    # NCG Results
    ncg = results.get("engines", {}).get("ncg", {})
    if "quantum_state" in ncg:
        quantum_state = ncg["quantum_state"]
        print(f"\nNon-Commutative Geometry:")
        print(f"  - Commutator Norm: {ncg.get('commutator_norm', 0):.2f}")
        print(f"  - Uncertainty: {ncg.get('uncertainty', 0):.2f}")
        print(f"  - Iceberg Detected: {ncg.get('iceberg_signal', {}).get('detected', False)}")
        print(f"  - Quantum State Energy: {quantum_state.get('energy', 0):.2f}")
    
    # HoTT Results
    hott = results.get("engines", {}).get("hott", {})
    if "manifold_size" in hott:
        print(f"\nHomotopy Type Theory:")
        print(f"  - Manifold Size: {hott.get('manifold_size', 0)}")
        print(f"  - Curvature: {hott.get('curvature', 0):.3f}")
    
    # Final Recommendation
    print("\n" + "=" * 50)
    print("FINAL RECOMMENDATION:")
    print("=" * 50)
    recommendation = results.get("recommendation", {})
    print(f"  Action: {recommendation.get('action', 'N/A').upper()}")
    print(f"  Direction: {recommendation.get('direction', 0):.3f}")
    print(f"  Strength: {recommendation.get('strength', 0):.3f}")
    print(f"  Confidence: {recommendation.get('confidence', 0):.3f}")
    
    # Prime utilities demonstration
    print("\n" + "=" * 50)
    print("PRIME UTILITIES DEMONSTRATION:")
    print("=" * 50)
    
    # Test prime functions
    test_numbers = [100, 123, 997, 1024]
    for n in test_numbers:
        factors = PrimeUtilities.prime_factors(n)
        print(f"  {n} = {' × '.join(map(str, factors))}")
    
    # p-adic distance example
    x, y, p = 100, 150, 5
    distance = PrimeUtilities.p_adic_distance(x, y, p)
    print(f"\n  p-adic distance between {x} and {y} (p={p}): {distance:.6f}")
    
    print("\n" + "=" * 70)
    print("QASE Example Complete")
    print("=" * 70)

if __name__ == "__main__":
    main()