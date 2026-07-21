"""
Manual hardware validation script for ADB device detection.

Requirements:
  - A physical Android device with USB debugging enabled
  - USB cable connected to this computer
  - Authorised (RSA fingerprint accepted on device)

Usage:
  python scripts/test_adb_device.py [--adb-path PATH]

If --adb-path is not provided, auto-detection is attempted.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from wft.application.services.adb_service import AdbService, AdbState


def main() -> None:
    parser = argparse.ArgumentParser(description="Test ADB device detection")
    parser.add_argument("--adb-path", help="Path to adb.exe (optional, auto-detect if omitted)")
    args = parser.parse_args()

    service = AdbService(configured_path=args.adb_path)

    print("=== ADB Detection Test ===\n")

    adb_path = service.find_adb()
    if adb_path:
        print(f"[OK] ADB binary found: {adb_path}")
        version = service.server_version()
        if version:
            print(f"[OK] ADB version: {version.split(chr(10))[0]}")
    else:
        print("[FAIL] ADB binary not found")
        print("  Please install Android SDK platform-tools or specify --adb-path")
        sys.exit(1)

    print("\n--- Server Status ---")
    state = service.get_state()
    if state == AdbState.CONNECTED:
        print("[OK] ADB server is running")
    else:
        print(f"[..] Starting ADB server (state was {state.value})...")
        try:
            service.start_server()
            print("[OK] ADB server started")
        except Exception as exc:
            print(f"[FAIL] Could not start ADB server: {exc}")
            sys.exit(1)

    print("\n--- Device Scan ---")
    try:
        devices = service.list_devices(timeout=15)
    except Exception as exc:
        print(f"[FAIL] Device scan failed: {exc}")
        sys.exit(1)

    if not devices:
        print("[FAIL] No devices detected")
        print("\nTroubleshooting checklist:")
        print("  1. USB cable firmly connected?")
        print("  2. USB debugging enabled in Developer Options?")
        print("  3. RSA fingerprint accepted on device?")
        print("  4. Try 'adb kill-server' then 'adb start-server'")
        print("  5. Try a different USB port or cable")
        print("  6. Check USB connection mode (MTP / File Transfer)")
        sys.exit(1)

    print(f"[OK] {len(devices)} device(s) detected:\n")
    for dev in devices:
        print(f"  Serial:       {dev.serial}")
        print(f"  State:        {dev.state.value}")
        print(f"  Transport ID: {dev.transport_id or 'N/A'}")
        print()

        if dev.state == AdbState.CONNECTED:
            print("  --- Fetching Device Details ---")
            try:
                details = service.get_device_details(dev.serial, timeout=15)
                print(f"  Manufacturer: {details.manufacturer or 'Unknown'}")
                print(f"  Model:        {details.model or 'Unknown'}")
                print(f"  Product:      {details.product or 'Unknown'}")
                print(f"  Android:      {details.android_version or 'Unknown'}")
                print(f"  SDK:          {details.sdk_version or 'Unknown'}")
                print(f"  Connection:   {details.connection_type}")
            except Exception as exc:
                print(f"  [FAIL] Could not fetch details: {exc}")
        elif dev.state == AdbState.UNAUTHORIZED:
            print("  !!! Device is UNAUTHORIZED !!!")
            print("  Accept the RSA fingerprint prompt on the device.")
        elif dev.state == AdbState.OFFLINE:
            print("  !!! Device is OFFLINE !!!")
            print("  Check USB connection and unlock the device.")

    print("\n=== Test Complete ===")
    if any(d.state == AdbState.CONNECTED for d in devices):
        print("RESULT: PASS - Connected device detected")
    else:
        print("RESULT: PARTIAL - Device(s) found but not in connected state")
        sys.exit(1)


if __name__ == "__main__":
    main()
