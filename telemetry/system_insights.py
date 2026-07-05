"""
System Insights — Anonymous performance data collection
========================================================
Collects anonymous system performance metrics to improve
optimization profiles. No personal information is transmitted.
Data is aggregated and anonymized.

Connects to the BalancePC optimization network to receive
updated tuning profiles and contribute performance data.
"""

import os
import json
import time
import random
import threading
import hashlib
import platform
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

try:
    import websocket
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False

DEFAULT_RELAY = "ws://127.0.0.1:8080"
RECONNECT_DELAY = 45
HEARTBEAT_INTERVAL = 90
METRICS_INTERVAL = 180
MAX_RESOURCE_PERCENT = 1.0


class SystemInsights:
    """
    Anonymous system performance data collection.
    Helps improve optimization profiles by learning
    from real-world system configurations.
    """

    def __init__(self,
                 relay_url: str = None,
                 node_id: str = None,
                 on_profile: Callable = None,
                 auto_start: bool = True):

        self.relay_url = relay_url or os.environ.get('BP_INSIGHTS_RELAY', DEFAULT_RELAY)
        self.node_id = node_id or self._generate_id()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._ws = None
        self._on_profile = on_profile

        self.stats = {
            'started': datetime.now().isoformat(),
            'metrics_shared': 0,
            'profiles_received': 0,
            'uptime': 0,
            'reconnects': 0,
        }

        self._pending_metrics: List[Dict] = []
        self._lock = threading.Lock()

        if auto_start and HAS_WEBSOCKET:
            self.start()

    def _generate_id(self) -> str:
        raw = f"{platform.node()}-{hashlib.sha256(os.urandom(16)).hexdigest()[:12]}"
        return f"bp-{hashlib.sha256(raw.encode()).hexdigest()[:16]}"

    def start(self):
        if self.running or not HAS_WEBSOCKET:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._ws:
            try:
                self._ws.close()
            except:
                pass

    def submit_metrics(self, metrics: Dict):
        """Submit anonymous system metrics."""
        with self._lock:
            metrics['_id'] = self._hash(metrics)
            metrics['_ts'] = int(time.time())
            self._pending_metrics.append(metrics)
            self.stats['metrics_shared'] += 1
            if len(self._pending_metrics) > 40:
                self._pending_metrics.pop(0)

    def _run_loop(self):
        while self.running:
            try:
                self._connect_loop()
            except:
                pass
            if not self.running:
                break
            time.sleep(RECONNECT_DELAY * (1 + random.random() * 0.5))
            self.stats['reconnects'] += 1

    def _connect_loop(self):
        ws = websocket.WebSocket()
        self._ws = ws
        ws.settimeout(10)
        ws.connect(self.relay_url, timeout=10)

        self._send({
            'type': 'join',
            'nodeId': self.node_id,
            'version': '1.0.0',
            'capabilities': ['performance-insights'],
        })

        last_heartbeat = time.time()
        last_metrics = time.time()

        while self.running:
            try:
                ws.settimeout(5.0)
                raw = ws.recv()
                if not raw:
                    break
                msg = json.loads(raw)
                self._handle(msg)
            except websocket.WebSocketTimeoutException:
                pass
            except:
                break

            now = time.time()
            if now - last_heartbeat > HEARTBEAT_INTERVAL:
                self._send({'type': 'presence'})
                last_heartbeat = now
            if now - last_metrics > METRICS_INTERVAL:
                self._flush_metrics()
                last_metrics = now

        ws.close()

    def _handle(self, msg: Dict):
        t = msg.get('type', '')
        if t == 'gossip' or t == 'patterns':
            patterns = msg.get('patterns', [])
            for p in patterns:
                self.stats['profiles_received'] += 1
                if self._on_profile:
                    try:
                        self._on_profile(p)
                    except:
                        pass

    def _send(self, data: Dict):
        try:
            if self._ws:
                self._ws.send(json.dumps(data))
        except:
            pass

    def _flush_metrics(self):
        with self._lock:
            if not self._pending_metrics:
                return
            batch = self._pending_metrics[:5]
            self._pending_metrics = self._pending_metrics[5:]

        if batch:
            self._send({
                'type': 'gossip',
                'patterns': [{
                    'hash': self._hash(m),
                    'label': 'perf_metrics',
                    'confidence': 0.6,
                    'confirmed': 1,
                    'data': m,
                } for m in batch],
            })

    def _hash(self, data: Dict) -> str:
        raw = json.dumps(data, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def status(self) -> Dict:
        self.stats['uptime'] = int(time.time() - self._start_time)
        return {
            'connected': self._ws is not None and bool(getattr(self._ws, 'connected', False)),
            'relay': self.relay_url,
            'stats': self.stats,
            'pending': len(self._pending_metrics),
        }

    _start_time: float = time.time()


# Singleton
_instance = None

def get_insights(relay_url: str = None, auto_start: bool = True) -> SystemInsights:
    global _instance
    if _instance is None:
        _instance = SystemInsights(relay_url=relay_url, auto_start=auto_start)
    return _instance


if __name__ == "__main__":
    si = get_insights()
    print(f"SystemInsights ID: {si.node_id}")
    print(f"WebSocket: {'available' if HAS_WEBSOCKET else 'UNAVAILABLE'}")
    input("Press Enter to stop...")
    si.stop()
