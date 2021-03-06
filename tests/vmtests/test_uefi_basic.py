# This file is part of curtin. See LICENSE file for copyright and license info.

from . import (VMBaseClass)

from .releases import base_vm_classes as relbase

import textwrap


class TestBasicAbs(VMBaseClass):
    interactive = False
    arch_skip = ["s390x"]
    conf_file = "examples/tests/uefi_basic.yaml"
    extra_disks = ['4G']
    uefi = True
    disk_to_check = [('main_disk', 1), ('main_disk', 2)]
    collect_scripts = VMBaseClass.collect_scripts + [textwrap.dedent("""
        cd OUTPUT_COLLECT_D
        blkid -o export /dev/vda > blkid_output_vda
        blkid -o export /dev/vda1 > blkid_output_vda1
        blkid -o export /dev/vda2 > blkid_output_vda2
        cat /proc/partitions > proc_partitions
        ls -al /dev/disk/by-uuid/ > ls_uuid
        cat /etc/fstab > fstab
        mkdir -p /dev/disk/by-dname
        ls /dev/disk/by-dname/ > ls_dname
        find /etc/network/interfaces.d > find_interfacesd
        ls /sys/firmware/efi/ > ls_sys_firmware_efi
        cat /sys/class/block/vda/queue/logical_block_size > vda_lbs
        cat /sys/class/block/vda/queue/physical_block_size > vda_pbs
        blockdev --getsz /dev/vda > vda_blockdev_getsz
        blockdev --getss /dev/vda > vda_blockdev_getss
        blockdev --getpbsz /dev/vda > vda_blockdev_getpbsz
        blockdev --getbsz /dev/vda > vda_blockdev_getbsz
        """)]

    def test_output_files_exist(self):
        self.output_files_exist(
            ["blkid_output_vda", "blkid_output_vda1", "blkid_output_vda2",
             "fstab", "ls_dname", "ls_uuid", "ls_sys_firmware_efi",
             "proc_partitions"])

    def test_sys_firmware_efi(self):
        sys_efi_possible = [
            'config_table',
            'efivars',
            'fw_platform_size',
            'fw_vendor',
            'runtime',
            'runtime-map',
            'systab',
            'vars',
        ]
        efi_lines = self.load_collect_file(
            "ls_sys_firmware_efi").strip().split('\n')

        # sys/firmware/efi contents differ based on kernel and configuration
        for efi_line in efi_lines:
            self.assertIn(efi_line, sys_efi_possible)

    def test_disk_block_sizes(self):
        """ Test disk logical and physical block size are match
            the class block size.
        """
        for bs in ['lbs', 'pbs']:
            size = int(self.load_collect_file('vda_' + bs))
            self.assertEqual(self.disk_block_size, size)

    def test_disk_block_size_with_blockdev(self):
        """ validate maas setting
        --getsz                   get size in 512-byte sectors
        --getss                   get logical block (sector) size
        --getpbsz                 get physical block (sector) size
        --getbsz                  get blocksize
        """
        for syscall in ['getss', 'getpbsz']:
            size = int(self.load_collect_file('vda_blockdev_' + syscall))
            self.assertEqual(self.disk_block_size, size)


class PreciseUefiTestBasic(relbase.precise, TestBasicAbs):
    __test__ = False

    def test_ptable(self):
        print("test_ptable does not work for Precise")

    def test_dname(self):
        print("test_dname does not work for Precise")


class PreciseHWETUefiTestBasic(relbase.precise_hwe_t, PreciseUefiTestBasic):
    __test__ = False


class TrustyUefiTestBasic(relbase.trusty, TestBasicAbs):
    __test__ = True


class TrustyHWEXUefiTestBasic(relbase.trusty_hwe_x, TrustyUefiTestBasic):
    __test__ = True


class XenialGAUefiTestBasic(relbase.xenial_ga, TestBasicAbs):
    __test__ = True


class XenialHWEUefiTestBasic(relbase.xenial_hwe, TestBasicAbs):
    __test__ = True


class XenialEdgeUefiTestBasic(relbase.xenial_edge, TestBasicAbs):
    __test__ = True


class BionicUefiTestBasic(relbase.bionic, TestBasicAbs):
    __test__ = True


class CosmicUefiTestBasic(relbase.cosmic, TestBasicAbs):
    __test__ = True


class TrustyUefiTestBasic4k(TrustyUefiTestBasic):
    disk_block_size = 4096


class TrustyHWEXUefiTestBasic4k(relbase.trusty_hwe_x, TrustyUefiTestBasic4k):
    __test__ = True


class XenialGAUefiTestBasic4k(XenialGAUefiTestBasic):
    disk_block_size = 4096


class BionicUefiTestBasic4k(BionicUefiTestBasic):
    disk_block_size = 4096


class CosmicUefiTestBasic4k(CosmicUefiTestBasic):
    disk_block_size = 4096

# vi: ts=4 expandtab syntax=python
