#!/usr/bin/env python3
"""
Comprehensive QASE Test Suite
Tests all mathematical frameworks and integration points.
"""

import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, '.')

def test_prime_utilities():
    """Test PrimeUtilities class."""
    print("Testing PrimeUtilities...")
    from xauusd_qase import PrimeUtilities
    
    # Test is_prime
    assert PrimeUtilities.is_prime(2) == True
    assert PrimeUtilities.is_prime(3) == True
    assert PrimeUtilities.is_prime(4) == False
    assert PrimeUtilities.is_prime(17) == True
    print("  ✓ is_prime works correctly")
    
    # Test prime_factors
    assert PrimeUtilities.prime_factors(100) == [2, 2, 5, 5]
    assert PrimeUtilities.prime_factors(123) == [3, 41]
    assert PrimeUtilities.prime_factors(997) == [997]
    print("  ✓ prime_factors works correctly")
    
    # Test prime_sieve
    primes = PrimeUtilities.prime_sieve(100)
    assert primes == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
    print("  ✓ prime_sieve works correctly")
    
    # Test p-adic valuation
    assert PrimeUtilities.p_adic_valuation(100, 2) == 2
    assert PrimeUtilities.p_adic_valuation(100, 5) == 2
    assert PrimeUtilities.p_adic_valuation(100, 3) == 0
    print("  ✓ p_adic_valuation works correctly")
    
    # Test p-adic distance
    assert PrimeUtilities.p_adic_distance(100, 150, 5) == 0.04
    assert PrimeUtilities.p_adic_distance(100, 100, 5) == 0.0
    print("  ✓ p_adic_distance works correctly")

def test_iutt_alignment():
    """Test IUTT Alignment Engine."""
    print("\nTesting IUTT Alignment Engine...")
    from xauusd_qase import IUTTAlignmentEngine
    
    engine = IUTTAlignmentEngine()
    
    # Create test data
    np.random.seed(42)
    n_points = 100
    
    # Micro ticks (Universe A)
    micro_ticks = np.linspace(2000, 2010, n_points) + np.random.normal(0, 0.1, n_points)
    
    # Macro profile (Universe B)
    macro_profile = np.linspace(2000, 2010, n_points)
    
    # Perform mapping
    result = engine.map_universes(micro_ticks, macro_profile)
    
    assert 'teichmuller_distance' in result
    assert 'equilibrium_point' in result
    assert 'universe_a' in result
    assert 'universe_b' in result
    print("  ✓ IUTT mapping produces valid results")
    print(f"    - Teichmüller Distance: {result['teichmuller_distance']:.4f}")
    print(f"    - Equilibrium Price: {result['equilibrium_point']['price']:.4f}")

def test_padic_quantum():
    """Test p-adic Quantum Engine."""
    print("\nTesting p-adic Quantum Engine...")
    from xauusd_qase import PAdicQuantumEngine
    
    engine = PAdicQuantumEngine()
    
    # Create test order book
    np.random.seed(42)
    n_levels = 20
    base_price = 2000.0
    
    bid_prices = base_price - np.arange(0.1, 0.1 * n_levels + 0.1, 0.1)
    bid_volumes = np.random.randint(10, 1000, n_levels)
    
    ask_prices = base_price + np.arange(0.1, 0.1 * n_levels + 0.1, 0.1)
    ask_volumes = np.random.randint(10, 1000, n_levels)
    
    order_book = pd.DataFrame({
        'price': np.concatenate([bid_prices, ask_prices]),
        'volume': np.concatenate([bid_volumes, ask_volumes]),
        'side': ['buy'] * n_levels + ['sell'] * n_levels
    })
    
    # Perform analysis
    result = engine.analyze_order_book(order_book)
    
    assert 'liquidity_clusters' in result
    assert 'prime_divisibility_score' in result
    assert 'langlands_signal' in result
    assert 'p_adic_distances' in result
    print("  ✓ p-adic analysis produces valid results")
    print(f"    - Divisibility Score: {result['prime_divisibility_score']:.2f}")
    print(f"    - Langlands Signal: {result['langlands_signal']['signal']:.4f}")

