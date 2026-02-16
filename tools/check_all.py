#!/usr/bin/env python3
"""
Master Connectivity Check Tool
Runs all connectivity checks in sequence
Usage: python tools/check_all.py
"""

import sys
import subprocess
from pathlib import Path


def run_check(script_name: str, description: str) -> bool:
    """Run a single check script and return success status."""
    
    print("\n" + "=" * 60)
    print(f"🔍 {description}")
    print("=" * 60)
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"\n⏱️  {description} timed out")
        return False
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False


def main():
    """Run all connectivity checks."""
    
    print("\n" + "🚀" * 30)
    print("  TestStrategy Agent — Master Connectivity Check")
    print("🚀" * 30)
    
    checks = [
        ("check_jira.py", "JIRA Connection"),
        ("check_groq.py", "Groq LLM Connection"),
        ("check_ollama.py", "Ollama LLM Connection"),
        ("check_template.py", "Template PDF"),
    ]
    
    results = {}
    
    for script, description in checks:
        results[description] = run_check(script, description)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    for description, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} — {description}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! Ready for Phase 3 (Architect).")
        print("=" * 60)
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("=" * 60)
        print("\nNote: At least one of Groq or Ollama must pass for LLM functionality.")
        print("      JIRA and Template checks must pass for the app to work.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
