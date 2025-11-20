"""Compatibility shim re-exporting the shared vendor ORM models.

New code should import :class:`awa_common.models_vendor.Vendor` and
:class:`awa_common.models_vendor.VendorPrice` directly.
"""

from awa_common.models_vendor import Vendor, VendorPrice

__all__ = ["Vendor", "VendorPrice"]
