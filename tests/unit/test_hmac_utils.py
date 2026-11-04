from src.utils.hmac_utils import generate_export_signature


def test_generate_export_signature_deterministic():
    secret = "test_signing_secret_12345"
    timestamp = "1730712000"
    method = "GET"
    path = "/portal/export"
    query = "page=1"

    sig1 = generate_export_signature(method, path, query, timestamp, secret)
    sig2 = generate_export_signature(method, path, query, timestamp, secret)

    assert len(sig1) == 64
    assert sig1 == sig2
    # Verify signature changes if timestamp or secret changes
    sig_diff_time = generate_export_signature(method, path, query, "1730712001", secret)
    assert sig1 != sig_diff_time
