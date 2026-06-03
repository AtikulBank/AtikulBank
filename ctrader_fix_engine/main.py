#!/usr/bin/env python3
"""
cTrader FIX 4.4 High-Frequency Trading Engine
Main entry point - Lean Architecture
"""

import sys
import signal
from pathlib import Path

from .config.loader import load_config, FixConfig
from .engine.session import FixSession, SessionState


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n[SHUTDOWN] Received shutdown signal...")
    sys.exit(0)


def main():
    """Main entry point"""
    print("=" * 70)
    print("  cTrader FIX 4.4 High-Frequency Trading Engine")
    print("  Lean Architecture - Pure Cython + Raw C-Sockets")
    print("=" * 70)
    print()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load configuration
    print("[CONFIG] Loading configuration from .env...")
    try:
        config = load_config()
        print(f"[CONFIG] Host: {config.host}:{config.port}")
        print(f"[CONFIG] Sender: {config.sender_comp_id}")
        print(f"[CONFIG] Target: {config.target_comp_id}")
        print(f"[CONFIG] Heartbeat: {config.heartbeat_interval}s")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to load configuration: {e}")
        print()
        print("Please create a .env file with the following variables:")
        print("  FIX_HOST=your.fix.server.com")
        print("  FIX_PORT=9876")
        print("  SENDER_COMP_ID=YOUR_SENDER_ID")
        print("  TARGET_COMP_ID=YOUR_TARGET_ID")
        print("  SENDER_SUB_ID=YOUR_SUB_ID")
        print("  FIX_PASSWORD=YOUR_PASSWORD")
        sys.exit(1)
    
    # Create session
    print("[SESSION] Creating FIX session...")
    session = FixSession(config)
    
    # Set up message handlers
    def on_message(message):
        """Handle incoming messages"""
        print(f"[MSG] Received: {message.msg_type}")
    
    def on_execution_report(report):
        """Handle execution reports"""
        print(f"[EXEC] Order: {report.get(11)} Status: {report.get(39)}")
    
    def on_disconnect():
        """Handle disconnection"""
        print("[DISCONNECT] Connection lost")
    
    session.set_message_handler(on_message)
    session.set_execution_report_handler(on_execution_report)
    session.set_disconnect_handler(on_disconnect)
    
    # Connect
    print("[CONNECT] Connecting to FIX server...")
    try:
        session.connect()
        print("[CONNECT] Connected successfully")
        print()
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)
    
    # Logon
    print("[LOGON] Sending logon message...")
    try:
        logon_msg = session.logon(config.password)
        print("[LOGON] Logon sent, waiting for response...")
        print()
    except Exception as e:
        print(f"[ERROR] Logon failed: {e}")
        session.disconnect()
        sys.exit(1)
    
    # Main loop
    print("[ENGINE] Starting main engine loop...")
    print("[ENGINE] Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            # Receive messages
            message = session.receive_message(timeout=1.0)
            
            if message:
                # Process message
                pass
            
            # Check heartbeat timeout
            if session.check_heartbeat_timeout():
                print("[HEARTBEAT] Timeout detected, sending test request...")
                session.send_test_request()
            
            # Check session state
            if session.state == SessionState.ERROR:
                print("[ERROR] Session error, attempting reconnect...")
                session.disconnect()
                import time
                time.sleep(config.reconnect_interval)
                session.connect()
                session.logon(config.password)
            
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Shutting down...")
    except Exception as e:
        print(f"\n[ERROR] Engine error: {e}")
    finally:
        session.disconnect()
        print("[SHUTDOWN] Session closed")
        print("=" * 70)


if __name__ == "__main__":
    main()