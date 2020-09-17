# Copyright (C) 2013, 2014 Red Hat, Inc.
#
# This work is licensed under the GNU GPLv2 or later.
# See the COPYING file in the top-level directory.

import os
import unittest

import pytest

from tests import utils

from virtinst import Capabilities
from virtinst import DomainCapabilities


DATADIR = utils.DATADIR + "/capabilities"


class TestCapabilities(unittest.TestCase):
    def _buildCaps(self, filename):
        path = os.path.join(DATADIR, filename)
        conn = utils.URIs.open_testdefault_cached()
        return Capabilities(conn, open(path).read())

    def testCapsCPUFeaturesNewSyntax(self):
        filename = "test-qemu-with-kvm.xml"
        host_feature_list = ['lahf_lm', 'xtpr', 'cx16', 'tm2', 'est', 'vmx',
            'ds_cpl', 'pbe', 'tm', 'ht', 'ss', 'acpi', 'ds']

        caps = self._buildCaps(filename)
        for f in host_feature_list:
            self.assertEqual(
                    f in [feat.name for feat in caps.host.cpu.features], True)

        self.assertEqual(caps.host.cpu.model, "core2duo")
        self.assertEqual(caps.host.cpu.vendor, "Intel")
        self.assertEqual(caps.host.cpu.topology.threads, 3)
        self.assertEqual(caps.host.cpu.topology.cores, 5)
        self.assertEqual(caps.host.cpu.topology.sockets, 7)

    def testCapsUtilFuncs(self):
        caps_with_kvm = self._buildCaps("test-qemu-with-kvm.xml")
        caps_no_kvm = self._buildCaps("test-qemu-no-kvm.xml")
        caps_empty = self._buildCaps("test-empty.xml")

        def test_utils(caps, has_guests, is_kvm):
            assert caps.has_install_options() == has_guests
            if caps.guests:
                self.assertEqual(caps.guests[0].is_kvm_available(), is_kvm)

        test_utils(caps_empty, False, False)
        test_utils(caps_with_kvm, True, True)
        test_utils(caps_no_kvm, True, False)

        # Small test for extra unittest coverage
        with pytest.raises(ValueError, match=r".*virtualization type 'xen'.*"):
            caps_empty.guest_lookup(os_type="linux")
        with pytest.raises(ValueError, match=r".*not support any.*"):
            caps_empty.guest_lookup()

    def testCapsNuma(self):
        cells = self._buildCaps("lxc.xml").host.topology.cells
        self.assertEqual(len(cells), 1)
        self.assertEqual(len(cells[0].cpus), 8)
        self.assertEqual(cells[0].cpus[3].id, '3')


    ##############################
    # domcapabilities.py testing #
    ##############################

    def testDomainCapabilities(self):
        xml = open(DATADIR + "/test-domcaps.xml").read()
        caps = DomainCapabilities(utils.URIs.open_testdriver_cached(), xml)

        self.assertEqual(caps.os.loader.supported, True)
        self.assertEqual(caps.os.loader.get_values(),
            ["/foo/bar", "/tmp/my_path"])
        self.assertEqual(caps.os.loader.enum_names(), ["type", "readonly"])
        self.assertEqual(caps.os.loader.get_enum("type").get_values(),
            ["rom", "pflash"])

    def testDomainCapabilitiesx86(self):
        xml = open(DATADIR + "/kvm-x86_64-domcaps.xml").read()
        caps = DomainCapabilities(utils.URIs.open_testdriver_cached(), xml)

        self.assertEqual(caps.machine, "pc-i440fx-2.1")
        self.assertEqual(caps.arch, "x86_64")
        self.assertEqual(caps.domain, "kvm")
        self.assertEqual(caps.path, "/bin/qemu-system-x86_64")

        custom_mode = caps.cpu.get_mode("custom")
        self.assertTrue(bool(custom_mode))
        cpu_model = custom_mode.get_model("Opteron_G4")
        self.assertTrue(bool(cpu_model))
        self.assertTrue(cpu_model.usable)

        models = caps.get_cpu_models()
        assert len(models) > 10
        assert "SandyBridge" in models

        assert caps.label_for_firmware_path(None) == "BIOS"
        assert "Custom:" in caps.label_for_firmware_path("/foobar")
        assert "UEFI" in caps.label_for_firmware_path("OVMF")

    def testDomainCapabilitiesAArch64(self):
        xml = open(DATADIR + "/kvm-aarch64-domcaps.xml").read()
        caps = DomainCapabilities(utils.URIs.open_testdriver_cached(), xml)

        assert "None" in caps.label_for_firmware_path(None)
