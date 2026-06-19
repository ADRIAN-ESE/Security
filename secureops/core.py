"""
SecureOps Dashboard — Core Module

Encryption, threat detection, persistent encrypted storage, and the
in-memory dashboard engine. This is the same engine from the original
script, with one fix applied:

  FIX: SecureLogStore.retrieve_events() now actually decrypts stored
  records (previously it just returned the raw ciphertext blobs and
  claimed to decrypt them). A new decrypt_event() method re-derives the
  per-record key from the store's in-memory master key + timestamp,
  exactly as store_event() did when writing the record, and runs it
  through SecureCipher.decrypt_record() (which also verifies the
  integrity checksum before decrypting).
"""

import time
import random
import datetime
import threading
import json
import hashlib
import os
import math
from collections import deque, Counter
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Callable
from enum import Enum
import secrets


# ============================================================================
# ENCRYPTION MODULE
# ============================================================================

class CipherType(Enum):
    CAESAR = "caesar"
    VIGENERE = "vigenere"
    XOR = "xor"


@dataclass
class EncryptedRecord:
    """Immutable encrypted log record with integrity verification."""
    ciphertext: str
    cipher_type: str
    key_hash: str  # SHA-256 of key (for verification, not the key itself)
    timestamp: str
    nonce: str  # Prevent replay attacks
    checksum: str  # Verify ciphertext integrity

    def verify(self) -> bool:
        """Verify record integrity."""
        computed = hashlib.sha256(
            f"{self.ciphertext}{self.nonce}".encode()
        ).hexdigest()[:16]
        return computed == self.checksum


class SecurityError(Exception):
    """Custom exception for security violations."""
    pass


class SecureCipher:
    """
    Cipher engine with constant-time character shifting, key derivation
    and hashing, secure random nonces, and tamper-evident records.
    """

    def __init__(self):
        self._operation_count = 0
        self._lock = threading.Lock()

    def _secure_shift(self, char: str, shift: int, decrypt: bool = False) -> str:
        """Constant-time character shift to prevent timing analysis."""
        if not char.isalpha():
            return char

        ascii_offset = 65 if char.isupper() else 97
        effective_shift = (-shift) if decrypt else shift
        new_pos = (ord(char) - ascii_offset + effective_shift) % 26
        return chr(new_pos + ascii_offset)

    def caesar(self, text: str, shift: int, decrypt: bool = False) -> str:
        if not isinstance(shift, int):
            raise ValueError("Shift must be an integer")

        shift = shift % 26
        result = [self._secure_shift(c, shift, decrypt) for c in text]

        with self._lock:
            self._operation_count += 1

        return "".join(result)

    def vigenere(self, text: str, key: str, decrypt: bool = False) -> str:
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")

        if not all(c.isalpha() for c in key):
            raise ValueError("Key must contain only alphabetic characters")

        key = key.lower()
        result = []
        key_index = 0

        for char in text:
            if char.isalpha():
                shift = ord(key[key_index % len(key)]) - 97
                result.append(self._secure_shift(char, shift, decrypt))
                key_index += 1
            else:
                result.append(char)

        with self._lock:
            self._operation_count += 1

        return "".join(result)

    def xor_cipher(self, text: str, key: str, decrypt: bool = False) -> str:
        if not key:
            raise ValueError("Key cannot be empty")

        if len(key) < len(text):
            stretched_key = ""
            while len(stretched_key) < len(text):
                stretched_key += key
            key = stretched_key[:len(text)]

        result = []
        for i, char in enumerate(text):
            xor_val = ord(char) ^ ord(key[i])
            result.append(chr(xor_val))

        with self._lock:
            self._operation_count += 1

        return "".join(result)

    def encrypt_record(self, plaintext: str, cipher_type: CipherType,
                        key: str, shift: Optional[int] = None,
                        timestamp: Optional[str] = None) -> EncryptedRecord:
        nonce = secrets.token_hex(8)
        timestamp = timestamp or datetime.datetime.now().isoformat()

        if cipher_type == CipherType.CAESAR:
            if shift is None:
                raise ValueError("Caesar cipher requires shift parameter")
            ciphertext = self.caesar(plaintext, shift, decrypt=False)
            key_repr = str(shift)
        elif cipher_type == CipherType.VIGENERE:
            ciphertext = self.vigenere(plaintext, key, decrypt=False)
            key_repr = key
        else:  # XOR
            ciphertext = self.xor_cipher(plaintext, key, decrypt=False)
            key_repr = key

        key_hash = hashlib.sha256(key_repr.encode()).hexdigest()[:16]
        checksum = hashlib.sha256(
            f"{ciphertext}{nonce}".encode()
        ).hexdigest()[:16]

        return EncryptedRecord(
            ciphertext=ciphertext,
            cipher_type=cipher_type.value,
            key_hash=key_hash,
            timestamp=timestamp,
            nonce=nonce,
            checksum=checksum
        )

    def decrypt_record(self, record: EncryptedRecord, key: str,
                        shift: Optional[int] = None) -> str:
        """Decrypt a record after verifying integrity."""
        if not record.verify():
            raise SecurityError("Record integrity check failed! Possible tampering.")

        cipher_type = CipherType(record.cipher_type)

        if cipher_type == CipherType.CAESAR:
            return self.caesar(record.ciphertext, shift, decrypt=True)
        elif cipher_type == CipherType.VIGENERE:
            return self.vigenere(record.ciphertext, key, decrypt=True)
        else:
            return self.xor_cipher(record.ciphertext, key, decrypt=True)

    @property
    def operations_performed(self) -> int:
        with self._lock:
            return self._operation_count


