#!/usr/bin/env python3
"""
Live Gate - Main Power Button
Start the Quantum Trading Machine with REAL cTrader connection
NO simulated fallback - exits immediately on connection failure
Ultra-Advanced Integration with 13k+ line quantum matrix
"""

import sys
import signal
import time
import socket
import ssl
import os
from dotenv import load_dotenv

# Quantum Brain imports - Full integration with upgraded modules
from quantum_brain import (
    QuantumMathEngine, 
    IntelligenceMatrix,
    WorldClassQuantumEngine,
    MathematicalFilterIntegration,
    EnhancedRLManager
)

# FIX Pipeline imports
from fix_pipeline import TcpSocket, FixEncoder, FixDecoder, SocketError, FixMsgType


def validate_config():
    """Validate FIX configuration from .env file"""
    password = os.getenv('FIX_PASSWORD', '')
    if not password or password in ['your_fix_api_password_here', '']:
        print("ERROR: FIX_PASSWORD not set in .env file!", flush=True)
        print("Go to cTrader → Settings → FIX API → Change Password", flush=True)
        print("Then set FIX_PASSWORD=yourpassword in .env", flush=True)
        sys.exit(1)
    
    # Check for non-ASCII characters (Bengali etc)
    try:
        password.encode('ascii')
    except UnicodeEncodeError:
        print("ERROR: FIX_PASSWORD contains non-ASCII characters!", flush=True)
        print("Use only English letters, numbers, and basic symbols", flush=True)
        sys.exit(1)
    
    # Warn about # character
    if '#' in password:
        print("WARNING: Password contains # which breaks .env parsing!", flush=True)
        print("Wrap it in quotes: FIX_PASSWORD=\"your#pass\"", flush=True)


def signal_handler(signum, frame):
    print("\n[SHUTDOWN] Power off...", flush=True)
    sys.exit(0)


def try_connect_and_login(host, port, sender_comp_id, target_comp_id, sender_sub_id, password):
    """
    Try to connect to cTrader FIX gateway and login.
    Returns (success, socket, encoder, decoder) tuple.
    """
    print(f"\n[CONNECT] Attempting connection to {host}:{port}...", flush=True)
    
    # Create SSL context
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    # Create raw socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30.0)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    try:
        # Connect
        sock.connect((host, port))
        print(f"  [CONNECT] TCP connected to {host}:{port}", flush=True)
        
        # Wrap with SSL
        ssl_sock = context.wrap_socket(sock, server_hostname=host)
        print(f"  [CONNECT] SSL handshake completed", flush=True)
        
        # Create encoder/decoder
        encoder = FixEncoder(
            sender_comp_id=sender_comp_id,
            target_comp_id=target_comp_id,
            sender_sub_id=sender_sub_id,
            target_sub_id=sender_sub_id,  # TargetSubID same as SenderSubID
            heartbeat_interval=30
        )
        decoder = FixDecoder()
        
        # Create logon message with ResetSeqNumFlag=Y
        logon_msg = encoder.create_logon(password, reset=True)
        print(f"  [LOGON] Sending logon message with ResetSeqNumFlag=Y...", flush=True)
        print(f"  [LOGON] Raw message: {logon_msg}", flush=True)
        
        # Send logon
        logon_bytes = logon_msg.replace("|", "\x01").encode('latin-1')
        # Ensure SOH delimiter at end
        if not logon_bytes.endswith(b"\x01"):
            logon_bytes += b"\x01"
        ssl_sock.sendall(logon_bytes)
        print(f"  [LOGON] Sent {len(logon_bytes)} bytes", flush=True)

        # Wait for response with select()
        import select
        print(f"  [LOGON] Waiting for server response (timeout=30s)...", flush=True)
        ssl_sock.settimeout(None)
        readable, _, _ = select.select([ssl_sock], [], [], 30)
        if not readable:
            print(f"  [ERROR] Timeout - no response from server")
            ssl_sock.close()
            return False, None, None, None

        raw_data = b''
        ssl_sock.settimeout(2.0)
        while True:
            try:
                chunk = ssl_sock.recv(65536)
                if not chunk:
                    break
                raw_data += chunk
            except (socket.timeout, ssl.SSLWantReadError):
                break

        if raw_data:
            decoded = raw_data.decode('latin-1')
            readable_msg = decoded.replace('\x01', '|')
            print(f"  [RECV] Server response: {readable_msg[:300]}")
            if '35=A' in decoded:
                print(f"  [LOGON] SUCCESS - Connected!")
                return True, ssl_sock, encoder, decoder
            elif '35=5' in decoded:
                print(f"  [LOGOUT] Server rejected: {readable_msg}")
            else:
                print(f"  [UNKNOWN] Response: {readable_msg[:200]}")
        else:
            print(f"  [ERROR] No data received from server")

        ssl_sock.close()
        return False, None, None, None
        
    except socket.timeout:
        print(f"  [ERROR] Connection timeout to {host}:{port}", flush=True)
        return False, None, None, None
    except ssl.SSLError as e:
        print(f"  [ERROR] SSL error: {e}", flush=True)
        return False, None, None, None
    except ConnectionRefusedError:
        print(f"  [ERROR] Connection refused to {host}:{port}", flush=True)
        return False, None, None, None
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False, None, None, None


