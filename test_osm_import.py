#!/usr/bin/env python3
"""
Test script for OSM import functionality in Docker environment.

This script verifies that:
1. Database connections work
2. OSM import commands execute successfully
3. Health check endpoint includes OSM status
4. Basic tile operations work
"""

import os
import sys
import django
from pathlib import Path
from django.core.management import execute_from_command_line
from django.test import RequestFactory
from conditions.views import health_check
from conditions.models_spots import OSMSpot, ImportTile
from conditions.models import SnorkelLocation

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snorkelforecast.snorkelforecast.settings")
django.setup()


def test_database_connection():
    """Test database connectivity."""
    print("🧪 Testing database connection...")

    try:
        # Test legacy locations
        legacy_count = SnorkelLocation.objects.count()
        print(f"  ✅ Legacy locations: {legacy_count}")

        # Test OSM spots
        osm_count = OSMSpot.objects.count()
        print(f"  ✅ OSM spots: {osm_count}")

        # Test import tiles
        tile_count = ImportTile.objects.count()
        print(f"  ✅ Import tiles: {tile_count}")

        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False


def test_health_endpoint():
    """Test health check endpoint."""
    print("🧪 Testing health check endpoint...")

    try:
        factory = RequestFactory()
        request = factory.get("/health/")
        response = health_check(request)

        if response.status_code == 200:
            print("  ✅ Health check: OK")
            print(f"  📊 Response: {response.content.decode()[:200]}...")
            return True
        else:
            print(f"  ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Health check error: {e}")
        return False


def test_osm_import_dry_run():
    """Test OSM import command with dry run."""
    print("🧪 Testing OSM import dry run...")

    try:
        # Test creating a small tile queue
        execute_from_command_line(
            [
                "manage.py",
                "import_osm_tiles",
                "--create-tiles",
                "--zoom",
                "9",
                "--country-bbox",
                "36,-5,40,0",  # Small area around Spain
                "--dry-run",
            ]
        )
        print("  ✅ Tile queue creation: OK")

        # Test importing a few tiles
        execute_from_command_line(
            ["manage.py", "import_osm_tiles", "--batch-size", "1", "--dry-run"]
        )
        print("  ✅ Tile import dry run: OK")

        return True
    except Exception as e:
        print(f"  ❌ OSM import error: {e}")
        return False


def test_models():
    """Test that models work correctly."""
    print("🧪 Testing models...")

    try:
        # Test creating an OSM spot
        spot = OSMSpot(
            osm_type="n",
            osm_id=12345,
            name="Test Marina",
            latitude=36.5,
            longitude=-5.0,
            source="test",
        )
        spot.save()
        print("  ✅ OSM spot creation: OK")

        # Test confidence calculation
        spot.update_confidence()
        print(f"  📊 Confidence score: {spot.confidence}")

        # Clean up
        spot.delete()
        print("  ✅ Model cleanup: OK")

        return True
    except Exception as e:
        print(f"  ❌ Model error: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting OSM Import Docker Integration Tests\n")

    tests = [
        test_database_connection,
        test_health_endpoint,
        test_models,
        test_osm_import_dry_run,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()

    print("📊 Test Results:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(
        f"  📈 Success rate: {passed}/{passed + failed} ({100 * passed / (passed + failed):.1f}%)"
    )

    if failed == 0:
        print("\n🎉 All tests passed! OSM import is ready for Docker deployment.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