# ============================================================================
# SECURITY EVENT ENGINE
# ============================================================================

@dataclass
class SecurityEvent:
    """Structured security event with severity classification."""
    timestamp: datetime.datetime
    event_type: str
    severity: str
    source: str
    details: str
    event_id: str
    encrypted: bool = False

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


class ThreatDetector:
    """
    Threat detection using cipher analysis techniques: frequency analysis
    for Caesar-encoded payloads, Kasiski-style repeat detection, and
    Shannon entropy for randomness.
    """

    ENGLISH_FREQ = {
        'e': 12.7, 't': 9.1, 'a': 8.2, 'o': 7.5, 'i': 7.0,
        'n': 6.7, 's': 6.3, 'h': 6.1, 'r': 6.0, 'd': 4.3,
        'l': 4.0, 'c': 2.8, 'u': 2.8, 'm': 2.4, 'w': 2.4,
        'f': 2.2, 'g': 2.0, 'y': 2.0, 'p': 1.9, 'b': 1.5
    }

    def __init__(self):
        self.cipher_engine = SecureCipher()
        self._patterns = deque(maxlen=1000)

    def calculate_entropy(self, text: str) -> float:
        """Shannon entropy — high entropy suggests encryption/compression."""
        if not text:
            return 0.0

        freq = Counter(text.lower())
        length = len(text)
        entropy = -sum(
            (count / length) * math.log2(count / length)
            for count in freq.values()
        )
        return entropy

    def detect_caesar_payload(self, text: str) -> Optional[int]:
        """Detect Caesar shift via chi-squared statistic against English freq."""
        text = ''.join(c for c in text.lower() if c.isalpha())
        if len(text) < 10:
            return None

        best_shift = None
        best_score = float('inf')

        for shift in range(26):
            decrypted = self.cipher_engine.caesar(text, shift, decrypt=True)
            score = self._chi_squared(decrypted)
            if score < best_score:
                best_score = score
                best_shift = shift

        if best_score < 150:
            return best_shift
        return None

    def _chi_squared(self, text: str) -> float:
        text = ''.join(c for c in text.lower() if c.isalpha())
        if not text:
            return float('inf')

        length = len(text)
        score = 0.0

        for char, expected_freq in self.ENGLISH_FREQ.items():
            observed = text.count(char)
            expected = (expected_freq / 100) * length
            if expected > 0:
                score += ((observed - expected) ** 2) / expected

        return score

    def analyze_event(self, event: SecurityEvent) -> Dict:
        details = event.details
        entropy = self.calculate_entropy(details)
        caesar_shift = self.detect_caesar_payload(details)

        threat_level = "Low"
        indicators = []

        if entropy > 4.5:
            indicators.append("High entropy — possible encrypted payload")
            threat_level = "Medium"

        if caesar_shift is not None:
            indicators.append(f"Caesar cipher detected (shift={caesar_shift})")
            threat_level = "High"

        if event.severity in ["High", "Critical"]:
            threat_level = max(threat_level, event.severity, key=lambda x:
                {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}.get(x, 0))

        if len(details) > 20:
            repeating = self._find_repeating_sequences(details)
            if repeating:
                indicators.append(f"Repeating sequences detected: {repeating}")

        self._patterns.append({
            'event_id': event.event_id,
            'threat_level': threat_level,
            'indicators': indicators
        })

        return {
            'event_id': event.event_id,
            'threat_level': threat_level,
            'entropy': round(entropy, 2),
            'indicators': indicators,
            'caesar_shift_detected': caesar_shift,
            'timestamp': datetime.datetime.now().isoformat()
        }

    def _find_repeating_sequences(self, text: str, min_len: int = 3) -> List[str]:
        sequences = {}
        text = ''.join(c for c in text if c.isalnum()).lower()

        for i in range(len(text) - min_len + 1):
            seq = text[i:i + min_len]
            sequences.setdefault(seq, []).append(i)

        repeating = []
        for seq, positions in sequences.items():
            if len(positions) > 1:
                distances = [positions[j + 1] - positions[j]
                             for j in range(len(positions) - 1)]
                repeating.append(f"{seq} at distances {distances}")

        return repeating[:3]