def test_ncg_quantum():
    """Test Non-Commutative Geometry Engine."""
    print("\nTesting Non-Commutative Geometry Engine...")
    from xauusd_qase import NonCommutativeGeometryEngine
    
    engine = NonCommutativeGeometryEngine()
    
    # Create test order book
    np.random.seed(42)
    n_levels = 20
    base_price = 2000.0
    
    bid_prices = base_price - np.arange(0.1, 0.1 * n_levels + 0.1, 0.1)
    bid_volumes = np.random.randint(10, 1000, n_levels)
    
    ask_prices = base_price + np.arange(0.1, 0.1 * n_levels + 0.1, 0.1)
    ask_volumes = np.random.randint(10, 1000, n_levels)
    
    order_book = pd.DataFrame({
        'price': np.concatenate([bid_prices, ask_prices]),
        'volume': np.concatenate([bid_volumes, ask_volumes]),
        'side': ['buy'] * n_levels + ['sell'] * n_levels
    })
    
    # Perform analysis
    result = engine.analyze_order_book_ncg(order_book)
    
    assert 'commutator_norm' in result
    assert 'uncertainty' in result
    assert 'iceberg_signal' in result
    assert 'quantum_state' in result
    print("  ✓ NCG analysis produces valid results")
    print(f"    - Commutator Norm: {result['commutator_norm']:.2f}")
    print(f"    - Uncertainty: {result['uncertainty']:.2f}")

def test_hott_engine():
    """Test Homotopy Type Theory Engine."""
    print("\nTesting Homotopy Type Theory Engine...")
    from xauusd_qase import HomotopyTypeTheoryEngine
    
    engine = HomotopyTypeTheoryEngine()
    
    # Create test data
    np.random.seed(42)
    n_points = 100
    price_data = pd.DataFrame({
        'open': np.linspace(2000, 2010, n_points),
        'high': np.linspace(2001, 2011, n_points),
        'low': np.linspace(1999, 2009, n_points),
        'close': np.linspace(2000, 2010, n_points),
        'volume': np.random.randint(1000, 5000, n_points)
    })
    
    # Perform analysis
    result = engine.initialize_state_space(price_data)
    
    assert 'manifold_size' in result
    assert 'curvature' in result
    assert 'dimension' in result
    print("  ✓ HoTT analysis produces valid results")
    print(f"    - Manifold Size: {result['manifold_size']}")
    print(f"    - Curvature: {result['curvature']:.4f}")
    print(f"    - Dimension: {result['dimension']}")

def test_full_qase():
    """Test full QASE analysis."""
    print("\nTesting Full QASE Analysis...")
    from xauusd_qase import QuantumAlgebraicSymmetryEngine
    
    qase = QuantumAlgebraicSymmetryEngine()
    
    # Create test data
    np.random.seed(42)
    n_points = 100
    price_data = pd.DataFrame({
        'open': np.linspace(2000, 2010, n_points),
        'high': np.linspace(2001, 2011, n_points),
        'low': np.linspace(1999, 2009, n_points),
        'close': np.linspace(2000, 2010, n_points),
        'volume': np.random.randint(1000, 5000, n_points)
    })
    
    macro_data = pd.DataFrame({
        'close': np.linspace(2000, 2010, n_points)
    })
    
    # Perform full analysis
    results = qase.full_analysis(price_data, macro_data=macro_data)
    
    assert 'engines' in results
    assert 'recommendation' in results
    assert 'market_state' in results
    
    # Check that engines are present
    engines = results['engines']
    assert 'iutt' in engines
    assert 'hott' in engines
    
    # Check recommendation
    rec = results['recommendation']
    assert 'action' in rec
    assert 'confidence' in rec
    
    print("  ✓ Full QASE analysis produces valid results")
    print(f"    - Recommendation: {rec['action']}")
    print(f"    - Confidence: {rec['confidence']:.4f}")
    print(f"    - Engines: {list(engines.keys())}")

def test_qase_engine_wrapper():
    """Test QASEEngine wrapper in main bot."""
    print("\nTesting QASEEngine Wrapper...")
    
    # Read the main bot file and check for QASEEngine
    with open('xauusd_god_bot.py', 'r') as f:
        content = f.read()
    
    # Check for QASEEngine class
    assert 'class QASEEngine:' in content
    print("  ✓ QASEEngine class found")
    
    # Check for QASE initialization
    assert 'self.qase = QASEEngine(config)' in content
    print("  ✓ QASEEngine initialization found")
    
    # Check for QASE analysis call
    assert 'self.qase.analyze(' in content
    print("  ✓ QASE analysis call found")
    
    # Check for QASE TUI update
    assert 'self.tui.update("qase", qase_result)' in content
    print("  ✓ QASE TUI update found")

def main():
    """Run all QASE tests."""
    print("=" * 70)
    print("COMPREHENSIVE QASE TEST SUITE")
    print("=" * 70)
    
    try:
        # Run all tests
        test_prime_utilities()
        test_iutt_alignment()
        test_padic_quantum()
        test_ncg_quantum()
        test_hott_engine()
        test_full_qase()
        test_qase_engine_wrapper()
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)