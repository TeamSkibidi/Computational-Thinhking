"""
Test Repository - Full Integration Test
Tests all CRUD operations with MySQL database
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models and repository
from do_an.models import Place, Address
from do_an.repository import PlaceRepository

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}→ {text}{RESET}")

# Test counters (global)
tests_passed = 0
tests_failed = 0

def test_result(condition, success_msg, error_msg):
    global tests_passed, tests_failed
    if condition:
        print_success(success_msg)
        tests_passed += 1
        return True
    else:
        print_error(error_msg)
        tests_failed += 1
        return False

def main():
    global tests_passed, tests_failed
    print_header("REPOSITORY FULL INTEGRATION TEST")
    
    # Check environment variables
    print_info("Checking environment variables...")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    
    if not db_host:
        print_error("DB_HOST not found in .env file!")
        print_info("Please create .env file with database configuration")
        return
    
    print_success(f"Database: {db_name} @ {db_host}")
    
    # Initialize repository
    print_info("Initializing PlaceRepository...")
    repo = PlaceRepository()
    
    if repo.use_mysql:
        print_success("Using MySQL database")
    else:
        print_success("Using in-memory storage (fallback)")
    
    # Test 1: Count initial places
    print_header("TEST 1: Count Initial Places")
    initial_count = repo.count()
    print_info(f"Initial place count: {initial_count}")
    test_result(initial_count >= 0, "Count method works", "Count method failed")
    
    # Test 2: Create and Save Place with Address
    print_header("TEST 2: Create and Save Place")
    
    address = Address(
        houseNumber="123",
        street="Nguyen Hue",
        ward="Ben Nghe",
        district="District 1",
        city="Ho Chi Minh",
        lat=10.7769,
        lng=106.7009,
        url="https://maps.google.com/test"
    )
    
    place = Place(
        name="Nhà Hàng Test ABC",
        priceVnd=250000,
        summary="Nhà hàng test cho repository",
        description="Đây là mô tả chi tiết của nhà hàng test",
        openTime="08:00",
        closeTime="22:00",
        phone="+84901234567",
        rating=4.5,
        reviewCount=100,
        popularity=500,
        imageName="test_restaurant.jpg",
        address=address
    )
    
    print_info(f"Creating place: {place.name}")
    try:
        place_id = repo.save_place(place)
        test_result(
            place_id > 0,
            f"Place saved successfully with ID: {place_id}",
            "Failed to save place"
        )
    except Exception as e:
        print_error(f"Error saving place: {e}")
        tests_failed += 1
        return
    
    # Test 3: Get Place by ID
    print_header("TEST 3: Get Place by ID")
    print_info(f"Fetching place with ID: {place_id}")
    
    found_place = repo.get_place_by_id(place_id)
    test_result(
        found_place is not None,
        f"Place found: {found_place.name if found_place else 'None'}",
        "Place not found"
    )
    
    if found_place:
        test_result(
            found_place.name == place.name,
            f"Name matches: {found_place.name}",
            "Name doesn't match"
        )
        test_result(
            found_place.rating == place.rating,
            f"Rating matches: {found_place.rating}",
            "Rating doesn't match"
        )
        test_result(
            found_place.address and found_place.address.city == "Ho Chi Minh",
            f"Address loaded: {found_place.address.city if found_place.address else 'None'}",
            "Address not loaded correctly"
        )
    
    # Test 4: Update Place
    print_header("TEST 4: Update Place")
    
    if found_place:
        found_place.rating = 4.8
        found_place.reviewCount = 150
        found_place.summary = "Updated summary - Test repository"
        
        print_info(f"Updating place ID {place_id}: rating {place.rating} → {found_place.rating}")
        
        update_success = repo.update_place(found_place)
        test_result(
            update_success,
            "Place updated successfully",
            "Failed to update place"
        )
        
        # Verify update
        updated_place = repo.get_place_by_id(place_id)
        if updated_place:
            test_result(
                updated_place.rating == 4.8,
                f"Rating updated correctly: {updated_place.rating}",
                "Rating not updated"
            )
            test_result(
                updated_place.reviewCount == 150,
                f"Review count updated: {updated_place.reviewCount}",
                "Review count not updated"
            )
    
    # Test 5: Search by Keyword
    print_header("TEST 5: Search by Keyword")
    
    # Search for our test place
    print_info("Searching for 'test'...")
    results = repo.find_by_keyword("test")
    test_result(
        len(results) > 0,
        f"Found {len(results)} place(s)",
        "No places found"
    )
    
    if results:
        found_our_place = any(p.id == place_id for p in results)
        test_result(
            found_our_place,
            "Our test place found in search results",
            "Test place not in search results"
        )
    
    # Test 6: Get All Places
    print_header("TEST 6: Get All Places")
    
    all_places = repo.get_all()
    print_info(f"Total places in database: {len(all_places)}")
    test_result(
        len(all_places) > 0,
        f"Retrieved {len(all_places)} place(s)",
        "No places retrieved"
    )
    
    # Test 7: Count After Insert
    print_header("TEST 7: Count After Insert")
    
    new_count = repo.count()
    print_info(f"Place count: {initial_count} → {new_count}")
    test_result(
        new_count > initial_count,
        f"Count increased by {new_count - initial_count}",
        "Count didn't increase"
    )
    
    # Test 8: Place Model Methods
    print_header("TEST 8: Place Model Methods")
    
    if found_place:
        # Test format_money
        formatted_price = found_place.format_money()
        test_result(
            formatted_price is not None and "VNĐ" in formatted_price,
            f"Format money works: {formatted_price}",
            "Format money failed"
        )
        
        # Test is_open_now
        is_open = found_place.is_open_now()
        print_info(f"Restaurant open now: {is_open}")
        test_result(
            is_open is not None,
            f"is_open_now() works: {is_open}",
            "is_open_now() failed"
        )
        
        # Test to_json
        place_json = found_place.to_json()
        test_result(
            isinstance(place_json, dict) and 'name' in place_json,
            f"to_json() works: {len(place_json)} fields",
            "to_json() failed"
        )
        
        # Test address methods
        if found_place.address:
            full_address = found_place.address.get_full_address()
            test_result(
                len(full_address) > 0,
                f"Full address: {full_address}",
                "get_full_address() failed"
            )
    
    # Test 9: Delete Place (Cleanup)
    print_header("TEST 9: Delete Place (Cleanup)")
    
    print_info(f"Deleting test place ID: {place_id}")
    delete_success = repo.delete_by_id(place_id)
    test_result(
        delete_success,
        "Place deleted successfully",
        "Failed to delete place"
    )
    
    # Verify deletion
    deleted_place = repo.get_place_by_id(place_id)
    test_result(
        deleted_place is None,
        "Verified: Place no longer exists",
        "Place still exists after deletion"
    )
    
    # Final count
    final_count = repo.count()
    print_info(f"Final count: {final_count} (should equal initial: {initial_count})")
    test_result(
        final_count == initial_count,
        "Database cleaned up successfully",
        "Database not cleaned properly"
    )
    
    # Summary
    print_header("TEST SUMMARY")
    total_tests = tests_passed + tests_failed
    print(f"\nTotal Tests: {total_tests}")
    print_success(f"Passed: {tests_passed}")
    if tests_failed > 0:
        print_error(f"Failed: {tests_failed}")
    else:
        print_success("All tests passed! 🎉")
    
    print(f"\nSuccess Rate: {(tests_passed/total_tests*100):.1f}%\n")
    
    # Exit code
    sys.exit(0 if tests_failed == 0 else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
