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
from fix_pipeline import TcpSocket, FixEncoder, FixDecoder, SocketError, FixMsgType


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
    decoder = FixDecoder()
    socket = TcpSocket(host=FIX_HOST, port=FIX_PORT, timeout=30.0)
    print("  Order encoder: READY")
    print("  Decoder: READY")
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
            time.sleep(1)  # Wait for logon response

            # Subscribe to market data for XAUUSD
            print("[SUBSCRIBE] Requesting live XAUUSD market data...")
            md_request = decoder.create_market_data_request(
                symbol="XAUUSD",
                sender=SENDER_COMP_ID,
                target=TARGET_COMP_ID,
                sub_id=SENDER_SUB_ID,
                request_id="XAUUSD_MD_1"
            )
            socket.send(md_request.replace("|", "\x01").encode('ascii'))
            print("  Market data subscription sent!")
        except Exception as e:
            print(f"  Logon/Subscribe failed: {e}")

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
    live_bid = 0.0
    live_ask = 0.0
    demo_mode = socket is None

    def receive_and_decode():
        """Receive FIX message from socket and decode it"""
        nonlocal live_bid, live_ask
        if not socket or not socket.is_connected:
            return None
        try:
            raw_data = socket.recv(65536)
            if raw_data:
                decoded = raw_data.decode('ascii', errors='ignore')
                result = decoder.decode_message(decoded)
                if result["type"] in ("market_data_snapshot", "market_data_incremental"):
                    tick = result["tick"]
                    if tick.bid_price > 0:
                        live_bid = tick.bid_price
                    if tick.ask_price > 0:
                        live_ask = tick.ask_price
                    print(f"  [LIVE] {tick.symbol} | Bid={tick.bid_price:.5f} | Ask={tick.ask_price:.5f} | Seq={tick.msg_seq_num}")
                    return result
                elif result["type"] == "heartbeat":
                    return result
                elif result["type"] == "logon":
                    print("  [LOGON] Server confirmed logon")
                    return result
                elif result["type"] == "reject":
                    print(f"  [REJECT] {result.get('text', 'Unknown')}")
                    return result
                else:
                    return result
        except SocketError as e:
            if "timeout" not in str(e).lower():
                print(f"  [ERROR] {e}")
        except Exception as e:
            pass
        return None

    try:
        while True:
            tick_count += 1

            # Receive live data from cTrader
            if not demo_mode:
                # Try to receive multiple messages
                for _ in range(10):
                    receive_and_decode()

            # Use live prices if available, otherwise use demo mode
            if live_bid > 0 and live_ask > 0:
                timestamp = time.time()
                bid = live_bid
                ask = live_ask
                volume = random.uniform(0.1, 1.0)
            else:
                # Demo mode with simulated tick
                base_price = 2350.0 + random.uniform(-0.5, 0.5)
                timestamp = time.time()
                bid = base_price
                ask = base_price + 0.10
                volume = random.uniform(0.1, 1.0)
                if tick_count == 1:
                    print("  [DEMO] Using simulated ticks - waiting for live feed...")

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