# ============================================================================
# PERSISTENCE LAYER
# ============================================================================

class SecureLogStore:
    """
    Encrypted log storage with integrity verification AND working
    decryption on retrieval (see decrypt_event below).
    """

    def __init__(self, storage_path: str = "secure_logs.jsonl"):
        self.storage_path = storage_path
        self.cipher = SecureCipher()
        self._buffer = deque(maxlen=50)
        self._lock = threading.Lock()
        self._master_key = os.urandom(32).hex()  # In production, use a KMS

        if not os.path.exists(storage_path):
            open(storage_path, 'w').close()

    def _derive_key(self, timestamp_iso: str, cipher_type: CipherType):
        """
        Re-derive the per-record key the same way store_event does.

        FIX: the original derivation used a raw hex digest as the key for
        every cipher type, including Vigenère — but vigenere() requires an
        alphabetic-only key, so every Vigenère-encrypted store (the
        default) raised ValueError and silently dropped every event.
        Now each cipher type gets a key in the alphabet it actually needs.
        """
        key_seed = f"{self._master_key}{timestamp_iso}"
        digest = hashlib.sha256(key_seed.encode()).hexdigest()

        if cipher_type == CipherType.VIGENERE:
            key = ''.join(chr(97 + (int(d, 16) % 26)) for d in digest[:16])
        else:
            key = digest[:16]

        shift = int(digest, 16) % 26
        return key, shift

    def store_event(self, event: SecurityEvent,
                     cipher_type: CipherType = CipherType.VIGENERE) -> EncryptedRecord:
        """Encrypt and store a security event."""
        plaintext = json.dumps(event.to_dict())
        timestamp_iso = event.timestamp.isoformat()
        key, shift = self._derive_key(timestamp_iso, cipher_type)

        if cipher_type == CipherType.CAESAR:
            record = self.cipher.encrypt_record(plaintext, cipher_type, key, shift, timestamp_iso)
        else:
            record = self.cipher.encrypt_record(plaintext, cipher_type, key, timestamp=timestamp_iso)

        with self._lock:
            self._buffer.append(record)
            if len(self._buffer) >= 10:
                self._flush()

        return record

    def _flush(self):
        """Write buffered records to disk."""
        with open(self.storage_path, 'a') as f:
            while self._buffer:
                record = self._buffer.popleft()
                f.write(json.dumps(asdict(record)) + '\n')

    def decrypt_event(self, record_dict: Dict) -> Dict:
        """
        Actually decrypt a stored record back to its original event dict.
        Re-derives the key (and shift, for Caesar) from the in-memory
        master key + the record's own timestamp — the same derivation
        used in store_event — then verifies integrity and decrypts.
        """
        record = EncryptedRecord(**record_dict)
        cipher_type = CipherType(record.cipher_type)
        key, shift = self._derive_key(record.timestamp, cipher_type)

        if cipher_type == CipherType.CAESAR:
            plaintext = self.cipher.decrypt_record(record, key, shift)
        else:
            plaintext = self.cipher.decrypt_record(record, key)

        return json.loads(plaintext)

    def retrieve_events(self, limit: int = 100, decrypt: bool = True) -> List[Dict]:
        """
        Return recent events. With decrypt=True (default) each record is
        decrypted back into its original event dict. With decrypt=False
        the raw encrypted record dicts are returned instead.
        """
        events = []

        if not os.path.exists(self.storage_path):
            return events

        with open(self.storage_path, 'r') as f:
            lines = f.readlines()[-limit:]

        for line in lines:
            try:
                data = json.loads(line.strip())
                events.append(self.decrypt_event(data) if decrypt else data)
            except Exception:
                continue

        return events

    def close(self):
        """Ensure all data is flushed."""
        with self._lock:
            self._flush()


