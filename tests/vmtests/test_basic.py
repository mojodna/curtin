from . import (
    VMBaseClass,
    get_apt_proxy)

from unittest import TestCase

import os
import re
import textwrap


class TestBasicAbs(VMBaseClass):
    __test__ = False
    interactive = False
    conf_file = "examples/tests/basic.yaml"
    install_timeout = 600
    boot_timeout = 120
    extra_disks = ['128G', '128G']
    disk_to_check = {'main_disk': 1, 'main_disk': 2}
    collect_scripts = [textwrap.dedent("""
        cd OUTPUT_COLLECT_D
        blkid -o export /dev/vda > blkid_output_vda
        blkid -o export /dev/vda1 > blkid_output_vda1
        blkid -o export /dev/vda2 > blkid_output_vda2
        btrfs-show-super /dev/vdd > btrfs_show_super_vdd
        cat /proc/partitions > proc_partitions
        ls -al /dev/disk/by-uuid/ > ls_uuid
        cat /etc/fstab > fstab
        mkdir -p /dev/disk/by-dname
        ls /dev/disk/by-dname/ > ls_dname

        v=""
        out=$(apt-config shell v Acquire::HTTP::Proxy)
        eval "$out"
        echo "$v" > apt-proxy
        """)]

    def test_output_files_exist(self):
        self.output_files_exist(
            ["blkid_output_vda", "blkid_output_vda1", "blkid_output_vda2",
             "btrfs_show_super_vdd", "fstab", "ls_dname", "ls_uuid",
             "proc_partitions"])

    def test_ptable(self):
        blkid_info = self.get_blkid_data("blkid_output_vda")
        self.assertEquals(blkid_info["PTTYPE"], "dos")

    def test_partitions(self):
        with open(os.path.join(self.td.collect, "fstab")) as fp:
            fstab_lines = fp.readlines()
        print("\n".join(fstab_lines))
        # Test that vda1 is on /
        blkid_info = self.get_blkid_data("blkid_output_vda1")
        fstab_entry = None
        for line in fstab_lines:
            if blkid_info['UUID'] in line:
                fstab_entry = line
                break
        self.assertIsNotNone(fstab_entry)
        self.assertEqual(fstab_entry.split(' ')[1], "/")

        # Test that vda2 is on /home
        blkid_info = self.get_blkid_data("blkid_output_vda2")
        fstab_entry = None
        for line in fstab_lines:
            if blkid_info['UUID'] in line:
                fstab_entry = line
                break
        self.assertIsNotNone(fstab_entry)
        self.assertEqual(fstab_entry.split(' ')[1], "/home")

        # Test whole disk vdd is mounted at /btrfs
        fstab_entry = None
        for line in fstab_lines:
            if "/dev/vdd" in line:
                fstab_entry = line
                break
        self.assertIsNotNone(fstab_entry)
        self.assertEqual(fstab_entry.split(' ')[1], "/btrfs")

    def test_whole_disk_format(self):
        # confirm the whole disk format is the expected device
        with open(os.path.join(self.td.collect,
                  "btrfs_show_super_vdd"), "r") as fp:
            btrfs_show_super = fp.read()

        with open(os.path.join(self.td.collect, "ls_uuid"), "r") as fp:
            ls_uuid = fp.read()

        # extract uuid from btrfs superblock
        btrfs_fsid = [line for line in btrfs_show_super.split('\n')
                      if line.startswith('fsid\t\t')]
        self.assertEqual(len(btrfs_fsid), 1)
        btrfs_uuid = btrfs_fsid[0].split()[1]
        self.assertTrue(btrfs_uuid is not None)

        # extract uuid from /dev/disk/by-uuid on /dev/vdd
        # parsing ls -al output on /dev/disk/by-uuid:
        # lrwxrwxrwx 1 root root   9 Dec  4 20:02
        #  d591e9e9-825a-4f0a-b280-3bfaf470b83c -> ../../vdg
        vdd_uuid = [line.split()[8] for line in ls_uuid.split('\n')
                    if 'vdd' in line]
        self.assertEqual(len(vdd_uuid), 1)
        vdd_uuid = vdd_uuid.pop()
        self.assertTrue(vdd_uuid is not None)

        # compare them
        self.assertEqual(vdd_uuid, btrfs_uuid)

    def test_proxy_set(self):
        expected = get_apt_proxy()
        with open(os.path.join(self.td.collect, "apt-proxy")) as fp:
            apt_proxy_found = fp.read().rstrip()
        if expected:
            # the proxy should have gotten set through
            self.assertIn(expected, apt_proxy_found)
        else:
            # no proxy, so the output of apt-config dump should be empty
            self.assertEqual("", apt_proxy_found)


