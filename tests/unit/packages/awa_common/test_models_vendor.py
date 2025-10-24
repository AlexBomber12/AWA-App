from awa_common.models_vendor import Vendor, VendorPrice


def test_vendor_model_defaults():
    vendor = Vendor(name="Acme", locale="en", email="sales@example.com")
    assert vendor.name == "Acme"
    price = VendorPrice(sku="SKU1", cost=12.5, vendor=vendor)
    assert price.vendor is vendor