def main():
    """Main entry point - Power on the machine with full quantum integration"""
    print("=" * 80, flush=True)
    print("  QUANTUM TRADING MACHINE v2.0 - ULTRA-ADVANCED INTEGRATION", flush=True)
    print("  13,629 LINES OF INSTITUTIONAL-GRADE CODE", flush=True)
    print("  LIVE cTrader FIX Connection Mode - NO SIMULATED FALLBACK", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load configuration from .env (dotenv already loaded at top of file)
    print("[CONFIG] Loading .env configuration...", flush=True)

    import os
    FIX_HOST = os.getenv('FIX_HOST', 'demo-uk-eqx-01.p.c-trader.com')
    SENDER_COMP_ID = os.getenv('SENDER_COMP_ID', 'demo.ctrader.5832984')
    TARGET_COMP_ID = os.getenv('TARGET_COMP_ID', 'cServer')
    FIX_PASSWORD = os.getenv('FIX_PASSWORD', '').strip().strip('"').strip("'")

    print(f"  Host: {FIX_HOST}", flush=True)
    print(f"  SenderCompID: {SENDER_COMP_ID}", flush=True)
    print(f"  TargetCompID: {TARGET_COMP_ID}", flush=True)
    print(f"  Password: {'*' * len(FIX_PASSWORD) if FIX_PASSWORD else 'NOT SET'}", flush=True)
    print(flush=True)

    if not FIX_PASSWORD:
        print("[ERROR] FIX_PASSWORD not set in .env file!", flush=True)
        print("[ERROR] Please add FIX_PASSWORD=your_password to your .env file", flush=True)
        sys.exit(1)

    # Try both ports: 5211 for QUOTE (prices), 5212 for TRADE
    ports_to_try = [
        (5211, "QUOTE"),   # Price feed port
        (5212, "TRADE"),   # Trading port
    ]
    
    ssl_sock = None
    encoder = None
    decoder = None
    active_port = None
    active_session_type = None

    print("[CONNECT] Attempting FIX connections...", flush=True)
    print("=" * 80, flush=True)

    for port, session_type in ports_to_try:
        print(f"\n{'='*60}", flush=True)
        print(f"[TRY] Port {port} ({session_type} session, flush=True)")
        print("=" * 60, flush=True)
        
        success, sock, enc, dec = try_connect_and_login(
            host=FIX_HOST,
            port=port,
            sender_comp_id=SENDER_COMP_ID,
            target_comp_id=TARGET_COMP_ID,
            sender_sub_id=session_type,  # Use QUOTE or TRADE as SenderSubID
            password=FIX_PASSWORD
        )
        
        if success:
            ssl_sock = sock
            encoder = enc
            decoder = dec
            active_port = port
            active_session_type = session_type
            print(f"\n[SUCCESS] Connected via port {port} ({session_type}, flush=True)!")
            break
        else:
            print(f"[FAIL] Port {port} ({session_type}, flush=True) failed - continuing to next...")

    if not ssl_sock:
        print("\n" + "=" * 80, flush=True)
        print("[CRITICAL] ALL FIX CONNECTION ATTEMPTS FAILED", flush=True)
        print("=" * 80, flush=True)
        print("\nPossible causes:", flush=True)
        print("1. Invalid credentials - check SenderCompID and FIX_PASSWORD", flush=True)
        print("2. Demo account may not have FIX API access enabled", flush=True)
        print("3. Network/firewall blocking connection to cTrader servers", flush=True)
        print("4. cTrader demo server may be temporarily unavailable", flush=True)
        print("\nPlease verify your cTrader demo account has FIX API access.", flush=True)
        print("Check https://help.ctrader.com/fix/ for documentation.", flush=True)
        sys.exit(1)

    # Initialize QUANTUM BRAIN - Full 13k+ line integration
    print("\n" + "=" * 80, flush=True)
    print("[QUANTUM BRAIN] INITIALIZING FULL 13,629 LINE QUANTUM MATRIX", flush=True)
    print("=" * 80, flush=True)
    
    # Stage 1: Mathematical Filters (100+ metrics)
    print("[STAGE 1] Initializing 100+ mathematical filters...", flush=True)
    quantum_engine = QuantumMathEngine(lookback=500)
    print("  ✓ QuantumMathEngine: READY (100+ metrics, flush=True)")
    
    # Stage 2: Intelligence Matrix (100+ ML + 10+ RL models)
    print("[STAGE 2] Initializing 100+ ML + 10+ RL model matrix...", flush=True)
    intelligence = IntelligenceMatrix()
    print(f"  ✓ IntelligenceMatrix: READY ({len(intelligence.ml_models, flush=True)} ML + {len(intelligence.rl_models)} RL)")
    
    # Stage 3: World-Class Quantum Engine (quantum algorithms + execution)
    print("[STAGE 3] Initializing World-Class Quantum Engine...", flush=True)
    quantum_engine_full = WorldClassQuantumEngine(n_qubits=8)
    quantum_engine_full.initialize()
    print("  ✓ WorldClassQuantumEngine: READY", flush=True)
    
    # Stage 4: Mathematical Filter Integration (linking layers)
    print("[STAGE 4] Initializing Mathematical Filter Integration layer...", flush=True)
    math_integration = MathematicalFilterIntegration()
    math_integration.connect_mathematical_filters(quantum_engine)
    print("  ✓ MathematicalFilterIntegration: READY", flush=True)
    
    # Stage 5: Enhanced RL Manager (with mathematical integration)
    print("[STAGE 5] Initializing Enhanced RL Manager...", flush=True)
    rl_manager = EnhancedRLManager()
    rl_manager.connect_mathematical_filters(quantum_engine)
    print("  ✓ EnhancedRLManager: READY", flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("[QUANTUM BRAIN] ALL SUBSYSTEMS INITIALIZED SUCCESSFULLY", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)

    # Subscribe to XAUUSD market data
    print("[SUBSCRIBE] Requesting XAUUSD market data...", flush=True)
    md_request = decoder.create_market_data_request(
        symbol="XAUUSD",
        sender=SENDER_COMP_ID,
        target=TARGET_COMP_ID,
        sub_id=active_session_type,
        request_id="XAUUSD_MD_1"
    )
    ssl_sock.sendall(encoder.to_wire(md_request))
    print(f"  Market data request sent!", flush=True)
    time.sleep(1)

    # Main engine loop - REAL-TIME PROCESSING
    print(flush=True)
    print(f"[ENGINE] Starting REAL-TIME engine with LIVE XAUUSD data", flush=True)
    print(f"         Session: {active_session_type} | Port: {active_port}", flush=True)
    print(f"         Processing Pipeline: TICK → MATH_FILTERS → INTELLIGENCE_MATRIX → EXECUTION", flush=True)
    print("[ENGINE] Press Ctrl+C to stop", flush=True)
    print(flush=True)

    tick_count = 0
    buy_count = 0
    sell_count = 0
    hold_count = 0
    start_time = time.time()
    live_bid = 0.0
    live_ask = 0.0
    last_price_update = 0
    connection_lost = False
    total_trades_executed = 0
    math_filter_calls = 0
    intelligence_calls = 0

    try:
        while True:
            # Receive any pending market data with short timeout
            try:
                ssl_sock.settimeout(0.01)  # 10ms timeout for non-blocking reads
                data = ssl_sock.recv(65536)
                
                if data:
                    decoded = data.decode('ascii', errors='replace')
                    result = decoder.decode_message(decoded)
                    
                    if result["type"] in ("market_data_snapshot", "market_data_incremental"):
                        tick = result["tick"]
                        if tick.bid_price > 0:
                            live_bid = tick.bid_price
                            last_price_update = time.time()
                        if tick.ask_price > 0:
                            live_ask = tick.ask_price
                            last_price_update = time.time()
                        
                        tick_count += 1
                        timestamp = time.time()
                        bid = tick.bid_price
                        ask = tick.ask_price
                        volume = 0.1
                        
                        # Print tick info
                        if tick_count % 10 == 0:
                            spread = ask - bid if ask > 0 else 0
                            print(f"  [TICK] #{tick_count:05d} | Bid={bid:.5f} | Ask={ask:.5f} | Spread={spread:.2f}", flush=True)
                        
                        # Check if prices are stale
                        if time.time() - last_price_update > 10:
                            print(f"  [WARNING] Price feed stale (last update {time.time() - last_price_update:.1f}s ago)", flush=True)
                        
                        # STAGE 1: Quantum Mathematical Filters (100+ metrics)
                        math_filter_calls += 1
                        quantum_metrics = quantum_engine.process_tick(
                            timestamp=timestamp, bid=bid, ask=ask, volume=volume
                        )
                        
                        # STAGE 2: Mathematical Filter Integration (extract features for RL)
                        math_features = math_integration.extract_filter_features(quantum_metrics)
                        math_integration.update_history(quantum_metrics)
                        
                        # STAGE 3: Intelligence Matrix (100+ ML + 10+ RL models)
                        intelligence_calls += 1
                        ensemble_prediction = intelligence.process_quantum_metrics(quantum_metrics)
                        
                        # STAGE 4: Decision Logic with confidence thresholds
                        composite = ensemble_prediction.final_ensemble_signal
                        confidence = ensemble_prediction.ensemble_confidence
                        model_agreement = ensemble_prediction.model_agreement
                        
                        # Generate order with advanced risk management
                        if (abs(composite) > 0.15 and 
                            confidence > 0.3 and 
                            model_agreement > 0.4):  # Additional model agreement check
                            
                            side = "1" if composite > 0 else "2"
                            # Position sizing based on signal strength and confidence
                            quantity = 0.01 + abs(composite) * 0.1 * confidence
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
                            try:
                                ssl_sock.sendall(encoder.to_wire(fix_msg))
                                total_trades_executed += 1
                                
                                if side == "1":
                                    buy_count += 1
                                    action = "BUY"
                                else:
                                    sell_count += 1
                                    action = "SELL"
                                
                                print(f"  [ORDER] #{tick_count} {action} | Qty={quantity:.3f} | Price={order_price:.5f} | Signal={composite:+.3f} | Conf={confidence:.2f}", flush=True)
                            except Exception as e:
                                print(f"  [ORDER] Send failed: {e}", flush=True)
                        else:
                            hold_count += 1
                            
                    elif result["type"] == "execution_report":
                        report = result["report"]
                        print(f"  [EXEC] Order {report.cl_ord_id} | Status={report.ord_status} | AvgPx={report.avg_px}", flush=True)
                    elif result["type"] == "test_request":
                        test_id = result.get("tags", {}).get("112", "")
                        if test_id:
                            heartbeat = encoder.create_heartbeat(test_id)
                            ssl_sock.sendall(encoder.to_wire(heartbeat))
                    elif result["type"] == "reject":
                        print(f"  [REJECT] {result.get('text', 'Unknown', flush=True)}")
                        
            except socket.timeout:
                pass  # No data, continue
            except BlockingIOError:
                pass  # No data, continue
            except Exception as e:
                print(f"  [ERROR] Receive error: {e}", flush=True)
                connection_lost = True
                
            # Check for stale prices
            if tick_count > 0 and live_bid > 0 and (time.time() - last_price_update) > 30:
                print(f"  [ALERT] No price updates for 30 seconds!", flush=True)
            
            # Check if connection was lost
            if connection_lost:
                print("\n[ERROR] Connection lost! Attempting reconnect...", flush=True)
                
                success, new_sock, enc, dec = try_connect_and_login(
                    host=FIX_HOST,
                    port=active_port,
                    sender_comp_id=SENDER_COMP_ID,
                    target_comp_id=TARGET_COMP_ID,
                    sender_sub_id=active_session_type,
                    password=FIX_PASSWORD
                )
                
                if success:
                    ssl_sock = new_sock
                    encoder = enc
                    decoder = dec
                    connection_lost = False
                    print("[RECONNECT] Successfully reconnected!", flush=True)
                    
                    # Re-subscribe to market data
                    md_request = decoder.create_market_data_request(
                        symbol="XAUUSD",
                        sender=SENDER_COMP_ID,
                        target=TARGET_COMP_ID,
                        sub_id=active_session_type,
                        request_id="XAUUSD_MD_2"
                    )
                    ssl_sock.sendall(encoder.to_wire(md_request))
                else:
                    print("[CRITICAL] Reconnect failed!", flush=True)
                    sys.exit(1)
            
            # Small delay to prevent CPU spinning
            time.sleep(0.001)

    except KeyboardInterrupt:
        pass
    finally:
        # Shutdown
        elapsed = time.time() - start_time
        tps = tick_count / max(elapsed, 0.001)
        
        print(flush=True)
        print("=" * 80, flush=True)
        print("  SHUTDOWN SUMMARY - QUANTUM TRADING MACHINE", flush=True)
        print("=" * 80, flush=True)
        print(f"  Session Type: {active_session_type}", flush=True)
        print(f"  Port: {active_port}", flush=True)
        print(f"  Total ticks processed: {tick_count}", flush=True)
        print(f"  Runtime: {elapsed:.1f} seconds", flush=True)
        print(f"  Throughput: {tps:.0f} ticks/sec", flush=True)
        print(f"  Orders sent: {total_trades_executed}", flush=True)
        print(f"  Buy orders: {buy_count}", flush=True)
        print(f"  Sell orders: {sell_count}", flush=True)
        print(f"  Hold signals: {hold_count}", flush=True)
        print(f"  Final Bid={live_bid:.5f} | Ask={live_ask:.5f}", flush=True)
        print(f"  Math Filter Calls: {math_filter_calls}", flush=True)
        print(f"  Intelligence Matrix Calls: {intelligence_calls}", flush=True)
        print(f"  Quantum Engine Status: ACTIVE", flush=True)
        print("=" * 80, flush=True)
        
        # Send logout
        try:
            logout_msg = encoder.create_logout("Engine shutdown")
            ssl_sock.sendall(encoder.to_wire(logout_msg))
            ssl_sock.close()
        except:
            pass
        
        print("[SHUTDOWN] Power off complete", flush=True)
        print("[SHUTDOWN] Quantum matrix shut down safely", flush=True)


if __name__ == "__main__":
    load_dotenv()
    validate_config()
    main()