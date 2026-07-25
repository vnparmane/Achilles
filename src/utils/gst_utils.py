def calculate_gst(taxable: float, rate: float, seller_state_code: str | None, buyer_state_code: str | None) -> dict:
    if rate == 0:
        return {"cgst": 0.0, "sgst": 0.0, "igst": 0.0}
    if seller_state_code and buyer_state_code and seller_state_code != buyer_state_code:
        igst = round(taxable * rate / 100, 2)
        return {"cgst": 0.0, "sgst": 0.0, "igst": igst}
    half = round(taxable * rate / 100 / 2, 2)
    return {"cgst": half, "sgst": half, "igst": 0.0}
