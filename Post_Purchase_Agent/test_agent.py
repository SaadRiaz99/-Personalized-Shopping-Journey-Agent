"""Tests for Post-Purchase Loyalty & Retention Agent (mock mode)."""
import post_purchase_agent_mock as m


def test_c001_profile_new_buyer():
    result = m.cmd_profile("C001")
    assert "Aisha Khan" in result
    assert "BRONZE" in result
    assert "120" in result


def test_c004_profile_platinum():
    result = m.cmd_profile("C004")
    assert "Usman Malik" in result
    assert "PLATINUM" in result
    assert "25000" in result


def test_track_confirmed_order():
    result = m.cmd_track("ORD001")
    assert "ORDER CONFIRMED" in result
    assert "Wireless Headphones" in result
    assert "TCS" in result


def test_track_delayed_order():
    result = m.cmd_track("ORD010")
    assert "DELAYED" in result
    assert "Customs clearance" in result
    assert "apologise" in result


def test_track_delivered():
    result = m.cmd_track("ORD003")
    assert "DELIVERED" in result
    assert "Coffee Maker" in result


def test_sentiment_positive():
    result = m.cmd_sentiment("Amazing product! Love it! Perfect!")
    assert "POSITIVE" in result


def test_sentiment_negative():
    result = m.cmd_sentiment("Stopped working after 2 days. Very disappointed.")
    assert "NEGATIVE" in result


def test_sentiment_mixed():
    result = m.cmd_sentiment("Good quality but the color is slightly different")
    assert "MIXED" in result


def test_sentiment_neutral():
    result = m.cmd_sentiment("It arrived on time.")
    assert "NEUTRAL" in result


def test_retention_delayed():
    result = m.cmd_retention("C006")
    assert "Rs. 200" in result
    assert "URGENT" in result


def test_retention_negative_feedback():
    result = m.cmd_retention("C004")
    assert "WEARE15" in result or "15%" in result
    assert "URGENT" in result


def test_retention_new_buyer():
    result = m.cmd_retention("C001")
    assert "WELCOME10" in result or "10%" in result


def test_feedback_record():
    result = m.cmd_feedback("ORD001", "Great product, very happy!")
    order = m._find_order("ORD001")
    assert order["feedback"] == "Great product, very happy!"
    assert "positive" in result.lower() or "POSITIVE" in result


def test_unknown_order():
    result = m.cmd_track("INVALID")
    assert "not found" in result


def test_unknown_customer():
    result = m.cmd_profile("INVALID")
    assert "Unknown" in result


if __name__ == "__main__":
    tests = [
        ("C001 profile", test_c001_profile_new_buyer),
        ("C004 profile", test_c004_profile_platinum),
        ("Track confirmed", test_track_confirmed_order),
        ("Track delayed", test_track_delayed_order),
        ("Track delivered", test_track_delivered),
        ("Sentiment positive", test_sentiment_positive),
        ("Sentiment negative", test_sentiment_negative),
        ("Sentiment mixed", test_sentiment_mixed),
        ("Sentiment neutral", test_sentiment_neutral),
        ("Retention delayed", test_retention_delayed),
        ("Retention negative feedback", test_retention_negative_feedback),
        ("Retention new buyer", test_retention_new_buyer),
        ("Record feedback", test_feedback_record),
        ("Unknown order", test_unknown_order),
        ("Unknown customer", test_unknown_customer),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print(f"\n  Results: {passed} passed, {failed} failed out of {len(tests)}")
