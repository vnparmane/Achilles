from src.utils.gst_utils import calculate_gst


def test_same_state_cgst_sgst():
    result = calculate_gst(1000, 18, "27", "27")
    assert result["cgst"] == 90.0
    assert result["sgst"] == 90.0
    assert result["igst"] == 0.0


def test_different_state_igst():
    result = calculate_gst(1000, 18, "27", "09")
    assert result["cgst"] == 0.0
    assert result["sgst"] == 0.0
    assert result["igst"] == 180.0


def test_zero_rate():
    result = calculate_gst(1000, 0, "27", "27")
    assert result["cgst"] == 0.0
    assert result["sgst"] == 0.0
    assert result["igst"] == 0.0


def test_no_state_codes():
    result = calculate_gst(1000, 18, None, None)
    assert result["cgst"] == 90.0
    assert result["sgst"] == 90.0


def test_only_seller_state():
    result = calculate_gst(1000, 18, "27", None)
    assert result["cgst"] == 90.0
    assert result["sgst"] == 90.0