class TrustyTestBasic(TestBasicAbs, TestCase):
    __test__ = True
    repo = "maas-daily"
    release = "trusty"
    arch = "amd64"

    # FIXME(LP: #1523037): dname does not work on trusty, so we cannot expect
    # sda-part2 to exist in /dev/disk/by-dname as we can on other releases
    # when dname works on trusty, then we need to re-enable by removing line.
    def test_dname(self):
        print("test_dname does not work for Trusty")

    def test_ptable(self):
        print("test_ptable does not work for Trusty")


class PreciseTestBasic(TestBasicAbs, TestCase):
    __test__ = True
    repo = "maas-daily"
    release = "precise"
    arch = "amd64"
    collect_scripts = [textwrap.dedent("""
        cd OUTPUT_COLLECT_D
        blkid -o export /dev/vda > blkid_output_vda
        blkid -o export /dev/vda1 > blkid_output_vda1
        blkid -o export /dev/vda2 > blkid_output_vda2
        btrfs-show /dev/vdd > btrfs_show_super_vdd
        cat /proc/partitions > proc_partitions
        ls -al /dev/disk/by-uuid/ > ls_uuid
        cat /etc/fstab > fstab
        mkdir -p /dev/disk/by-dname
        ls /dev/disk/by-dname/ > ls_dname

        v=""
        out=$(apt-config shell v Acquire::HTTP::Proxy)
        eval "$out"
        echo "$v" > apt-proxy
        """)]

    def test_whole_disk_format(self):
        # confirm the whole disk format is the expected device
        with open(os.path.join(self.td.collect,
                  "btrfs_show_super_vdd"), "r") as fp:
            btrfs_show_super = fp.read()

        with open(os.path.join(self.td.collect, "ls_uuid"), "r") as fp:
            ls_uuid = fp.read()

        # extract uuid from btrfs superblock
        btrfs_fsid = re.findall('.*uuid:\ (.*)\n', btrfs_show_super)

        self.assertEqual(len(btrfs_fsid), 1)
        btrfs_uuid = btrfs_fsid.pop()
        self.assertTrue(btrfs_uuid is not None)

        # extract uuid from /dev/disk/by-uuid on /dev/vdd
        # parsing ls -al output on /dev/disk/by-uuid:
        # lrwxrwxrwx 1 root root   9 Dec  4 20:02
        #  d591e9e9-825a-4f0a-b280-3bfaf470b83c -> ../../vdg
        vdd_uuid = [line.split()[8] for line in ls_uuid.split('\n')
                    if 'vdd' in line]
        self.assertEqual(len(vdd_uuid), 1)
        vdd_uuid = vdd_uuid.pop()
        self.assertTrue(vdd_uuid is not None)

        # compare them
        self.assertEqual(vdd_uuid, btrfs_uuid)

    def test_ptable(self):
        print("test_ptable does not work for Precise")

    def test_dname(self):
        print("test_dname does not work for Precise")


class VividTestBasic(TestBasicAbs, TestCase):
    __test__ = True
    repo = "maas-daily"
    release = "vivid"
    arch = "amd64"


class WilyTestBasic(TestBasicAbs, TestCase):
    __test__ = True
    repo = "maas-daily"
    release = "wily"
    arch = "amd64"


class XenialTestBasic(TestBasicAbs, TestCase):
    __test__ = True
    repo = "maas-daily"
    release = "xenial"
    arch = "amd64"
    # FIXME: net.ifnames=0 should not be required as image should
    #        eventually address this internally.  Note, also we do
    #        currently need this copied over to the installed environment
    #        although in theory the udev rules we write should fix that.
    extra_kern_args = "--- net.ifnames=0"
