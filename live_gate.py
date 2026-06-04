#!/usr/bin/env python3
"""
Live Gate - Main Power Button
Start the Quantum Trading Machine
"""

import sys
import signal
import time
import random

# Quantum Brain imports
from quantum_brain import QuantumMathEngine, IntelligenceMatrix

# FIX Pipeline imports
from fix_pipeline import TcpSocket, FixEncoder, SocketError


def signal_handler(signum, frame):
    print("\n[SHUTDOWN] Power off...")
    sys.exit(0)


def main():
    """Main entry point - Power on the machine"""
    print("=" * 70)
    print("  QUANTUM TRADING MACHINE v2.0")
    print("  Pure Cython + Raw C-Sockets Architecture")
    print("=" * 70)
    print()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load configuration from .env
    print("[CONFIG] Loading .env configuration...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    import os
    FIX_HOST = os.getenv('FIX_HOST', 'live-uk-eqx-01.p.c-trader.com')
    FIX_PORT = int(os.getenv('FIX_PORT', '5212'))
    SENDER_COMP_ID = os.getenv('SENDER_COMP_ID', 'your_sender_comp_id')
    TARGET_COMP_ID = os.getenv('TARGET_COMP_ID', 'cServer')
    SENDER_SUB_ID = os.getenv('SENDER_SUB_ID', 'TRADE')
    FIX_PASSWORD = os.getenv('FIX_PASSWORD', 'your_fix_password')

    print(f"  Host: {FIX_HOST}:{FIX_PORT}")
    print(f"  Sender: {SENDER_COMP_ID}")
    print(f"  Target: {TARGET_COMP_ID}")
    print()

    # Initialize Quantum Brain
    print("[QUANTUM BRAIN] Initializing 100+ mathematical filters...")
    quantum_engine = QuantumMathEngine(lookback=500)
    intelligence = IntelligenceMatrix()
    print("  Mathematical filters: READY")
    print("  Intelligence matrix: READY (28 ML + 5 RL)")
    print()

    # Initialize FIX Pipeline
    print("[FIX PIPELINE] Initializing high-speed routing...")
    encoder = FixEncoder(
        sender_comp_id=SENDER_COMP_ID,
        target_comp_id=TARGET_COMP_ID,
        sender_sub_id=SENDER_SUB_ID,
        heartbeat_interval=30
    )
    socket = TcpSocket(host=FIX_HOST, port=FIX_PORT, timeout=30.0)
    print("  Order encoder: READY")
    print("  Network socket: READY")
    print()

    # Connect to cTrader
    print("[CONNECT] Connecting to cTrader FIX gateway...")
    try:
        socket.connect()
        print("  Connected successfully!")
    except SocketError as e:
        print(f"  Connection failed: {e}")
        print("  (Running in demo mode with simulated ticks)")
        socket = None

    # Logon
    if socket:
        print("[LOGON] Sending logon message...")
        try:
            logon_msg = encoder.create_logon(FIX_PASSWORD)
            socket.send(logon_msg.replace("|", "\x01").encode('ascii'))
            print("  Logon sent!")
        except Exception as e:
            print(f"  Logon failed: {e}")

    # Main engine loop
    print()
    print("[ENGINE] Starting main engine loop...")
    print("[ENGINE] Press Ctrl+C to stop")
    print()

    tick_count = 0
    buy_count = 0
    sell_count = 0
    hold_count = 0
    start_time = time.time()

    try:
        while True:
            tick_count += 1

            # Generate simulated tick (replace with real feed)
            base_price = 2350.0 + random.uniform(-0.5, 0.5)
            timestamp = time.time()
            bid = base_price
            ask = base_price + 0.10
            volume = random.uniform(0.1, 1.0)

            # STAGE 1: Quantum Mathematical Filters
            quantum_metrics = quantum_engine.process_tick(
                timestamp=timestamp, bid=bid, ask=ask, volume=volume
            )

            # STAGE 2: Intelligence Matrix (ML/RL Ensemble)
            ensemble_prediction = intelligence.process_quantum_metrics(quantum_metrics)

            # STAGE 3: Decision Logic
            composite = ensemble_prediction.final_ensemble_signal
            confidence = ensemble_prediction.ensemble_confidence

            # Generate order
            if abs(composite) > 0.15 and confidence > 0.3:
                side = "1" if composite > 0 else "2"
                quantity = 0.01 + abs(composite) * 0.1
                order_price = bid if side == "1" else ask
                cl_ord_id = f"ORD-{int(time.time() * 1000)}-{tick_count:06d}"

                # Generate FIX message
                fix_msg = encoder.create_new_order(
                    cl_ord_id=cl_ord_id,
                    symbol="XAUUSD",
                    side=side,
                    quantity=quantity,
                    price=order_price
                )

                # Send via socket
                if socket and socket.is_connected:
                    try:
                        socket.send(fix_msg.replace("|", "\x01").encode('ascii'))
                    except:
                        pass

                if side == "1":
                    buy_count += 1
                    action = "BUY"
                else:
                    sell_count += 1
                    action = "SELL"

                print(f"  Tick #{tick_count}: {action} | Signal={composite:+.4f} | Conf={confidence:.2f} | Price={order_price:.5f}")
            else:
                hold_count += 1
                if tick_count % 10 == 0:
                    print(f"  Tick #{tick_count}: HOLD | Signal={composite:+.4f} | Conf={confidence:.2f}")

            # Print stats every 100 ticks
            if tick_count % 100 == 0:
                elapsed = time.time() - start_time
                tps = tick_count / max(elapsed, 0.001)
                print(f"\n  [STATS] Ticks={tick_count} | TPS={tps:.0f} | Buy={buy_count} | Sell={sell_count} | Hold={hold_count}\n")

            # Small delay to simulate real tick rate
            time.sleep(0.001)

    except KeyboardInterrupt:
        pass
    finally:
        # Shutdown
        elapsed = time.time() - start_time
        tps = tick_count / max(elapsed, 0.001)
        print()
        print("=" * 70)
        print("  SHUTDOWN SUMMARY")
        print("=" * 70)
        print(f"  Total ticks: {tick_count}")
        print(f"  Runtime: {elapsed:.1f} seconds")
        print(f"  Throughput: {tps:.0f} ticks/sec")
        print(f"  Trades: Buy={buy_count} | Sell={sell_count} | Hold={hold_count}")
        print("=" * 70)

        if socket:
            try:
                logout_msg = encoder.create_logout("Engine shutdown")
                socket.send(logout_msg.replace("|", "\x01").encode('ascii'))
                socket.close()
            except:
                pass

        print("[SHUTDOWN] Power off complete")


if __name__ == "__main__":
    main()