# ============================================================================
# REAL-TIME DASHBOARD ENGINE
# ============================================================================

class SecureOpsDashboard:
    """
    Unified dashboard: live security event monitoring, real-time
    encryption operations, threat detection/alerting, persistent
    encrypted storage.
    """

    def __init__(self):
        self.events = deque(maxlen=100)
        self.encrypted_store = SecureLogStore()
        self.threat_detector = ThreatDetector()
        self.cipher = SecureCipher()

        self.alert_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
        self.source_counts = {}
        self.threat_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}

        self.event_templates = [
            ("Failed SSH login attempt", "Suspicious Login", "Medium"),
            ("Port scan detected from external IP", "Intrusion Attempt", "High"),
            ("Signature match: Trojan.Generic", "Malware Detected", "Critical"),
            ("Outbound connection to known C2 server", "Anomaly Detected", "Critical"),
            ("Firewall rule triggered: Blocked inbound", "Firewall Blocked", "Low"),
            ("Multiple failed 2FA attempts", "Suspicious Login", "High"),
            ("Unusual process execution: powershell -enc", "Malware Detected", "High"),
            ("Database query anomaly: SELECT * FROM users", "Anomaly Detected", "Medium"),
            ("Certificate validation failure", "Intrusion Attempt", "Medium"),
            ("Memory allocation spike in web server", "Anomaly Detected", "Low"),
        ]

        self._running = False
        self._lock = threading.Lock()
        self._subscribers: List[Callable] = []
        self._producer_thread = None

    def generate_realistic_event(self) -> SecurityEvent:
        """Generate a security event with realistic patterns."""
        template = random.choice(self.event_templates)
        description, event_type, severity = template

        if random.random() < 0.1:  # 10% chance: embed a cipher payload for the demo
            secret_msg = "URGENT: Exfiltrate data at midnight"
            shift = random.randint(1, 25)
            encrypted_payload = self.cipher.caesar(secret_msg, shift)
            description += f" | Payload: {encrypted_payload}"

        source = random.choice([
            "Web-Prod-01", "DB-Primary", "Firewall-Edge",
            "Workstation-IT-42", "K8s-Cluster-A", "SIEM-Collector"
        ])

        return SecurityEvent(
            timestamp=datetime.datetime.now(),
            event_type=event_type,
            severity=severity,
            source=source,
            details=description,
            event_id=secrets.token_hex(8)
        )

    def process_event(self, event: SecurityEvent):
        """Process a single event through the pipeline."""
        threat_report = self.threat_detector.analyze_event(event)
        encrypted_record = self.encrypted_store.store_event(event)

        with self._lock:
            self.events.append(event)
            self.alert_counts[event.severity] += 1
            self.source_counts[event.source] = self.source_counts.get(event.source, 0) + 1
            self.threat_counts[threat_report['threat_level']] += 1

        for subscriber in self._subscribers:
            try:
                subscriber(event, threat_report, encrypted_record)
            except Exception:
                pass

    def subscribe(self, callback: Callable):
        """Subscribe to real-time event updates."""
        self._subscribers.append(callback)

    def start_monitoring(self):
        """Start the event generation and processing loop."""
        self._running = True

        def producer():
            while self._running:
                event = self.generate_realistic_event()
                self.process_event(event)
                time.sleep(random.uniform(0.5, 2.0))

        self._producer_thread = threading.Thread(target=producer, daemon=True)
        self._producer_thread.start()

    def stop(self):
        """Graceful shutdown."""
        self._running = False
        self.encrypted_store.close()

    def get_snapshot(self) -> Dict:
        """Get current dashboard state."""
        with self._lock:
            recent_threats = [
                self.threat_detector.analyze_event(e)
                for e in list(self.events)[-10:]
            ]

            return {
                'alert_counts': dict(self.alert_counts),
                'source_counts': dict(
                    sorted(self.source_counts.items(),
                           key=lambda x: x[1], reverse=True)[:5]
                ),
                'threat_counts': dict(self.threat_counts),
                'recent_events': [e.to_dict() for e in list(self.events)[-5:]],
                'recent_threats': recent_threats,
                'total_operations': self.cipher.operations_performed,
                'storage_size': os.path.getsize(self.encrypted_store.storage_path)
                if os.path.exists(self.encrypted_store.storage_path) else 0
            }
