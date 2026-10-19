#!/usr/bin/env python3
"""Build arkanaOS workstation packages from staged output and official Firefox."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

import lz4.frame

FIREFOX_VERSION = "158.0"
FIREFOX_URL = (
    "https://archive.mozilla.org/pub/firefox/releases/158.0/linux-x86_64/en-US/"
    "firefox-158.0.tar.xz"
)
FIREFOX_SHA512 = (
    "da90b8c7c6f391935508f99a54d730e5141044c0ce0e915900ecb3f208e840f10a4cf8d38"
    "d76852335e6c436bbe2a16e1bf72945fe067340ad94d9ae98f41c59"
)
FIREFOX_ARCHIVE_BYTES = 90_552_004
FIREFOX_ICON = "firefox/browser/chrome/icons/default/default128.png"
PACKAGES = (
    "arkcfg",
    "arkpkg",
    "fastfetch",
    "firefox",
    "git",
    "vim",
    "openbox",
    "openbox-devel",
    "labwc",
    "wlroots",
    "wlroots-devel",
    "libsfdo",
    "libsfdo-devel",
    "weston",
    "weston-devel",
    "seatd",
    "seatd-devel",
    "wayland-devel",
    "wayland-protocols",
    "xwayland",
    "xwayland-devel",
    "xkbcommon-tools",
    "xkbcommon-devel",
    "imagemagick",
    "gdb",
    "xorriso",
    "xorg-nested-servers",
    "gdbm-tools",
    "libxml2-tools",
    "libjpeg-turbo-tools",
    "libwebp-tools",
    "openssl-cli",
    "openssl-rehash",
    "xorg-devel",
    "libxmu",
    "libxmu-devel",
    "libxres",
    "libxres-devel",
    "libxv",
    "libxv-devel",
    "libxcursor",
    "libxinerama",
    "libxfixes",
    "libxrandr",
    "libxrender",
    "libxcomposite",
    "libxdamage",
    "libxft",
    "mesa-devel",
    "libepoxy-devel",
    "cairo-devel",
    "pixman-devel",
    "freetype-devel",
    "fontconfig-devel",
    "harfbuzz-devel",
    "graphite2-devel",
    "glib-devel",
    "libpng-devel",
    "libjpeg-turbo-devel",
    "libwebp-devel",
    "libtiff-devel",
    "libxml2-devel",
    "openssl-devel",
    "curl-devel",
    "libarchive-devel",
    "expat-devel",
    "zlib-devel",
    "zstd-devel",
    "pcre2-devel",
    "libffi-devel",
    "libevent-devel",
    "libuv-devel",
    "libdrm-devel",
    "libinput-devel",
    "libevdev-devel",
    "libwacom-devel",
    "bzip2-devel",
    "xz-devel",
    "lz4-devel",
    "dbus-devel",
    "systemd-devel",
    "at-spi2-core-devel",
    "atk-devel",
    "gdk-pixbuf-devel",
    "pango-devel",
    "librsvg-devel",
    "gtk3-devel",
    "libthai-devel",
    "libdatrie-devel",
    "fribidi-devel",
    "gudev-devel",
    "readline-devel",
    "ncurses-devel",
    "sqlite-devel",
    "gdbm-devel",
    "jansson-devel",
    "json-c-devel",
    "slang-devel",
    "newt-devel",
    "util-linux-devel",
    "bzip2-tools",
    "xz-tools",
    "zstd-tools",
    "lz4-tools",
    "libarchive-tools",
    "dosfstools",
    "e2fsprogs",
    "libparted-devel",
    "kmod-devel",
    "libcap-devel",
    "acl-devel",
    "attr-devel",
    "libseccomp-devel",
    "audit-devel",
    "cryptsetup-devel",
    "devmapper-devel",
    "libbpf-devel",
    "elfutils-devel",
    "libgcrypt-devel",
    "libgpg-error-devel",
    "libtasn1-devel",
    "p11-kit-devel",
    "nettle-devel",
    "gmp-devel",
    "mpfr-devel",
    "libidn2-devel",
    "libunistring-devel",
    "libpsl-devel",
    "libnghttp2-devel",
    "libtirpc-devel",
    "openldap-devel",
    "cyrus-sasl-devel",
    "rust-std",
    "rustc-runtime",
    "llvm-runtime",
    "rustc",
    "cargo",
    "binutils",
    "gcc",
    "gcc-libs",
    "gcc-c",
    "gcc-cxx",
    "gcc-tools",
    "make",
    "cmake",
    "ninja",
    "meson",
    "pkgconf",
    "autoconf",
    "automake",
    "bison",
    "flex",
    "m4",
    "feh",
    "mtools",
    "parted",
    "cryptsetup",
    "efibootmgr",
    "efivar",
    "gettext-tools",
    "fontconfig-tools",
    "gdk-pixbuf-tools",
    "gtk3-tools",
    "ncurses-tools",
    "sqlite-tools",
    "curl-cli",
    "patch",
    "less",
    "rsync",
    "wget",
    "linux-headers",
    "alsa-devel",
    "fuse3-devel",
    "libmagic-devel",
    "libedit-devel",
    "libxcrypt-devel",
    "perl",
    "fvwm3",
    "libnsl-devel",
    "keyutils-devel",
    "libcap-ng-devel",
    "libnvme-devel",
    "libpci-devel",
    "gnutls-devel",
    "krb5-devel",
    "pam-devel",
    "python-devel",
    "newt-tools",
    "fuse3-tools",
    "squashfs-tools",
    "acl-tools",
    "attr-tools",
    "libdeflate-tools",
    "pcre2-tools",
    "libmnl-devel",
    "iproute2",
    "grub",
    "glib-tools",
    "pango-tools",
    "cairo-tools",
    "harfbuzz-tools",
    "dav1d-devel",
    "libdeflate-devel",
    "brotli-devel",
    "libdisplay-info-devel",
    "imlib2-devel",
    "libunwind-devel",
    "lzo-devel",
    "libproc2-devel",
    "xcalc",
    "xclock",
    "xedit",
    "xeyes",
    "xload",
    "xlogo",
    "xmag",
    "xman",
    "xmessage",
    "oclock",
    "xbiff",
    "xclipboard",
    "xconsole",
    "xditview",
    "xev",
    "xfontsel",
    "font-misc-misc",
    "font-alias",
    "font-bh-75dpi",
    "font-bh-100dpi",
    "font-sun-misc",
    "font-schumacher-misc",
    "font-dec-misc",
    "font-sony-misc",
    "font-micro-misc",
    "font-misc-cyrillic",
    "font-daewoo-misc",
    "font-arabic-misc",
    "font-bitstream-75dpi",
    "font-bitstream-100dpi",
    "font-cursor-misc",
    "font-isas-misc",
    "font-jis-misc",
    "font-mutt-misc",
    "font-screen-cyrillic",
    "font-misc-ethiopic",
    "font-misc-meltho",
    "font-bh-ttf",
    "font-bh-type1",
    "font-bitstream-type1",
    "font-ibm-type1",
    "font-cronyx-cyrillic",
    "font-adobe-75dpi",
    "font-adobe-100dpi",
    "font-adobe-utopia-75dpi",
    "font-adobe-utopia-100dpi",
    "font-adobe-utopia-type1",
    "font-winitzki-cyrillic",
    "xorg-font-encodings",
    "xcursor-themes",
    "fox-libs",
    "fox-devel",
    "fox-tools",
    "xfe",
    "fltk-libs",
    "fltk-devel",
    "fltk-tools",
    "dillo",
    "motif-libs",
    "motif-devel",
    "motif-tools",
    "nedit",
    "xbitmaps",
    "xgc",
    "xkill",
    "xmore",
    "xpr",
    "xsm",
    "xwd",
    "xwud",
    "xwininfo",
    "xosview",
    "smproxy",
    "x11perf",
    "xdriinfo",
    "xrestop",
    "xvinfo",
    "iceauth",
    "xfd",
    "xauth",
    "ico",
    "xbacklight",
    "xgamma",
    "xhost",
    "xinput",
    "xmodmap",
    "xprop",
    "xrandr",
    "xrefresh",
    "xset",
    "xsetroot",
    "xinit",
    "xdpyinfo",
    "xlsatoms",
    "xlsclients",
    "xscope",
    "xkbutils",
    "appres",
    "listres",
    "sessreg",
    "setxkbmap",
    "transset",
    "xcmsdb",
    "xcompmgr",
    "xcursorgen",
    "xkbcomp",
    "xkbevd",
    "xkbprint",
    "xlsfonts",
    "xrdb",
    "xstdcmap",
    "xvidtune",
    "bitmap",
    "fonttosfnt",
    "mkfontscale",
    "viewres",
    "luit",
    "xterm",
    "xpdf-tools",
    "nscde",
    "xorg-util-macros",
    "xcb-util",
    "procps-ng",
    "iputils",
    "iptables",
    "libnfnetlink",
    "libndp",
    "libmnl",
    "networkmanager",
    "findutils",
    "sed",
    "grep",
    "diffutils",
    "gawk",
    "nano",
    "tar",
    "sudo",
    "which",
    "unzip",
    "psmisc",
    "kmod-libs",
    "kmod-tools",
    "libpci",
    "pciutils",
    "systemd-libs",
    "systemd-tools",
    "util-linux-libs",
    "rfkill",
    "device-mapper",
    "lvm2",
    "audit-libs",
    "audit-tools",
    "libaio",
    "libnvme",
    "acl-libs",
    "alsa-libs",
    "attr-libs",
    "brotli-libs",
    "brotli-tools",
    "cpio",
    "cyrus-sasl-libs",
    "cyrus-sasl-plugins",
    "file",
    "giflib",
    "giflib-devel",
    "giflib-tools",
    "gmp-libs",
    "gnutls-libs",
    "gnutls-tools",
    "guile",
    "ksh93",
    "krb5-libs",
    "krb5-tools",
    "libbsd",
    "libbsd-devel",
    "libcap",
    "libcap-ng",
    "libcap-tools",
    "libffi-libs",
    "libgc",
    "libidn2-libs",
    "libltdl",
    "libmagic",
    "libmd",
    "libmd-devel",
    "libsensors",
    "libsensors-devel",
    "lm-sensors",
    "lmdb-libs",
    "lmdb-devel",
    "lmdb-tools",
    "mpfr-libs",
    "ncurses-libs",
    "nettle-libs",
    "openldap-libs",
    "openldap-tools",
    "openssl-libs",
    "p11-kit-libs",
    "pam-libs",
    "pcre2-libs",
    "popt-libs",
    "popt-devel",
    "readline-libs",
    "libtasn1-libs",
    "libunistring-libs",
    "system-docs",
)

STAGED_PACKAGE_FILES = {
    "openbox": (
        "usr/bin/openbox",
        "etc/xdg/openbox",
        "usr/share/applications/openbox.desktop",
        "usr/share/xsessions/openbox.desktop",
    ),
    "openbox-devel": (
        "usr/include/openbox",
        "usr/lib/libobrender.a",
        "usr/lib/libobt.a",
        "usr/lib/pkgconfig/obrender-3.5.pc",
        "usr/lib/pkgconfig/obt-3.5.pc",
    ),
    "labwc": (
        "usr/bin/labwc",
        "usr/share/wayland-sessions/labwc.desktop",
        "usr/share/xdg-desktop-portal/labwc-portals.conf",
    ),
    "wlroots": ("usr/lib/libwlroots-0.19.so",),
    "wlroots-devel": (
        "usr/include/wlroots-0.19",
        "usr/lib/pkgconfig/wlroots-0.19.pc",
    ),
    "libsfdo": (
        "usr/lib/libsfdo-basedir.so.0",
        "usr/lib/libsfdo-desktop-file.so.0",
        "usr/lib/libsfdo-desktop.so.0",
        "usr/lib/libsfdo-icon.so.0",
    ),
    "libsfdo-devel": (
        "usr/include/sfdo-basedir.h",
        "usr/include/sfdo-desktop-file.h",
        "usr/include/sfdo-desktop.h",
        "usr/include/sfdo-icon.h",
        "usr/lib/pkgconfig/libsfdo-basedir.pc",
        "usr/lib/pkgconfig/libsfdo-desktop-file.pc",
        "usr/lib/pkgconfig/libsfdo-desktop.pc",
        "usr/lib/pkgconfig/libsfdo-icon.pc",
    ),
    "weston": (
        "usr/bin/weston",
        "usr/lib/libweston-14",
        "usr/lib/weston",
        "usr/share/weston",
        "usr/share/wayland-sessions/weston.desktop",
    ),
    "weston-devel": (
        "usr/include/libweston-14",
        "usr/include/weston",
        "usr/share/libweston-14/protocols",
        "usr/lib/pkgconfig/libweston-14.pc",
        "usr/share/pkgconfig/libweston-14-protocols.pc",
    ),
    "seatd": (
        "usr/bin/seatd",
        "usr/bin/seatd-launch",
        "usr/lib/libseat.so.1",
        "usr/lib/systemd/system/seatd.service",
        "etc/systemd/system/multi-user.target.wants/seatd.service",
    ),
    "seatd-devel": (
        "usr/include/libseat.h",
        "usr/lib/pkgconfig/libseat.pc",
    ),
    "wayland-devel": (
        "usr/bin/wayland-scanner",
        "usr/share/wayland",
        "usr/share/aclocal/wayland-scanner.m4",
    ),
    "wayland-protocols": (
        "usr/include/wayland-protocols",
        "usr/share/wayland-protocols",
        "usr/share/pkgconfig/wayland-protocols.pc",
    ),
    "xwayland": (
        "usr/bin/Xwayland",
        "usr/share/applications/org.freedesktop.Xwayland.desktop",
        "usr/share/man/man1/Xwayland.1",
    ),
    "xwayland-devel": ("usr/share/pkgconfig/xwaylandproto.pc",),
    "xkbcommon-tools": (
        "usr/bin/xkbcli",
        "usr/lib/xkbcommon",
    ),
    "xkbcommon-devel": (
        "usr/include/xkbcommon",
        "usr/lib/pkgconfig/xkbcommon.pc",
        "usr/lib/pkgconfig/xkbcommon-x11.pc",
    ),
    "imagemagick": (
        "usr/bin/animate",
        "usr/bin/compare",
        "usr/bin/composite",
        "usr/bin/conjure",
        "usr/bin/convert",
        "usr/bin/display",
        "usr/bin/identify",
        "usr/bin/import",
        "usr/bin/magick",
        "usr/bin/magick-script",
        "usr/bin/mogrify",
        "usr/bin/montage",
        "usr/bin/stream",
        "usr/lib/ImageMagick-7.1.2",
        "usr/share/ImageMagick-7",
    ),
    "gdb": (
        "usr/bin/gdb",
        "usr/bin/gdb-add-index",
        "usr/share/gdb",
        "usr/share/man/man1/gdb.1",
        "usr/share/man/man1/gdb-add-index.1",
    ),
    "xorriso": (
        "usr/bin/xorriso",
        "usr/bin/xorriso-dd-target",
        "usr/bin/xorriso-tcltk",
        "usr/bin/xorrisofs",
        "usr/share/man/man1/xorriso.1",
        "usr/share/man/man1/xorriso-dd-target.1",
        "usr/share/man/man1/xorriso-tcltk.1",
        "usr/share/man/man1/xorrisofs.1",
    ),
    "xorg-nested-servers": (
        "usr/bin/Xnest",
        "usr/bin/Xvfb",
        "usr/share/man/man1/Xnest.1",
        "usr/share/man/man1/Xvfb.1",
    ),
    "gdbm-tools": (
        "usr/bin/gdbm_dump",
        "usr/bin/gdbm_load",
        "usr/bin/gdbmtool",
        "usr/share/man/man1/gdbm_dump.1",
        "usr/share/man/man1/gdbm_load.1",
        "usr/share/man/man1/gdbmtool.1",
    ),
    "libxml2-tools": (
        "usr/bin/xmlcatalog",
        "usr/bin/xml2-config",
        "usr/bin/xmllint",
        "usr/bin/xmlwf",
        "usr/share/man/man1/xmlcatalog.1",
        "usr/share/man/man1/xmllint.1",
        "usr/share/man/man1/xmlwf.1",
    ),
    "libjpeg-turbo-tools": (
        "usr/bin/cjpeg",
        "usr/bin/djpeg",
        "usr/bin/jpegtran",
        "usr/bin/rdjpgcom",
        "usr/bin/wrjpgcom",
        "usr/share/man/man1/cjpeg.1",
        "usr/share/man/man1/djpeg.1",
        "usr/share/man/man1/jpegtran.1",
        "usr/share/man/man1/rdjpgcom.1",
        "usr/share/man/man1/wrjpgcom.1",
    ),
    "libwebp-tools": (
        "usr/bin/cwebp",
        "usr/bin/dwebp",
        "usr/bin/gif2webp",
        "usr/bin/img2webp",
        "usr/bin/webpinfo",
        "usr/bin/webpmux",
        "usr/share/man/man1/cwebp.1",
        "usr/share/man/man1/gif2webp.1",
        "usr/share/man/man1/img2webp.1",
        "usr/share/man/man1/webpinfo.1",
        "usr/share/man/man1/webpmux.1",
    ),
    "openssl-cli": ("usr/bin/openssl",),
    "openssl-rehash": (
        "usr/bin/c_rehash",
        "usr/share/man/man1/openssl-rehash.1ssl",
    ),
    "xorg-devel": (
        "usr/include/X11",
        "usr/include/xcb",
        "usr/include/xorg",
        "usr/include/libxcvt",
        "usr/include/pciaccess.h",
    ),
    "mesa-devel": (
        "usr/include/EGL",
        "usr/include/GL",
        "usr/include/GLES",
        "usr/include/GLES2",
        "usr/include/GLES3",
        "usr/include/KHR",
        "usr/include/gbm.h",
        "usr/include/gbm_backend_abi.h",
    ),
    "libepoxy-devel": (
        "usr/include/epoxy",
        "usr/lib/pkgconfig/epoxy.pc",
        "usr/lib/libepoxy.so",
    ),
    "cairo-devel": ("usr/include/cairo",),
    "pixman-devel": (
        "usr/include/pixman-1",
        "usr/lib/pkgconfig/pixman-1.pc",
        "usr/lib/libpixman-1.so",
    ),
    "freetype-devel": (
        "usr/include/freetype2",
        "usr/bin/freetype-config",
        "usr/lib/pkgconfig/freetype2.pc",
        "usr/lib/libfreetype.so",
    ),
    "fontconfig-devel": (
        "usr/include/fontconfig",
        "usr/lib/pkgconfig/fontconfig.pc",
        "usr/lib/libfontconfig.so",
    ),
    "harfbuzz-devel": ("usr/include/harfbuzz",),
    "graphite2-devel": (
        "usr/include/graphite2",
        "usr/lib/pkgconfig/graphite2.pc",
        "usr/lib/libgraphite2.so",
    ),
    "glib-devel": (
        "usr/include/glib-2.0",
        "usr/include/gio-unix-2.0",
        "usr/lib/glib-2.0/include",
    ),
    "libpng-devel": (
        "usr/include/libpng16",
        "usr/include/png.h",
        "usr/include/pngconf.h",
        "usr/include/pnglibconf.h",
        "usr/bin/libpng-config",
        "usr/bin/libpng16-config",
        "usr/lib/pkgconfig/libpng16.pc",
        "usr/lib/libpng.so",
        "usr/lib/libpng16.so",
    ),
    "libjpeg-turbo-devel": (
        "usr/include/jconfig.h",
        "usr/include/jerror.h",
        "usr/include/jmorecfg.h",
        "usr/include/jpeglib.h",
        "usr/include/turbojpeg.h",
        "usr/lib/pkgconfig/libjpeg.pc",
        "usr/lib/libjpeg.so",
        "usr/lib/libturbojpeg.so",
    ),
    "libwebp-devel": ("usr/include/webp",),
    "libtiff-devel": (
        "usr/include/tiff.h",
        "usr/include/tiffconf.h",
        "usr/include/tiffio.h",
        "usr/include/tiffio.hxx",
        "usr/include/tiffvers.h",
        "usr/lib/pkgconfig/libtiff-4.pc",
        "usr/lib/libtiff.so",
        "usr/lib/libtiffxx.so",
    ),
    "libxml2-devel": (
        "usr/include/libxml2",
        "usr/lib/pkgconfig/libxml-2.0.pc",
        "usr/lib/libxml2.so",
    ),
    "openssl-devel": (
        "usr/include/openssl",
        "usr/lib/pkgconfig/openssl.pc",
        "usr/lib/libssl.so",
        "usr/lib/libcrypto.so",
    ),
    "curl-devel": (
        "usr/include/curl",
        "usr/bin/curl-config",
        "usr/lib/pkgconfig/libcurl.pc",
        "usr/lib/libcurl.so",
    ),
    "libarchive-devel": (
        "usr/include/archive.h",
        "usr/include/archive_entry.h",
        "usr/lib/pkgconfig/libarchive.pc",
        "usr/lib/libarchive.so",
    ),
    "expat-devel": (
        "usr/include/expat.h",
        "usr/include/expat_config.h",
        "usr/include/expat_external.h",
        "usr/lib/pkgconfig/expat.pc",
        "usr/lib/libexpat.so",
    ),
    "zlib-devel": (
        "usr/include/zlib.h",
        "usr/include/zconf.h",
        "usr/lib/pkgconfig/zlib.pc",
        "usr/lib/libz.so",
    ),
    "zstd-devel": (
        "usr/include/zstd.h",
        "usr/include/zstd_errors.h",
        "usr/include/zdict.h",
        "usr/lib/pkgconfig/libzstd.pc",
        "usr/lib/libzstd.so",
    ),
    "pcre2-devel": (
        "usr/include/pcre2.h",
        "usr/include/pcre2posix.h",
    ),
    "libffi-devel": (
        "usr/include/ffi.h",
        "usr/include/ffitarget.h",
        "usr/lib/pkgconfig/libffi.pc",
        "usr/lib/libffi.so",
    ),
    "libevent-devel": (
        "usr/include/event.h",
        "usr/include/event2",
        "usr/include/evdns.h",
        "usr/include/evhttp.h",
        "usr/include/evrpc.h",
        "usr/include/evutil.h",
    ),
    "libuv-devel": (
        "usr/include/uv.h",
        "usr/include/uv",
        "usr/lib/pkgconfig/libuv.pc",
        "usr/lib/libuv.so",
    ),
    "libdrm-devel": (
        "usr/include/libdrm",
        "usr/include/xf86drm.h",
        "usr/include/xf86drmMode.h",
    ),
    "libinput-devel": (
        "usr/include/libinput.h",
        "usr/lib/pkgconfig/libinput.pc",
        "usr/lib/libinput.so",
    ),
    "libevdev-devel": (
        "usr/include/libevdev-1.0",
        "usr/lib/pkgconfig/libevdev.pc",
        "usr/lib/libevdev.so",
    ),
    "libwacom-devel": (
        "usr/include/libwacom-1.0",
        "usr/lib/pkgconfig/libwacom.pc",
        "usr/lib/libwacom.so",
    ),
    "bzip2-devel": (
        "usr/include/bzlib.h",
        "usr/lib/pkgconfig/bzip2.pc",
    ),
    "xz-devel": (
        "usr/include/lzma.h",
        "usr/include/lzma",
        "usr/lib/pkgconfig/liblzma.pc",
        "usr/lib/liblzma.so",
    ),
    "lz4-devel": (
        "usr/include/lz4.h",
        "usr/include/lz4frame.h",
        "usr/include/lz4frame_static.h",
        "usr/include/lz4hc.h",
        "usr/lib/liblz4.so",
    ),
    "dbus-devel": (
        "usr/include/dbus-1.0",
        "usr/lib/dbus-1.0/include",
        "usr/lib/pkgconfig/dbus-1.pc",
        "usr/lib/libdbus-1.so",
    ),
    "systemd-devel": (
        "usr/include/systemd",
        "usr/include/libudev.h",
        "usr/lib/pkgconfig/libsystemd.pc",
        "usr/lib/pkgconfig/libudev.pc",
        "usr/lib/libsystemd.so",
        "usr/lib/libudev.so",
    ),
    "at-spi2-core-devel": (
        "usr/include/at-spi-2.0",
        "usr/include/at-spi2-atk",
        "usr/lib/pkgconfig/atspi-2.pc",
        "usr/lib/pkgconfig/atk-bridge-2.0.pc",
        "usr/lib/libatspi.so",
        "usr/lib/libatk-bridge-2.0.so",
    ),
    "atk-devel": (
        "usr/include/atk-1.0",
        "usr/lib/pkgconfig/atk.pc",
        "usr/lib/libatk-1.0.so",
    ),
    "gdk-pixbuf-devel": (
        "usr/include/gdk-pixbuf-2.0",
        "usr/lib/pkgconfig/gdk-pixbuf-2.0.pc",
        "usr/lib/libgdk_pixbuf-2.0.so",
    ),
    "pango-devel": ("usr/include/pango-1.0",),
    "gtk3-devel": (
        "usr/include/gtk-3.0",
        "usr/include/gail-3.0",
    ),
    "libthai-devel": (
        "usr/include/thai",
        "usr/lib/pkgconfig/libthai.pc",
        "usr/lib/libthai.so",
    ),
    "libdatrie-devel": (
        "usr/include/datrie",
        "usr/lib/pkgconfig/datrie-0.2.pc",
        "usr/lib/libdatrie.so",
    ),
    "fribidi-devel": (
        "usr/include/fribidi",
        "usr/lib/pkgconfig/fribidi.pc",
        "usr/lib/libfribidi.so",
    ),
    "gudev-devel": (
        "usr/include/gudev-1.0",
        "usr/lib/pkgconfig/gudev-1.0.pc",
        "usr/lib/libgudev-1.0.so",
    ),
    "readline-devel": (
        "usr/include/readline",
        "usr/lib/pkgconfig/readline.pc",
        "usr/lib/pkgconfig/history.pc",
        "usr/lib/libreadline.so",
        "usr/lib/libhistory.so",
    ),
    "ncurses-devel": (
        "usr/include/curses.h",
        "usr/include/ncurses.h",
        "usr/include/ncurses_dll.h",
        "usr/include/form.h",
        "usr/include/menu.h",
        "usr/include/panel.h",
        "usr/include/term.h",
        "usr/include/term_entry.h",
        "usr/include/unctrl.h",
    ),
    "sqlite-devel": (
        "usr/include/sqlite3.h",
        "usr/include/sqlite3ext.h",
        "usr/lib/pkgconfig/sqlite3.pc",
        "usr/lib/libsqlite3.so",
    ),
    "gdbm-devel": (
        "usr/include/gdbm.h",
        "usr/lib/libgdbm.so",
    ),
    "jansson-devel": (
        "usr/include/jansson.h",
        "usr/include/jansson_config.h",
        "usr/lib/pkgconfig/jansson.pc",
        "usr/lib/libjansson.so",
    ),
    "json-c-devel": (
        "usr/include/json-c",
        "usr/lib/pkgconfig/json-c.pc",
        "usr/lib/libjson-c.so",
    ),
    "slang-devel": (
        "usr/include/slang.h",
        "usr/include/slcurses.h",
        "usr/lib/pkgconfig/slang.pc",
        "usr/lib/libslang.so",
    ),
    "newt-devel": (
        "usr/include/newt.h",
        "usr/lib/pkgconfig/libnewt.pc",
        "usr/lib/libnewt.so",
    ),
    "util-linux-devel": (
        "usr/include/uuid",
        "usr/include/blkid",
        "usr/include/libmount",
        "usr/include/libfdisk",
        "usr/include/libsmartcols",
    ),
    "libparted-devel": (
        "usr/include/parted",
        "usr/lib/pkgconfig/libparted.pc",
        "usr/lib/libparted.so",
        "usr/lib/libparted-fs-resize.so",
    ),
    "kmod-devel": (
        "usr/include/libkmod.h",
        "usr/lib/pkgconfig/libkmod.pc",
        "usr/lib/libkmod.so",
    ),
    "libcap-devel": (
        "usr/include/sys/capability.h",
        "usr/lib/pkgconfig/libcap.pc",
        "usr/lib/libcap.so",
    ),
    "acl-devel": (
        "usr/include/acl",
        "usr/include/sys/acl.h",
        "usr/lib/pkgconfig/libacl.pc",
        "usr/lib/libacl.so",
    ),
    "attr-devel": (
        "usr/include/attr",
        "usr/lib/pkgconfig/libattr.pc",
        "usr/lib/libattr.so",
    ),
    "libseccomp-devel": (
        "usr/include/seccomp.h",
        "usr/lib/pkgconfig/libseccomp.pc",
        "usr/lib/libseccomp.so",
    ),
    "audit-devel": (
        "usr/include/libaudit.h",
        "usr/include/audit-records.h",
        "usr/include/audit_logging.h",
        "usr/include/auparse-defs.h",
        "usr/include/auparse.h",
        "usr/include/auplugin.h",
        "usr/lib/pkgconfig/audit.pc",
        "usr/lib/pkgconfig/auparse.pc",
        "usr/lib/libaudit.so",
        "usr/lib/libauparse.so",
    ),
    "cryptsetup-devel": (
        "usr/include/libcryptsetup.h",
        "usr/lib/pkgconfig/libcryptsetup.pc",
        "usr/lib/libcryptsetup.so",
    ),
    "devmapper-devel": (
        "usr/include/libdevmapper.h",
        "usr/lib/pkgconfig/devmapper.pc",
        "usr/lib/libdevmapper.so",
    ),
    "libbpf-devel": (
        "usr/include/bpf",
        "usr/lib/pkgconfig/libbpf.pc",
        "usr/lib/libbpf.so",
    ),
    "elfutils-devel": (
        "usr/include/libelf.h",
        "usr/include/gelf.h",
        "usr/include/elfutils",
        "usr/lib/pkgconfig/libelf.pc",
        "usr/lib/libelf.so",
        "usr/lib/libdw.so",
    ),
    "libgcrypt-devel": (
        "usr/include/gcrypt.h",
        "usr/lib/pkgconfig/libgcrypt.pc",
        "usr/lib/libgcrypt.so",
    ),
    "libgpg-error-devel": (
        "usr/include/gpg-error.h",
        "usr/include/gpgrt.h",
        "usr/lib/pkgconfig/gpg-error.pc",
        "usr/lib/libgpg-error.so",
    ),
    "libtasn1-devel": (
        "usr/include/libtasn1.h",
        "usr/lib/pkgconfig/libtasn1.pc",
        "usr/lib/libtasn1.so",
    ),
    "p11-kit-devel": (
        "usr/include/p11-kit-1",
        "usr/lib/pkgconfig/p11-kit-1.pc",
        "usr/lib/libp11-kit.so",
    ),
    "nettle-devel": (
        "usr/include/nettle",
        "usr/lib/pkgconfig/nettle.pc",
        "usr/lib/pkgconfig/hogweed.pc",
        "usr/lib/libnettle.so",
        "usr/lib/libhogweed.so",
    ),
    "gmp-devel": (
        "usr/include/gmp.h",
        "usr/include/gmpxx.h",
        "usr/lib/pkgconfig/gmp.pc",
        "usr/lib/pkgconfig/gmpxx.pc",
        "usr/lib/libgmp.so",
        "usr/lib/libgmpxx.so",
    ),
    "mpfr-devel": (
        "usr/include/mpfr.h",
        "usr/include/mpf2mpfr.h",
        "usr/lib/pkgconfig/mpfr.pc",
        "usr/lib/libmpfr.so",
    ),
    "libidn2-devel": (
        "usr/include/idn2.h",
        "usr/lib/pkgconfig/libidn2.pc",
        "usr/lib/libidn2.so",
    ),
    "libunistring-devel": (
        "usr/include/unistring",
        "usr/lib/libunistring.so",
    ),
    "libpsl-devel": (
        "usr/include/libpsl.h",
        "usr/lib/pkgconfig/libpsl.pc",
        "usr/lib/libpsl.so",
    ),
    "libnghttp2-devel": (
        "usr/include/nghttp2",
        "usr/lib/pkgconfig/libnghttp2.pc",
        "usr/lib/libnghttp2.so",
    ),
    "libtirpc-devel": (
        "usr/include/tirpc",
        "usr/lib/pkgconfig/libtirpc.pc",
        "usr/lib/libtirpc.so",
    ),
    "openldap-devel": (
        "usr/include/ldap.h",
        "usr/include/lber.h",
        "usr/include/lber_types.h",
        "usr/include/ldap_cdefs.h",
        "usr/include/ldap_features.h",
        "usr/include/ldap_schema.h",
        "usr/include/ldap_utf8.h",
        "usr/include/ldif.h",
        "usr/include/openldap.h",
        "usr/lib/pkgconfig/ldap.pc",
        "usr/lib/libldap.so",
        "usr/lib/liblber.so",
    ),
    "cyrus-sasl-devel": (
        "usr/include/sasl",
        "usr/lib/pkgconfig/libsasl2.pc",
        "usr/lib/libsasl2.so",
    ),
    "rust-std": ("usr/lib/rustlib",),
    "rustc-runtime": ("usr/lib/librustc_driver-999a121de2f042be.so",),
    "llvm-runtime": ("usr/lib/libLLVM.so.23.1-rust-1.99.0-stable",),
    "rustc": (
        "usr/bin/rustc",
        "usr/bin/rustdoc",
    ),
    "cargo": ("usr/bin/cargo",),
    "binutils": (
        "usr/bin/addr2line",
        "usr/bin/ar",
        "usr/bin/as",
        "usr/bin/c++filt",
        "usr/bin/elfedit",
        "usr/bin/gprof",
        "usr/bin/ld",
        "usr/bin/ld.bfd",
        "usr/bin/nm",
        "usr/bin/objcopy",
        "usr/bin/objdump",
        "usr/bin/ranlib",
        "usr/bin/readelf",
        "usr/bin/size",
        "usr/bin/strings",
        "usr/bin/strip",
        "usr/lib/libbfd-2.45.so",
        "usr/lib/libopcodes-2.45.so",
        "usr/lib/libsframe.so.2",
        "usr/lib/libctf.so.0",
        "usr/lib/libctf-nobfd.so.0",
    ),
    "gcc": (
        "usr/bin/gcc",
        "usr/bin/cc",
        "usr/bin/cpp",
        "usr/bin/gcc-ar",
        "usr/bin/gcc-nm",
        "usr/bin/gcc-ranlib",
    ),
    "gcc-libs": (
        "usr/lib/gcc",
        "usr/share/gcc-15.2.0",
    ),
    "gcc-c": (
        "usr/lib/gcc/x86_64-pc-linux-gnu/15.2.0/cc1",
        "usr/lib/gcc/x86_64-pc-linux-gnu/15.2.0/lto1",
        "usr/lib/gcc/x86_64-pc-linux-gnu/15.2.0/lto-wrapper",
        "usr/lib/gcc/x86_64-pc-linux-gnu/15.2.0/collect2",
    ),
    "gcc-cxx": (
        "usr/bin/g++",
        "usr/bin/c++",
        "usr/lib/gcc/x86_64-pc-linux-gnu/15.2.0/cc1plus",
    ),
    "gcc-tools": (
        "usr/bin/lto-dump",
        "usr/bin/gcov",
        "usr/bin/gcov-dump",
        "usr/bin/gcov-tool",
    ),
    "make": ("usr/bin/make",),
    "cmake": (
        "usr/bin/cmake",
        "usr/bin/ccmake",
        "usr/bin/cpack",
        "usr/bin/ctest",
        "usr/share/cmake-4.2",
    ),
    "ninja": ("usr/bin/ninja",),
    "meson": ("usr/bin/meson",),
    "pkgconf": (
        "usr/bin/pkgconf",
        "usr/bin/pkg-config",
    ),
    "libxmu": (),
    "libxmu-devel": (),
    "libxres": (),
    "libxres-devel": (),
    "libxv": (),
    "libxv-devel": (),
    "libxcursor": (),
    "libxinerama": (),
    "libxfixes": (),
    "libxrandr": (),
    "libxrender": (),
    "libxcomposite": (),
    "libxdamage": (),
    "libxft": (),
    "fox-libs": (),
    "fox-devel": (),
    "fox-tools": (),
    "xfe": (),
    "fltk-libs": (),
    "fltk-devel": (),
    "fltk-tools": (),
    "dillo": (),
    "motif-libs": (),
    "motif-devel": ("usr/include/Xm", "usr/include/Mrm", "usr/include/uil"),
    "motif-tools": ("usr/bin/mwm", "usr/bin/uil"),
    "nedit": (
        "usr/bin/nedit",
        "usr/bin/nedit-client",
        "usr/share/licenses/nedit/COPYRIGHT",
    ),
    "autoconf": (
        "usr/bin/autoconf",
        "usr/bin/autoheader",
        "usr/bin/autom4te",
        "usr/bin/autoreconf",
        "usr/bin/autoscan",
        "usr/bin/autoupdate",
        "usr/share/autoconf",
    ),
    "automake": (
        "usr/bin/automake",
        "usr/share/automake-1.18",
    ),
    "bison": (
        "usr/bin/bison",
        "usr/bin/yacc",
        "usr/share/bison",
    ),
    "flex": ("usr/bin/flex",),
    "m4": ("usr/bin/m4",),
    "feh": (
        "usr/bin/feh",
        "usr/share/applications/feh.desktop",
    ),
    "mtools": (
        "usr/bin/mattrib",
        "usr/bin/mcopy",
        "usr/bin/mdel",
        "usr/bin/mdeltree",
        "usr/bin/mdir",
        "usr/bin/mdoctorfat",
        "usr/bin/mformat",
        "usr/bin/mlabel",
        "usr/bin/mmd",
        "usr/bin/mmove",
        "usr/bin/mpartition",
        "usr/bin/mrd",
        "usr/bin/mren",
        "usr/bin/mshowfat",
        "usr/bin/mtools",
        "usr/bin/mtoolstest",
        "usr/bin/mtype",
        "usr/bin/mzip",
        "usr/share/info/mtools.info",
        "usr/share/man/man1/mattrib.1",
        "usr/share/man/man1/mcopy.1",
        "usr/share/man/man1/mdel.1",
        "usr/share/man/man1/mdeltree.1",
        "usr/share/man/man1/mdir.1",
        "usr/share/man/man1/mdoctorfat.1",
        "usr/share/man/man1/mformat.1",
        "usr/share/man/man1/mlabel.1",
        "usr/share/man/man1/mmd.1",
        "usr/share/man/man1/mmove.1",
        "usr/share/man/man1/mpartition.1",
        "usr/share/man/man1/mrd.1",
        "usr/share/man/man1/mren.1",
        "usr/share/man/man1/mshowfat.1",
        "usr/share/man/man1/mtools.1",
        "usr/share/man/man1/mtoolstest.1",
        "usr/share/man/man1/mtype.1",
        "usr/share/man/man1/mzip.1",
    ),
    "parted": (
        "usr/bin/parted",
        "usr/lib/libparted.so.2",
        "usr/lib/libparted-fs-resize.so.0",
    ),
    "cryptsetup": (
        "usr/bin/cryptsetup",
        "usr/lib/libcryptsetup.so.12",
    ),
    "efibootmgr": ("usr/bin/efibootmgr",),
    "efivar": (
        "usr/bin/efivar",
        "usr/lib/libefiboot.so.1",
        "usr/lib/libefivar.so.1",
    ),
    "gettext-tools": (
        "usr/bin/gettext",
        "usr/bin/gettextize",
        "usr/bin/msgattrib",
        "usr/bin/msgcat",
        "usr/bin/msgcmp",
        "usr/bin/msgcomm",
        "usr/bin/msgconv",
        "usr/bin/msgen",
        "usr/bin/msgexec",
        "usr/bin/msgfilter",
        "usr/bin/msgfmt",
        "usr/bin/msggrep",
        "usr/bin/msginit",
        "usr/bin/msgmerge",
        "usr/bin/msgunfmt",
        "usr/bin/msguniq",
        "usr/bin/ngettext",
        "usr/bin/xgettext",
        "usr/share/gettext",
    ),
    "fontconfig-tools": (
        "usr/bin/fc-cache",
        "usr/bin/fc-cat",
        "usr/bin/fc-list",
        "usr/bin/fc-match",
        "usr/bin/fc-pattern",
        "usr/bin/fc-query",
        "usr/bin/fc-scan",
        "usr/bin/fc-validate",
    ),
    "gdk-pixbuf-tools": (
        "usr/bin/gdk-pixbuf-query-loaders",
        "usr/bin/gdk-pixbuf-thumbnailer",
    ),
    "gtk3-tools": (
        "usr/bin/gtk-update-icon-cache",
        "usr/bin/gtk-query-immodules-3.0",
    ),
    "ncurses-tools": (
        "usr/bin/infocmp",
        "usr/bin/tic",
        "usr/bin/toe",
        "usr/bin/tput",
        "usr/bin/captoinfo",
        "usr/bin/clear",
    ),
    "sqlite-tools": ("usr/bin/sqlite3",),
    "curl-cli": ("usr/bin/curl",),
    "patch": ("usr/bin/patch",),
    "less": (
        "usr/bin/less",
        "usr/bin/lesskey",
        "usr/bin/lessecho",
        "usr/bin/more",
    ),
    "rsync": ("usr/bin/rsync",),
    "wget": ("usr/bin/wget",),
    "system-docs": (
        "usr/share/man",
        "usr/share/info",
        "usr/share/doc",
    ),
    "linux-headers": (
        "usr/include/linux",
        "usr/include/asm",
        "usr/include/asm-generic",
        "usr/include/sound",
        "usr/include/mtd",
        "usr/include/rdma",
        "usr/include/scsi",
        "usr/include/xen",
    ),
    "alsa-devel": (
        "usr/include/alsa",
        "usr/lib/pkgconfig/alsa.pc",
        "usr/lib/pkgconfig/alsa-topology.pc",
        "usr/lib/libasound.so",
        "usr/lib/libatopology.so",
    ),
    "fuse3-devel": (
        "usr/include/fuse3",
        "usr/lib/pkgconfig/fuse3.pc",
        "usr/lib/libfuse3.so",
    ),
    "libmagic-devel": (
        "usr/include/magic.h",
        "usr/lib/pkgconfig/libmagic.pc",
        "usr/lib/libmagic.so",
    ),
    "libedit-devel": (
        "usr/include/editline",
        "usr/include/histedit.h",
        "usr/lib/pkgconfig/libedit.pc",
        "usr/lib/libedit.so",
    ),
    "libxcrypt-devel": (
        "usr/include/crypt.h",
        "usr/lib/pkgconfig/libxcrypt.pc",
        "usr/lib/libcrypt.so",
    ),
    "libnsl-devel": (
        "usr/include/rpcsvc",
        "usr/lib/pkgconfig/libnsl.pc",
        "usr/lib/libnsl.so",
    ),
    "keyutils-devel": (
        "usr/include/keyutils.h",
        "usr/lib/pkgconfig/libkeyutils.pc",
        "usr/lib/libkeyutils.so",
    ),
    "libcap-ng-devel": (
        "usr/include/cap-ng.h",
        "usr/lib/pkgconfig/libcap-ng.pc",
        "usr/lib/libcap-ng.so",
    ),
    "libnvme-devel": (
        "usr/include/nvme",
        "usr/lib/pkgconfig/libnvme.pc",
        "usr/lib/pkgconfig/libnvme-mi.pc",
        "usr/lib/libnvme.so",
        "usr/lib/libnvme-mi.so",
    ),
    "libpci-devel": (
        "usr/include/pci",
        "usr/lib/pkgconfig/libpci.pc",
        "usr/lib/libpci.so",
    ),
    "gnutls-devel": (
        "usr/include/gnutls",
        "usr/lib/pkgconfig/gnutls.pc",
        "usr/lib/libgnutls.so",
    ),
    "krb5-devel": (
        "usr/include/krb5",
        "usr/include/gssapi",
        "usr/include/gssrpc",
        "usr/include/kadm5",
        "usr/include/kdb.h",
        "usr/include/com_err.h",
        "usr/lib/pkgconfig/mit-krb5.pc",
        "usr/lib/pkgconfig/mit-krb5-gssapi.pc",
        "usr/lib/pkgconfig/krb5.pc",
        "usr/lib/pkgconfig/krb5-gssapi.pc",
        "usr/lib/pkgconfig/gssrpc.pc",
        "usr/lib/pkgconfig/kadm-client.pc",
        "usr/lib/pkgconfig/kadm-server.pc",
        "usr/lib/pkgconfig/kdb.pc",
        "usr/lib/libcom_err.so",
        "usr/lib/libgssapi_krb5.so",
        "usr/lib/libgssrpc.so",
        "usr/lib/libk5crypto.so",
        "usr/lib/libkadm5clnt.so",
        "usr/lib/libkadm5clnt_mit.so",
        "usr/lib/libkadm5srv.so",
        "usr/lib/libkadm5srv_mit.so",
        "usr/lib/libkdb5.so",
        "usr/lib/libkrb5.so",
        "usr/lib/libkrb5support.so",
        "usr/lib/libverto.so",
    ),
    "pam-devel": (
        "usr/include/security",
        "usr/lib/pkgconfig/pam.pc",
        "usr/lib/pkgconfig/pam_misc.pc",
        "usr/lib/pkgconfig/pamc.pc",
        "usr/lib/libpam.so",
        "usr/lib/libpam_misc.so",
        "usr/lib/libpamc.so",
    ),
    "python-devel": (
        "usr/include/python3.13",
        "usr/lib/python3.13/config-3.13-x86_64-linux-gnu",
        "usr/lib/pkgconfig/python-3.13.pc",
        "usr/lib/pkgconfig/python-3.13-embed.pc",
        "usr/lib/pkgconfig/python3.pc",
        "usr/lib/pkgconfig/python3-embed.pc",
        "usr/lib/libpython3.13.so",
        "usr/lib/libpython3.so",
    ),
    "dav1d-devel": (
        "usr/include/dav1d",
        "usr/lib/pkgconfig/dav1d.pc",
        "usr/lib/libdav1d.so",
    ),
    "libdeflate-devel": (
        "usr/include/libdeflate.h",
        "usr/lib/pkgconfig/libdeflate.pc",
        "usr/lib/libdeflate.so",
    ),
    "brotli-devel": (
        "usr/include/brotli",
        "usr/lib/pkgconfig/libbrotlicommon.pc",
        "usr/lib/pkgconfig/libbrotlidec.pc",
        "usr/lib/pkgconfig/libbrotlienc.pc",
        "usr/lib/libbrotlicommon.so",
        "usr/lib/libbrotlidec.so",
        "usr/lib/libbrotlienc.so",
    ),
    "libdisplay-info-devel": (
        "usr/include/libdisplay-info",
        "usr/lib/pkgconfig/libdisplay-info.pc",
        "usr/lib/libdisplay-info.so",
    ),
    "imlib2-devel": (
        "usr/include/Imlib2.h",
        "usr/lib/pkgconfig/imlib2.pc",
        "usr/lib/libImlib2.so",
    ),
    "libunwind-devel": (
        "usr/include/libunwind.h",
        "usr/include/libunwind-common.h",
        "usr/include/libunwind-coredump.h",
        "usr/include/libunwind-dynamic.h",
        "usr/include/libunwind-ptrace.h",
        "usr/include/libunwind-x86_64.h",
        "usr/lib/pkgconfig/libunwind.pc",
        "usr/lib/pkgconfig/libunwind-coredump.pc",
        "usr/lib/pkgconfig/libunwind-generic.pc",
        "usr/lib/pkgconfig/libunwind-ptrace.pc",
        "usr/lib/pkgconfig/libunwind-setjmp.pc",
        "usr/lib/libunwind.so",
        "usr/lib/libunwind-generic.so",
        "usr/lib/libunwind-coredump.so",
        "usr/lib/libunwind-ptrace.so",
        "usr/lib/libunwind-setjmp.so",
    ),
    "lzo-devel": (
        "usr/include/lzo",
        "usr/lib/pkgconfig/lzo2.pc",
        "usr/lib/liblzo2.so",
    ),
    "libproc2-devel": (
        "usr/include/libproc2",
        "usr/lib/pkgconfig/libproc2.pc",
        "usr/lib/libproc2.so",
    ),
    "xcalc": ("usr/bin/xcalc",),
    "xclock": ("usr/bin/xclock",),
    "xedit": ("usr/bin/xedit",),
    "xeyes": ("usr/bin/xeyes",),
    "xload": ("usr/bin/xload",),
    "xlogo": ("usr/bin/xlogo",),
    "xmag": ("usr/bin/xmag",),
    "xman": ("usr/bin/xman",),
    "xmessage": ("usr/bin/xmessage",),
    "oclock": ("usr/bin/oclock",),
    "xbiff": ("usr/bin/xbiff",),
    "xclipboard": ("usr/bin/xclipboard",),
    "xconsole": ("usr/bin/xconsole",),
    "xditview": ("usr/bin/xditview",),
    "xev": ("usr/bin/xev",),
    "xfontsel": ("usr/bin/xfontsel",),
    "xgc": ("usr/bin/xgc",),
    "xkill": ("usr/bin/xkill",),
    "xmore": ("usr/bin/xmore",),
    "xpr": ("usr/bin/xpr",),
    "xsm": ("usr/bin/xsm",),
    "xwd": ("usr/bin/xwd",),
    "xwud": ("usr/bin/xwud",),
    "xwininfo": ("usr/bin/xwininfo",),
    "smproxy": ("usr/bin/smproxy",),
    "x11perf": ("usr/bin/x11perf",),
    "xdriinfo": ("usr/bin/xdriinfo",),
    "xrestop": ("usr/bin/xrestop",),
    "xvinfo": ("usr/bin/xvinfo",),
    "xosview": ("usr/bin/xosview2", "usr/bin/xosview"),
    "librsvg-devel": (
        "usr/bin/rsvg-convert",
        "usr/include/librsvg-2.0",
        "usr/lib/pkgconfig/librsvg-2.0.pc",
        "usr/share/licenses/spdx/LGPL-2.1-or-later.txt",
    ),
    "perl": (
        "usr/bin/perl",
        "usr/lib/perl5/5.42",
        "usr/share/perl5",
        "usr/share/licenses/spdx/Artistic-1.0-Perl.txt",
    ),
    "fvwm3": (
        "usr/lib/fvwm3",
        "usr/libexec/fvwm3",
        "usr/share/fvwm3",
        "usr/share/xsessions/fvwm3.desktop",
        "usr/share/licenses/spdx/GPL-2.0-or-later.txt",
    ),
    "nscde": (
        "usr/bin/arkana-nscde-session",
        "usr/bin/nscde",
        "usr/bin/nscde_fvwmclnt",
        "etc/skel/.NsCDE",
        "etc/xdg/menus/nscde-applications.menu",
        "usr/share/NsCDE",
        "usr/share/icons/NsCDE",
        "usr/share/licenses/documentation/nscde",
        "usr/share/xsessions/nscde.desktop",
    ),
    "glib-tools": (
        "usr/bin/gapplication",
        "usr/bin/gdbus",
        "usr/bin/gdbus-codegen",
        "usr/bin/gio",
        "usr/bin/gio-querymodules",
        "usr/bin/glib-compile-resources",
        "usr/bin/glib-compile-schemas",
        "usr/bin/glib-genmarshal",
        "usr/bin/glib-gettextize",
        "usr/bin/glib-mkenums",
        "usr/bin/gobject-query",
        "usr/bin/gresource",
        "usr/bin/gsettings",
        "usr/bin/gtester",
        "usr/bin/gtester-report",
        "usr/share/glib-2.0",
    ),
    "pango-tools": (
        "usr/bin/pango-list",
        "usr/bin/pango-segmentation",
        "usr/bin/pango-view",
    ),
    "cairo-tools": ("usr/bin/cairo-trace",),
    "harfbuzz-tools": (
        "usr/bin/hb-info",
        "usr/bin/hb-ot-shape-closure",
        "usr/bin/hb-shape",
        "usr/bin/hb-subset",
        "usr/bin/hb-view",
    ),
    "luit": ("usr/bin/luit",),
    "xterm": (
        "usr/bin/koi8rxterm",
        "usr/bin/resize",
        "usr/bin/uxterm",
        "usr/bin/xterm",
        "etc/X11/app-defaults/KOI8RXTerm",
        "etc/X11/app-defaults/KOI8RXTerm-color",
        "etc/X11/app-defaults/UXTerm",
        "etc/X11/app-defaults/UXTerm-color",
        "etc/X11/app-defaults/XTerm",
        "etc/X11/app-defaults/XTerm-color",
        "usr/share/applications/uxterm.desktop",
        "usr/share/applications/xterm.desktop",
    ),
    "xpdf-tools": (
        "usr/bin/pdfdetach",
        "usr/bin/pdffonts",
        "usr/bin/pdfimages",
        "usr/bin/pdfinfo",
        "usr/bin/pdftohtml",
        "usr/bin/pdftoppm",
        "usr/bin/pdftopng",
        "usr/bin/pdftops",
        "usr/bin/pdftotext",
        "usr/share/licenses/xpdf-tools",
    ),
    "font-misc-misc": (
        "usr/share/fonts/misc",
        "usr/share/licenses/font-misc-misc/COPYING",
    ),
    "font-alias": (
        "usr/share/fonts/misc/fonts.alias",
        "usr/share/fonts/75dpi/fonts.alias",
        "usr/share/fonts/100dpi/fonts.alias",
        "usr/share/fonts/cyrillic/fonts.alias",
        "usr/share/licenses/font-alias/COPYING",
    ),
    "font-bh-75dpi": (
        "usr/share/fonts/75dpi",
        "usr/share/licenses/font-bh-75dpi",
    ),
    "font-bh-100dpi": (
        "usr/share/fonts/100dpi",
        "usr/share/licenses/font-bh-100dpi",
    ),
    "font-sun-misc": (
        "usr/share/fonts/sun-misc",
        "usr/share/licenses/font-sun-misc/COPYING",
    ),
    "font-schumacher-misc": (
        "usr/share/fonts/schumacher-misc",
        "usr/share/licenses/font-schumacher-misc/COPYING",
    ),
    "font-dec-misc": (
        "usr/share/fonts/dec-misc",
        "usr/share/licenses/font-dec-misc/COPYING",
    ),
    "font-sony-misc": (
        "usr/share/fonts/sony-misc",
        "usr/share/licenses/font-sony-misc/COPYING",
    ),
    "font-micro-misc": (
        "usr/share/fonts/micro-misc",
        "usr/share/licenses/font-micro-misc/COPYING",
    ),
    "font-misc-cyrillic": (
        "usr/share/fonts/misc-cyrillic",
        "usr/share/licenses/font-misc-cyrillic/COPYING",
    ),
    "font-daewoo-misc": (
        "usr/share/fonts/daewoo-misc",
        "usr/share/licenses/font-daewoo-misc/COPYING",
    ),
    "font-arabic-misc": (
        "usr/share/fonts/arabic-misc",
        "usr/share/licenses/font-arabic-misc/COPYING",
    ),
    "font-bitstream-75dpi": (
        "usr/share/fonts/bitstream-75dpi",
        "usr/share/licenses/font-bitstream-75dpi/COPYING",
    ),
    "font-bitstream-100dpi": (
        "usr/share/fonts/bitstream-100dpi",
        "usr/share/licenses/font-bitstream-100dpi/COPYING",
    ),
    "font-cursor-misc": (
        "usr/share/fonts/cursor-misc",
        "usr/share/licenses/font-cursor-misc/COPYING",
    ),
    "font-isas-misc": (
        "usr/share/fonts/isas-misc",
        "usr/share/licenses/font-isas-misc/COPYING",
    ),
    "font-jis-misc": (
        "usr/share/fonts/jis-misc",
        "usr/share/licenses/font-jis-misc/COPYING",
    ),
    "font-mutt-misc": (
        "usr/share/fonts/mutt-misc",
        "usr/share/licenses/font-mutt-misc/COPYING",
    ),
    "font-screen-cyrillic": (
        "usr/share/fonts/screen-cyrillic",
        "usr/share/licenses/font-screen-cyrillic/COPYING",
    ),
    "font-misc-ethiopic": (
        "usr/share/fonts/misc-ethiopic",
        "usr/share/licenses/font-misc-ethiopic/COPYING",
    ),
    "font-misc-meltho": (
        "usr/share/fonts/misc-meltho",
        "usr/share/licenses/font-misc-meltho/COPYING",
    ),
    "font-bh-ttf": (
        "usr/share/fonts/bh-ttf",
        "usr/share/licenses/font-bh-ttf/COPYING",
        "usr/share/licenses/font-bh-ttf/COPYRIGHT.BH",
    ),
    "font-bh-type1": (
        "usr/share/fonts/bh-type1",
        "usr/share/licenses/font-bh-type1/COPYING",
        "usr/share/licenses/font-bh-type1/COPYRIGHT.BH",
    ),
    "font-bitstream-type1": (
        "usr/share/fonts/bitstream-type1",
        "usr/share/licenses/font-bitstream-type1/COPYING",
        "usr/share/licenses/font-bitstream-type1/Copyright",
    ),
    "font-ibm-type1": (
        "usr/share/fonts/ibm-type1",
        "usr/share/licenses/font-ibm-type1/COPYING",
        "usr/share/licenses/font-ibm-type1/COPYRIGHT.IBM",
    ),
    "font-cronyx-cyrillic": (
        "usr/share/fonts/cronyx-cyrillic",
        "usr/share/licenses/font-cronyx-cyrillic/COPYING",
        "usr/share/licenses/font-cronyx-cyrillic/COPYRIGHT",
    ),
    "font-adobe-75dpi": (
        "usr/share/fonts/adobe-75dpi",
        "usr/share/licenses/font-adobe-75dpi/COPYING",
    ),
    "font-adobe-100dpi": (
        "usr/share/fonts/adobe-100dpi",
        "usr/share/licenses/font-adobe-100dpi/COPYING",
    ),
    "font-adobe-utopia-75dpi": (
        "usr/share/fonts/adobe-utopia-75dpi",
        "usr/share/licenses/font-adobe-utopia-75dpi/COPYING",
    ),
    "font-adobe-utopia-100dpi": (
        "usr/share/fonts/adobe-utopia-100dpi",
        "usr/share/licenses/font-adobe-utopia-100dpi/COPYING",
    ),
    "font-adobe-utopia-type1": (
        "usr/share/fonts/adobe-utopia-type1",
        "usr/share/licenses/font-adobe-utopia-type1/COPYING",
    ),
    "font-winitzki-cyrillic": (
        "usr/share/fonts/winitzki-cyrillic",
        "usr/share/licenses/font-winitzki-cyrillic/COPYING",
    ),
    "xorg-font-encodings": (),
    "xcursor-themes": (
        "usr/share/icons",
        "usr/share/licenses/xcursor-themes/COPYING",
    ),
    "xbitmaps": (
        "usr/include/X11/bitmaps",
        "usr/lib/pkgconfig/xbitmaps.pc",
        "usr/share/licenses/xbitmaps/COPYING",
    ),
    "iceauth": ("usr/bin/iceauth",),
    "xfd": ("usr/bin/xfd",),
    "xauth": ("usr/bin/xauth",),
    "ico": ("usr/bin/ico",),
    "xorg-util-macros": (
        "usr/share/aclocal/xorg-macros.m4",
        "usr/share/pkgconfig/xorg-macros.pc",
        "usr/share/licenses/xorg-util-macros/COPYING",
    ),
    "xcb-util": (
        "usr/include/xcb/xcb_util.h",
        "usr/include/xcb/xcb_atom.h",
        "usr/include/xcb/xcb_aux.h",
        "usr/include/xcb/xcb_event.h",
        "usr/share/licenses/xcb-util/COPYING",
    ),
    "xbacklight": ("usr/bin/xbacklight",),
    "xgamma": ("usr/bin/xgamma",),
    "xhost": ("usr/bin/xhost",),
    "xinput": ("usr/bin/xinput",),
    "xmodmap": ("usr/bin/xmodmap",),
    "xprop": ("usr/bin/xprop",),
    "xrandr": ("usr/bin/xrandr",),
    "xrefresh": ("usr/bin/xrefresh",),
    "xset": ("usr/bin/xset",),
    "xsetroot": ("usr/bin/xsetroot",),
    "xinit": ("usr/bin/xinit",),
    "xdpyinfo": ("usr/bin/xdpyinfo",),
    "xlsatoms": ("usr/bin/xlsatoms",),
    "xlsclients": ("usr/bin/xlsclients",),
    "xscope": ("usr/bin/xscope",),
    "xkbutils": ("usr/bin/xkbbell", "usr/bin/xkbvleds", "usr/bin/xkbwatch"),
    "appres": ("usr/bin/appres",),
    "listres": ("usr/bin/listres",),
    "sessreg": ("usr/bin/sessreg",),
    "setxkbmap": ("usr/bin/setxkbmap",),
    "transset": ("usr/bin/transset",),
    "xcmsdb": ("usr/bin/xcmsdb",),
    "xcompmgr": ("usr/bin/xcompmgr",),
    "xcursorgen": ("usr/bin/xcursorgen",),
    "xkbcomp": ("usr/bin/xkbcomp",),
    "xkbevd": ("usr/bin/xkbevd",),
    "xkbprint": ("usr/bin/xkbprint",),
    "xlsfonts": ("usr/bin/xlsfonts",),
    "xrdb": ("usr/bin/xrdb",),
    "xstdcmap": ("usr/bin/xstdcmap",),
    "xvidtune": ("usr/bin/xvidtune",),
    "bitmap": ("usr/bin/bitmap", "usr/bin/bmtoa", "usr/bin/atobm"),
    "fonttosfnt": ("usr/bin/fonttosfnt",),
    "mkfontscale": ("usr/bin/mkfontscale",),
    "viewres": ("usr/bin/viewres",),
    "bzip2-tools": ("usr/bin/bzip2",),
    "xz-tools": ("usr/bin/xz",),
    "zstd-tools": ("usr/bin/zstd",),
    "lz4-tools": ("usr/bin/lz4",),
    "libarchive-tools": ("usr/bin/bsdtar",),
    "dosfstools": (
        "usr/bin/dosfsck",
        "usr/bin/fatlabel",
        "usr/bin/fsck.fat",
        "usr/bin/fsck.msdos",
        "usr/bin/fsck.vfat",
        "usr/bin/mkfs.fat",
        "usr/bin/mkfs.msdos",
        "usr/bin/mkfs.vfat",
    ),
    "e2fsprogs": (
        "etc/mke2fs.conf",
        "usr/bin/badblocks",
        "usr/bin/chattr",
        "usr/bin/debugfs",
        "usr/bin/dumpe2fs",
        "usr/bin/e2freefrag",
        "usr/bin/e2fsck",
        "usr/bin/e2image",
        "usr/bin/e2label",
        "usr/bin/e2mmpstatus",
        "usr/bin/e2undo",
        "usr/bin/e4crypt",
        "usr/bin/e4defrag",
        "usr/bin/filefrag",
        "usr/bin/fsck.ext2",
        "usr/bin/fsck.ext3",
        "usr/bin/fsck.ext4",
        "usr/bin/lsattr",
        "usr/bin/mke2fs",
        "usr/bin/mkfs.ext2",
        "usr/bin/mkfs.ext3",
        "usr/bin/mkfs.ext4",
        "usr/bin/resize2fs",
        "usr/bin/tune2fs",
    ),
    "acl-tools": ("usr/bin/getfacl", "usr/bin/setfacl"),
    "attr-tools": ("usr/bin/attr", "usr/bin/getfattr", "usr/bin/setfattr"),
    "libdeflate-tools": (
        "usr/bin/libdeflate-gunzip",
        "usr/bin/libdeflate-gzip",
    ),
    "pcre2-tools": ("usr/bin/pcre2grep", "usr/bin/pcre2test"),
    "libmnl-devel": (
        "usr/include/libmnl",
        "usr/lib/pkgconfig/libmnl.pc",
        "usr/lib/libmnl.so",
    ),
    "iproute2": (
        "usr/bin/bridge",
        "usr/bin/ctstat",
        "usr/bin/devlink",
        "usr/bin/ifstat",
        "usr/bin/ip",
        "usr/bin/lnstat",
        "usr/bin/nstat",
        "usr/bin/rdma",
        "usr/bin/routel",
        "usr/bin/rtacct",
        "usr/bin/rtmon",
        "usr/bin/ss",
        "usr/bin/tc",
        "usr/lib/tc",
        "usr/share/iproute2",
    ),
    "grub": (
        "usr/lib/grub",
        "usr/share/grub",
        "etc/grub.d",
    ),
    "newt-tools": ("usr/bin/whiptail",),
    "fuse3-tools": (
        "usr/bin/fusermount3",
        "usr/bin/mount.fuse3",
    ),
    "squashfs-tools": (
        "usr/bin/mksquashfs",
        "usr/bin/unsquashfs",
    ),
    "procps-ng": (
        "usr/bin/free",
        "usr/bin/pgrep",
        "usr/bin/pkill",
        "usr/bin/pmap",
        "usr/bin/ps",
        "usr/bin/pwdx",
        "usr/bin/slabtop",
        "usr/bin/sysctl",
        "usr/bin/tload",
        "usr/bin/top",
        "usr/bin/uptime",
        "usr/bin/vmstat",
        "usr/bin/w",
        "usr/bin/watch",
    ),
    "iputils": (
        "usr/bin/arping",
        "usr/bin/clockdiff",
        "usr/bin/ping",
        "usr/bin/tracepath",
    ),
    "iptables": (
        "usr/bin/ip6tables",
        "usr/bin/ip6tables-apply",
        "usr/bin/ip6tables-legacy",
        "usr/bin/ip6tables-legacy-restore",
        "usr/bin/ip6tables-legacy-save",
        "usr/bin/ip6tables-restore",
        "usr/bin/ip6tables-save",
        "usr/bin/iptables",
        "usr/bin/iptables-apply",
        "usr/bin/iptables-legacy",
        "usr/bin/iptables-legacy-restore",
        "usr/bin/iptables-legacy-save",
        "usr/bin/iptables-restore",
        "usr/bin/iptables-save",
        "usr/bin/iptables-xml",
        "usr/bin/xtables-legacy-multi",
        "usr/lib/xtables",
    ),
    "libnfnetlink": (),
    "libndp": (),
    "libmnl": (),
    "networkmanager": (
        "usr/bin/NetworkManager",
        "usr/bin/nmcli",
        "usr/bin/nm-online",
        "usr/lib/NetworkManager",
        "usr/lib/systemd/system/NetworkManager.service",
        "usr/lib/systemd/system/NetworkManager-dispatcher.service",
        "usr/lib/systemd/system/NetworkManager-wait-online.service",
        "usr/lib/systemd/system/NetworkManager-config-initrd.service",
        "usr/lib/systemd/system/NetworkManager-initrd.service",
        "usr/lib/systemd/system/NetworkManager-wait-online-initrd.service",
        "usr/lib/udev/rules.d/84-nm-drivers.rules",
        "usr/lib/udev/rules.d/85-nm-unmanaged.rules",
        "usr/lib/udev/rules.d/90-nm-thunderbolt.rules",
        "usr/share/dbus-1/system.d/org.freedesktop.NetworkManager.conf",
    ),
    "findutils": (
        "usr/bin/find",
        "usr/bin/locate",
        "usr/bin/updatedb",
        "usr/bin/xargs",
    ),
    "sed": ("usr/bin/sed",),
    "grep": ("usr/bin/egrep", "usr/bin/fgrep", "usr/bin/grep"),
    "diffutils": (
        "usr/bin/cmp",
        "usr/bin/diff",
        "usr/bin/diff3",
        "usr/bin/sdiff",
    ),
    "gawk": ("usr/bin/awk", "usr/bin/gawk", "usr/bin/gawk-5.3.2"),
    "nano": ("usr/bin/nano", "usr/bin/rnano", "usr/share/nano"),
    "tar": ("usr/bin/tar",),
    "sudo": (
        "etc/pam.d/sudo",
        "etc/sudoers",
        "etc/sudoers.d",
        "usr/bin/sudo",
        "usr/bin/sudoedit",
        "usr/lib/sudo",
        "usr/libexec/sudo",
        "usr/sbin/visudo",
    ),
    "which": ("usr/bin/which",),
    "unzip": (
        "usr/bin/funzip",
        "usr/bin/unzip",
        "usr/bin/unzipsfx",
        "usr/bin/zipgrep",
        "usr/bin/zipinfo",
    ),
    "psmisc": (
        "usr/bin/fuser",
        "usr/bin/killall",
        "usr/bin/peekfd",
        "usr/bin/prtstat",
        "usr/bin/pslog",
        "usr/bin/pstree",
        "usr/bin/pstree.x11",
    ),
    "kmod-libs": (),
    "kmod-tools": (
        "usr/bin/depmod",
        "usr/bin/insmod",
        "usr/bin/kmod",
        "usr/bin/lsmod",
        "usr/bin/modinfo",
        "usr/bin/modprobe",
        "usr/bin/rmmod",
    ),
    "libpci": (),
    "pciutils": (
        "usr/bin/lspci",
        "usr/bin/setpci",
        "usr/share/hwdata/pci.ids",
    ),
    "systemd-libs": (
        "usr/lib/libnss_systemd.so.2",
        "usr/lib/libsystemd.so.0",
        "usr/lib/libudev.so.1",
        "usr/lib/systemd/libsystemd-core-257.so",
        "usr/lib/systemd/libsystemd-shared-257.so",
    ),
    "systemd-tools": (
        "usr/bin/bootctl",
        "usr/bin/busctl",
        "usr/bin/coredumpctl",
        "usr/bin/hostnamectl",
        "usr/bin/journalctl",
        "usr/bin/localectl",
        "usr/bin/loginctl",
        "usr/bin/machinectl",
        "usr/bin/networkctl",
        "usr/bin/oomctl",
        "usr/bin/portablectl",
        "usr/bin/resolvectl",
        "usr/bin/systemd-ac-power",
        "usr/bin/systemd-analyze",
        "usr/bin/systemd-ask-password",
        "usr/bin/systemd-cat",
        "usr/bin/systemd-cgls",
        "usr/bin/systemd-cgtop",
        "usr/bin/systemd-confext",
        "usr/bin/systemd-creds",
        "usr/bin/systemd-delta",
        "usr/bin/systemd-detect-virt",
        "usr/bin/systemd-dissect",
        "usr/bin/systemd-escape",
        "usr/bin/systemd-hwdb",
        "usr/bin/systemd-id128",
        "usr/bin/systemd-inhibit",
        "usr/bin/systemd-machine-id-setup",
        "usr/bin/systemd-mount",
        "usr/bin/systemd-notify",
        "usr/bin/systemd-nspawn",
        "usr/bin/systemd-path",
        "usr/bin/systemd-repart",
        "usr/bin/systemd-resolve",
        "usr/bin/systemd-run",
        "usr/bin/systemd-socket-activate",
        "usr/bin/systemd-stdio-bridge",
        "usr/bin/systemd-sysext",
        "usr/bin/systemd-tmpfiles",
        "usr/bin/systemd-tty-ask-password-agent",
        "usr/bin/systemd-umount",
        "usr/bin/systemd-vpick",
        "usr/bin/systemctl",
        "usr/bin/timedatectl",
        "usr/bin/udevadm",
    ),
    "util-linux-libs": (),
    "rfkill": ("usr/bin/rfkill",),
    "device-mapper": ("usr/bin/dmsetup", "usr/bin/dmstats"),
    "lvm2": (
        "usr/bin/lvm",
        "usr/lib/udev/rules.d/11-dm-lvm.rules",
        "usr/lib/udev/rules.d/69-dm-lvm.rules",
    ),
    "audit-libs": (),
    "audit-tools": (
        "usr/bin/auditctl",
        "usr/bin/auditd",
        "usr/bin/audisp-af_unix",
        "usr/bin/audisp-filter",
        "usr/bin/audisp-remote",
        "usr/bin/audisp-syslog",
        "usr/bin/audispd-zos-remote",
        "usr/bin/augenrules",
        "usr/bin/aulast",
        "usr/bin/aulastlog",
        "usr/bin/aureport",
        "usr/bin/ausearch",
        "usr/bin/ausyscall",
    ),
    "libaio": (),
    "libnvme": (),
    "acl-libs": (),
    "alsa-libs": ("usr/share/alsa",),
    "attr-libs": (),
    "brotli-libs": (),
    "brotli-tools": ("usr/bin/brotli",),
    "cpio": ("usr/bin/cpio",),
    "cyrus-sasl-libs": (),
    "cyrus-sasl-plugins": (),
    "file": ("usr/bin/file", "usr/share/misc/magic.mgc"),
    "giflib": (),
    "giflib-devel": (
        "usr/include/gif_lib.h",
        "usr/lib/libgif.so",
        "usr/lib/libgif.a",
    ),
    "giflib-tools": (
        "usr/bin/gif2rgb",
        "usr/bin/gifbuild",
        "usr/bin/gifclrmp",
        "usr/bin/giffix",
        "usr/bin/giftext",
        "usr/bin/giftool",
    ),
    "gmp-libs": (),
    "gnutls-libs": (),
    "gnutls-tools": (
        "usr/bin/certtool",
        "usr/bin/gnutls-cli",
        "usr/bin/gnutls-cli-debug",
        "usr/bin/gnutls-serv",
        "usr/bin/psktool",
    ),
    "guile": (
        "usr/bin/guile",
        "usr/lib/libguile-3.0.so.1",
        "usr/lib/guile/3.0",
        "usr/share/guile/3.0",
    ),
    "ksh93": ("usr/bin/ksh", "usr/bin/ksh93"),
    "krb5-libs": (),
    "krb5-tools": (
        "usr/bin/kadmin",
        "usr/bin/kadmin.local",
        "usr/bin/kadmind",
        "usr/bin/kdestroy",
        "usr/bin/kinit",
        "usr/bin/klist",
        "usr/bin/kpasswd",
        "usr/bin/kprop",
        "usr/bin/kpropd",
        "usr/bin/kproplog",
        "usr/bin/ksu",
        "usr/bin/ktutil",
        "usr/bin/kvno",
        "usr/bin/kdb5_util",
        "usr/bin/krb5-config",
    ),
    "libbsd": (),
    "libbsd-devel": (
        "usr/include/bsd",
        "usr/lib/libbsd.so",
        "usr/lib/libbsd.a",
        "usr/lib/libbsd-ctor.a",
        "usr/lib/pkgconfig/libbsd.pc",
        "usr/lib/pkgconfig/libbsd-ctor.pc",
        "usr/lib/pkgconfig/libbsd-overlay.pc",
    ),
    "libcap": (),
    "libcap-ng": (),
    "libcap-tools": (
        "usr/bin/capsh",
        "usr/bin/captest",
        "usr/bin/filecap",
        "usr/bin/getcap",
        "usr/bin/getpcaps",
        "usr/bin/setcap",
    ),
    "libffi-libs": (),
    "libgc": (),
    "libidn2-libs": (),
    "libltdl": (),
    "libmagic": (),
    "libmd": (),
    "libmd-devel": (
        "usr/include/md2.h",
        "usr/include/md4.h",
        "usr/include/md5.h",
        "usr/include/sha.h",
        "usr/include/sha1.h",
        "usr/include/sha2.h",
        "usr/include/sha256.h",
        "usr/include/sha512.h",
        "usr/lib/libmd.so",
        "usr/lib/libmd.a",
        "usr/lib/pkgconfig/libmd.pc",
    ),
    "libsensors": (),
    "libsensors-devel": (
        "usr/include/sensors",
        "usr/lib/libsensors.so",
    ),
    "lm-sensors": (
        "usr/bin/sensors",
        "usr/bin/sensors-detect",
        "usr/bin/fancontrol",
        "usr/bin/pwmconfig",
        "usr/bin/sensors-conf-convert",
        "usr/bin/isadump",
        "usr/bin/isaset",
    ),
    "lmdb-libs": ("usr/lib/liblmdb.so",),
    "lmdb-devel": ("usr/include/lmdb.h", "usr/lib/liblmdb.a"),
    "lmdb-tools": (
        "usr/bin/mdb_copy",
        "usr/bin/mdb_dump",
        "usr/bin/mdb_load",
        "usr/bin/mdb_stat",
    ),
    "mpfr-libs": (),
    "ncurses-libs": (),
    "nettle-libs": (),
    "openldap-libs": (),
    "openldap-tools": (
        "usr/bin/ldapcompare",
        "usr/bin/ldapdelete",
        "usr/bin/ldapexop",
        "usr/bin/ldapmodify",
        "usr/bin/ldapmodrdn",
        "usr/bin/ldappasswd",
        "usr/bin/ldapsearch",
        "usr/bin/ldapurl",
        "usr/bin/ldapvc",
        "usr/bin/ldapwhoami",
    ),
    "openssl-libs": (),
    "p11-kit-libs": (),
    "pam-libs": (),
    "pcre2-libs": (),
    "popt-libs": (),
    "popt-devel": (
        "usr/include/popt.h",
        "usr/lib/libpopt.so",
        "usr/lib/libpopt.a",
        "usr/lib/pkgconfig/popt.pc",
    ),
    "readline-libs": (),
    "libtasn1-libs": (),
    "libunistring-libs": (),
}

STAGED_PACKAGE_GLOBS = {
    "pkgconf": (
        "usr/include/pkgconf",
        "usr/lib/libpkgconf.so*",
        "usr/lib/pkgconfig/libpkgconf.pc",
    ),
    "openbox": (
        "usr/bin/openbox-*",
        "usr/lib/libobrender.so*",
        "usr/lib/libobt.so*",
        "usr/lib/openbox-*",
        "usr/share/gnome-session/sessions/openbox*",
        "usr/share/gnome/wm-properties/openbox.desktop",
        "usr/share/man/man1/openbox*.1",
        "usr/share/pixmaps/openbox.png",
        "usr/share/themes/*/openbox-3",
        "usr/share/xsessions/openbox-*.desktop",
        "usr/share/locale/*/LC_MESSAGES/openbox.mo",
        "usr/share/licenses/documentation/openbox-3.6.1",
    ),
    "openbox-devel": (
        "usr/lib/libobrender.la",
        "usr/lib/libobt.la",
    ),
    "labwc": (
        "usr/share/man/man1/labwc*.1",
        "usr/share/locale/*/LC_MESSAGES/labwc.mo",
        "usr/share/licenses/documentation/labwc*",
    ),
    "wlroots": ("usr/share/licenses/documentation/wlroots*",),
    "wlroots-devel": ("usr/share/licenses/documentation/wlroots*",),
    "libsfdo": ("usr/lib/libsfdo-*.so*",),
    "libsfdo-devel": (
        "usr/include/sfdo-*.h",
        "usr/lib/pkgconfig/libsfdo-*.pc",
    ),
    "weston": (
        "usr/bin/weston-*",
        "usr/lib/libweston-14.so*",
        "usr/lib/weston-*",
        "usr/share/man/man1/weston*.1",
        "usr/share/man/man5/weston*.5",
        "usr/share/man/man7/weston*.7",
        "usr/share/licenses/documentation/weston*",
    ),
    "weston-devel": (
        "usr/lib/pkgconfig/weston.pc",
        "usr/share/licenses/documentation/weston*",
    ),
    "seatd": (
        "usr/lib/libseat.so*",
        "usr/share/man/man1/seatd*.1",
        "usr/share/licenses/documentation/seatd*",
    ),
    "seatd-devel": ("usr/share/licenses/documentation/seatd*",),
    "wayland-devel": (
        "usr/include/wayland-*.h",
        "usr/lib/pkgconfig/wayland-*.pc",
        "usr/share/licenses/documentation/wayland-*",
    ),
    "wayland-protocols": ("usr/share/licenses/documentation/wayland-protocols*",),
    "xwayland": ("usr/share/licenses/documentation/xwayland*",),
    "xwayland-devel": ("usr/share/licenses/documentation/xwayland*",),
    "xkbcommon-tools": (
        "usr/share/man/man1/xkbcli*.1",
        "usr/share/licenses/documentation/libxkbcommon*",
    ),
    "xkbcommon-devel": ("usr/share/licenses/documentation/libxkbcommon*",),
    "openssl-cli": (
        "usr/share/man/man1/openssl*.1ssl",
        "usr/share/man/man5/openssl*.5ssl",
        "usr/share/man/man7/openssl*.7ssl",
    ),
    "xorg-devel": (
        "usr/lib/pkgconfig/libX*.pc",
        "usr/lib/pkgconfig/libxcb*.pc",
        "usr/lib/pkgconfig/x11.pc",
        "usr/lib/pkgconfig/xau.pc",
        "usr/lib/pkgconfig/xcb*.pc",
        "usr/lib/pkgconfig/xcvt.pc",
        "usr/lib/pkgconfig/xdmcp.pc",
        "usr/lib/pkgconfig/xfont2.pc",
        "usr/lib/pkgconfig/xkbfile.pc",
        "usr/lib/pkgconfig/xshmfence.pc",
        "usr/lib/pkgconfig/fontenc.pc",
        "usr/lib/pkgconfig/fontutil.pc",
        "usr/lib/pkgconfig/pciaccess.pc",
        "usr/lib/pkgconfig/ice.pc",
        "usr/lib/pkgconfig/sm.pc",
        "usr/lib/libX*.so",
        "usr/lib/libxcb*.so",
        "usr/lib/libICE.so",
        "usr/lib/libSM.so",
        "usr/lib/libfontenc.so",
        "usr/lib/libxkbfile.so",
        "usr/lib/libxcvt.so",
        "usr/lib/libxshmfence.so",
        "usr/lib/libpciaccess.so",
    ),
    "libxmu": (
        "usr/lib/libXmu.so.6*",
        "usr/lib/libXmuu.so.1*",
        "usr/share/man/man3/Xmu*.3*",
        "usr/share/man/man3/Xmuu*.3*",
        "usr/share/licenses/libxmu/COPYING",
    ),
    "libxmu-devel": (
        "usr/lib/pkgconfig/xmu.pc",
        "usr/lib/pkgconfig/xmuu.pc",
        "usr/share/licenses/libxmu-devel/COPYING",
    ),
    "libxres": (
        "usr/lib/libXRes.so.1*",
        "usr/share/man/man3/XRes*.3*",
        "usr/share/licenses/libxres/COPYING",
    ),
    "libxres-devel": (
        "usr/lib/libXRes.so",
        "usr/lib/pkgconfig/xres.pc",
        "usr/include/X11/extensions/XRes.h",
        "usr/share/licenses/libxres-devel/COPYING",
    ),
    "libxv": (
        "usr/lib/libXv.so.1*",
        "usr/share/man/man3/Xv*.3*",
        "usr/share/licenses/libxv/COPYING",
    ),
    "libxv-devel": (
        "usr/lib/libXv.so",
        "usr/lib/pkgconfig/xv.pc",
        "usr/include/X11/extensions/Xvlib.h",
        "usr/share/licenses/libxv-devel/COPYING",
    ),
    "libxcursor": (
        "usr/lib/libXcursor.so.1*",
        "usr/share/licenses/libxcursor/COPYING",
    ),
    "libxinerama": (
        "usr/lib/libXinerama.so.1*",
        "usr/share/licenses/libxinerama/COPYING",
    ),
    "libxfixes": (
        "usr/lib/libXfixes.so.3*",
        "usr/share/licenses/libxfixes/COPYING",
    ),
    "libxrandr": (
        "usr/lib/libXrandr.so.2*",
        "usr/share/licenses/libxrandr/COPYING",
    ),
    "libxrender": (
        "usr/lib/libXrender.so.1*",
        "usr/share/licenses/libxrender/COPYING",
    ),
    "libxcomposite": (
        "usr/lib/libXcomposite.so.1*",
        "usr/share/licenses/libxcomposite/COPYING",
    ),
    "libxdamage": (
        "usr/lib/libXdamage.so.1*",
        "usr/share/licenses/libxdamage/COPYING",
    ),
    "libxft": (
        "usr/lib/libXft.so.2*",
        "usr/share/licenses/libxft/COPYING",
    ),
    "fox-libs": (
        "usr/lib/libFOX-1.6.so.0*",
        "usr/lib/libCHART-1.6.so.0*",
        "usr/share/licenses/fox-libs/LICENSE",
        "usr/share/licenses/fox-libs/LICENSE_ADDENDUM",
    ),
    "fox-devel": (
        "usr/include/fox-1.6/**",
        "usr/lib/libFOX-1.6.so",
        "usr/lib/libCHART-1.6.so",
        "usr/lib/pkgconfig/fox.pc",
        "usr/bin/fox-config",
        "usr/bin/reswrap",
        "usr/share/man/man1/reswrap.1*",
        "usr/share/licenses/fox-devel/LICENSE",
        "usr/share/licenses/fox-devel/LICENSE_ADDENDUM",
    ),
    "fox-tools": (
        "usr/bin/adie",
        "usr/bin/calculator",
        "usr/bin/PathFinder",
        "usr/bin/shutterbug",
        "usr/share/man/man1/adie.1*",
        "usr/share/man/man1/calculator.1*",
        "usr/share/man/man1/PathFinder.1*",
        "usr/share/man/man1/shutterbug.1*",
        "usr/share/licenses/fox-tools/LICENSE",
    ),
    "xfe": (
        "usr/bin/xfe",
        "usr/bin/xfa",
        "usr/bin/xfi",
        "usr/bin/xfw",
        "usr/share/applications/xfe.desktop",
        "usr/share/applications/xfa.desktop",
        "usr/share/applications/xfi.desktop",
        "usr/share/applications/xfw.desktop",
        "usr/share/xfe/**",
        "usr/share/locale/*/LC_MESSAGES/xfe.mo",
        "usr/share/man/man1/xfe.1*",
        "usr/share/man/man1/xfa.1*",
        "usr/share/man/man1/xfi.1*",
        "usr/share/man/man1/xfw.1*",
        "usr/share/polkit-1/actions/org.xfe.root.policy",
        "etc/xferc",
        "usr/share/licenses/xfe/COPYING",
    ),
    "fltk-libs": (
        "usr/lib/libfltk.so.1.4*",
        "usr/lib/libfltk_forms.so.1.4*",
        "usr/lib/libfltk_images.so.1.4*",
        "usr/share/licenses/fltk-libs/COPYING",
    ),
    "fltk-devel": (
        "usr/include/FL/**",
        "usr/lib/libfltk.so",
        "usr/lib/libfltk_forms.so",
        "usr/lib/libfltk_images.so",
        "usr/lib/pkgconfig/fltk*.pc",
        "usr/lib/cmake/fltk/**",
        "usr/bin/fltk-config",
        "usr/share/licenses/fltk-devel/COPYING",
    ),
    "fltk-tools": (
        "usr/bin/fluid",
        "usr/bin/fltk-options",
        "usr/share/applications/fluid.desktop",
        "usr/share/man/man1/fluid.1*",
        "usr/share/man/man1/fltk-options.1*",
        "usr/share/licenses/fltk-tools/COPYING",
    ),
    "dillo": (
        "usr/bin/dillo",
        "usr/bin/dpid",
        "usr/bin/dillo-install-hyphenation",
        "usr/share/applications/dillo.desktop",
        "usr/share/icons/hicolor/**",
        "usr/share/pixmaps/dillo.*",
        "etc/dillo/**",
        "usr/share/dillo/**",
        "usr/share/man/man1/dillo.1*",
        "usr/lib/dillo/**",
        "usr/share/licenses/dillo/COPYING",
    ),
    "motif-libs": (
        "usr/lib/libXm.so.[0-9]*",
        "usr/lib/libMrm.so.[0-9]*",
        "usr/lib/libUil.so.[0-9]*",
        "usr/share/licenses/motif-libs/COPYING",
    ),
    "motif-devel": (
        "usr/lib/libXm.so",
        "usr/lib/libXm.a",
        "usr/lib/libMrm.so",
        "usr/lib/libMrm.a",
        "usr/lib/libUil.so",
        "usr/lib/libUil.a",
        "usr/lib/pkgconfig/motif*.pc",
        "usr/share/licenses/motif-devel/COPYING",
    ),
    "motif-tools": (
        "usr/lib/X11/mwm/**",
        "usr/share/man/man1/mwm.1*",
        "usr/share/man/man1/uil.1*",
        "usr/share/licenses/motif-tools/COPYING",
    ),
    "nedit": (
        "usr/share/doc/nedit/**",
        "usr/share/man/man1/nedit.1*",
        "usr/share/man/man1/nedit-client.1*",
    ),
    "xorg-font-encodings": (
        "usr/share/fonts/encodings/**",
        "usr/share/licenses/xorg-font-encodings/COPYING",
    ),
    "mesa-devel": (
        "usr/lib/pkgconfig/egl.pc",
        "usr/lib/pkgconfig/gbm.pc",
        "usr/lib/pkgconfig/gl.pc",
        "usr/lib/pkgconfig/glx.pc",
        "usr/lib/pkgconfig/glesv1_cm.pc",
        "usr/lib/pkgconfig/glesv2.pc",
        "usr/lib/libEGL.so",
        "usr/lib/libGL.so",
        "usr/lib/libGLESv1_CM.so",
        "usr/lib/libGLESv2.so",
        "usr/lib/libgbm.so",
    ),
    "cairo-devel": (
        "usr/lib/pkgconfig/cairo*.pc",
        "usr/lib/libcairo*.so",
    ),
    "harfbuzz-devel": (
        "usr/lib/pkgconfig/harfbuzz*.pc",
        "usr/lib/libharfbuzz*.so",
    ),
    "libwebp-devel": (
        "usr/lib/pkgconfig/libwebp*.pc",
        "usr/lib/libwebp*.so",
    ),
    "pcre2-devel": (
        "usr/lib/pkgconfig/libpcre2*.pc",
        "usr/lib/libpcre2*.so",
    ),
    "libdrm-devel": (
        "usr/lib/pkgconfig/libdrm*.pc",
        "usr/lib/libdrm*.so",
    ),
    "libevent-devel": (
        "usr/lib/pkgconfig/libevent*.pc",
        "usr/lib/libevent*.so",
    ),
    "lz4-devel": ("usr/lib/pkgconfig/lz4.pc",),
    "glib-devel": (
        "usr/lib/pkgconfig/glib-2.0.pc",
        "usr/lib/pkgconfig/gio-2.0.pc",
        "usr/lib/pkgconfig/gio-unix-2.0.pc",
        "usr/lib/pkgconfig/gobject-2.0.pc",
        "usr/lib/pkgconfig/gmodule-2.0.pc",
        "usr/lib/pkgconfig/gmodule-export-2.0.pc",
        "usr/lib/pkgconfig/gmodule-no-export-2.0.pc",
        "usr/lib/pkgconfig/gthread-2.0.pc",
        "usr/lib/libgio-2.0.so",
        "usr/lib/libglib-2.0.so",
        "usr/lib/libgobject-2.0.so",
        "usr/lib/libgmodule-2.0.so",
        "usr/lib/libgthread-2.0.so",
    ),
    "gtk3-devel": (
        "usr/lib/pkgconfig/gtk+-3.0.pc",
        "usr/lib/pkgconfig/gtk+-unix-print-3.0.pc",
        "usr/lib/pkgconfig/gtk+-x11-3.0.pc",
        "usr/lib/pkgconfig/gtk+-wayland-3.0.pc",
        "usr/lib/pkgconfig/gdk-3.0.pc",
        "usr/lib/pkgconfig/gdk-x11-3.0.pc",
        "usr/lib/pkgconfig/gdk-wayland-3.0.pc",
        "usr/lib/libgtk-3.so",
        "usr/lib/libgdk-3.so",
        "usr/lib/libgailutil-3.so",
    ),
    "pango-devel": (
        "usr/lib/pkgconfig/pango*.pc",
        "usr/lib/libpango*.so",
    ),
    "ncurses-devel": (
        "usr/lib/pkgconfig/ncurses*.pc",
        "usr/lib/pkgconfig/form*.pc",
        "usr/lib/pkgconfig/menu*.pc",
        "usr/lib/pkgconfig/panel*.pc",
        "usr/lib/pkgconfig/tinfo.pc",
        "usr/lib/libncurses*.so",
        "usr/lib/libform*.so",
        "usr/lib/libmenu*.so",
        "usr/lib/libpanel*.so",
        "usr/lib/libtinfo.so",
        "usr/lib/libcurses.so",
    ),
    "util-linux-devel": (
        "usr/lib/pkgconfig/uuid.pc",
        "usr/lib/pkgconfig/blkid.pc",
        "usr/lib/pkgconfig/mount.pc",
        "usr/lib/pkgconfig/fdisk.pc",
        "usr/lib/pkgconfig/smartcols.pc",
        "usr/lib/libuuid.so",
        "usr/lib/libblkid.so",
        "usr/lib/libmount.so",
        "usr/lib/libfdisk.so",
        "usr/lib/libsmartcols.so",
    ),
    "libunistring-devel": ("usr/include/uni*.h",),
    "rustc": (
        "usr/bin/rust-gdb*",
        "usr/bin/rust-lldb*",
        "usr/share/man/man1/rustc*.1",
        "usr/share/man/man1/rustdoc*.1",
    ),
    "cargo": (
        "usr/share/bash-completion/completions/cargo",
        "usr/share/zsh/site-functions/_cargo",
        "usr/share/fish/vendor_completions.d/cargo.fish",
        "usr/share/man/man1/cargo*.1",
    ),
    "binutils": (
        "usr/bin/objcopy-*",
        "usr/bin/objdump-*",
        "usr/bin/ranlib-*",
        "usr/bin/readelf-*",
        "usr/lib/libbfd*.so*",
        "usr/lib/libopcodes*.so*",
        "usr/lib/libsframe.so*",
        "usr/lib/libctf*.so*",
        "usr/share/man/man1/addr2line*.1",
        "usr/share/man/man1/ar*.1",
        "usr/share/man/man1/as*.1",
        "usr/share/man/man1/ld*.1",
        "usr/share/man/man1/nm*.1",
        "usr/share/man/man1/objcopy*.1",
        "usr/share/man/man1/objdump*.1",
        "usr/share/man/man1/readelf*.1",
        "usr/share/man/man1/strip*.1",
    ),
    "gcc": (
        "usr/bin/gcc-*",
        "usr/bin/cpp-*",
    ),
    "gcc-libs": (
        "usr/share/info/gcc*",
        "usr/share/man/man7/gcc*.7",
    ),
    "gcc-cxx": (
        "usr/bin/g++-*",
        "usr/bin/c++-*",
        "usr/share/man/man1/g++*.1",
    ),
    "gcc-tools": (
        "usr/bin/gcov*",
        "usr/bin/lto-dump*",
        "usr/share/man/man1/gcov*.1",
    ),
    "cmake": (
        "usr/bin/cmake-gui",
        "usr/share/man/man1/cmake*.1",
        "usr/share/man/man1/ccmake*.1",
        "usr/share/man/man1/cpack*.1",
        "usr/share/man/man1/ctest*.1",
    ),
    "autoconf": (
        "usr/bin/autoconf-*",
        "usr/bin/autoheader-*",
        "usr/bin/autom4te-*",
        "usr/bin/autoreconf-*",
        "usr/bin/autoscan-*",
        "usr/bin/autoupdate-*",
        "usr/share/man/man1/autoconf*.1",
        "usr/share/man/man1/autoheader*.1",
        "usr/share/man/man1/autom4te*.1",
        "usr/share/man/man1/autoreconf*.1",
    ),
    "automake": (
        "usr/bin/automake-*",
        "usr/bin/aclocal*",
        "usr/share/man/man1/automake*.1",
        "usr/share/man/man1/aclocal*.1",
    ),
    "bison": (
        "usr/bin/bison-*",
        "usr/share/man/man1/bison*.1",
    ),
    "flex": (
        "usr/bin/flex-*",
        "usr/share/man/man1/flex*.1",
    ),
    "m4": (
        "usr/bin/m4-*",
        "usr/share/man/man1/m4*.1",
    ),
    "feh": (
        "usr/share/man/man1/feh*.1",
        "usr/share/doc/feh",
        "usr/share/icons/hicolor/*/apps/feh*",
    ),
    "gettext-tools": (
        "usr/bin/autopoint",
        "usr/bin/envsubst",
        "usr/bin/recode-sr-latin",
        "usr/share/aclocal/gettext.m4",
        "usr/share/man/man1/gettext*.1",
        "usr/share/man/man1/msg*.1",
        "usr/share/man/man1/ngettext*.1",
        "usr/share/man/man1/xgettext*.1",
    ),
    "fontconfig-tools": (
        "usr/bin/fc-conflist",
        "usr/share/man/man1/fc-*.1",
    ),
    "gdk-pixbuf-tools": ("usr/share/man/man1/gdk-pixbuf*.1",),
    "gtk3-tools": ("usr/share/man/man1/gtk-update-icon-cache*.1",),
    "ncurses-tools": (
        "usr/share/man/man1/infocmp*.1",
        "usr/share/man/man1/tic*.1",
        "usr/share/man/man1/toe*.1",
        "usr/share/man/man1/tput*.1",
        "usr/share/man/man1/clear*.1",
    ),
    "sqlite-tools": ("usr/share/man/man1/sqlite3*.1",),
    "curl-cli": ("usr/share/man/man1/curl*.1",),
    "patch": ("usr/share/man/man1/patch*.1",),
    "less": (
        "usr/share/man/man1/less*.1",
        "usr/share/man/man1/lesskey*.1",
    ),
    "rsync": (
        "usr/bin/rsync-ssl",
        "usr/share/man/man1/rsync*.1",
        "usr/share/man/man5/rsync*.5",
        "usr/share/man/man7/rsync*.7",
    ),
    "wget": ("usr/share/man/man1/wget*.1",),
    "xcalc": (
        "usr/share/man/man1/xcalc*.1",
        "usr/share/X11/app-defaults/XCalc*",
        "usr/share/applications/xcalc.desktop",
    ),
    "xclock": (
        "usr/share/man/man1/xclock*.1",
        "usr/share/X11/app-defaults/XClock*",
        "usr/share/applications/xclock.desktop",
    ),
    "xedit": (
        "usr/share/man/man1/xedit*.1",
        "usr/share/X11/app-defaults/Xedit*",
        "usr/lib/X11/xedit",
        "usr/share/applications/xedit.desktop",
    ),
    "xeyes": (
        "usr/share/man/man1/xeyes*.1",
        "usr/share/X11/app-defaults/XEyes*",
        "usr/share/applications/xeyes.desktop",
    ),
    "xload": (
        "usr/share/man/man1/xload*.1",
        "usr/share/X11/app-defaults/XLoad*",
        "usr/share/applications/xload.desktop",
    ),
    "xlogo": (
        "usr/share/man/man1/xlogo*.1",
        "usr/share/X11/app-defaults/XLogo*",
        "usr/share/applications/xlogo.desktop",
    ),
    "xmag": (
        "usr/share/man/man1/xmag*.1",
        "usr/share/X11/app-defaults/XMag*",
        "usr/share/applications/xmag.desktop",
    ),
    "xman": (
        "usr/share/man/man1/xman*.1",
        "usr/share/X11/app-defaults/Xman*",
        "usr/share/applications/xman.desktop",
    ),
    "xmessage": (
        "usr/share/man/man1/xmessage*.1",
        "usr/share/X11/app-defaults/Xmessage*",
        "usr/share/applications/xmessage.desktop",
    ),
    "oclock": (
        "usr/share/man/man1/oclock*.1",
        "usr/share/X11/app-defaults/Clock*",
        "usr/share/applications/oclock.desktop",
    ),
    "xbiff": (
        "usr/share/man/man1/xbiff*.1",
        "usr/share/applications/xbiff.desktop",
    ),
    "xclipboard": (
        "usr/share/man/man1/xclipboard*.1",
        "usr/share/X11/app-defaults/XClipboard*",
        "usr/share/applications/xclipboard.desktop",
    ),
    "xconsole": (
        "usr/share/man/man1/xconsole*.1",
        "usr/share/X11/app-defaults/XConsole*",
        "usr/share/applications/xconsole.desktop",
    ),
    "xditview": (
        "usr/share/man/man1/xditview*.1",
        "usr/share/X11/app-defaults/Xditview*",
        "usr/share/applications/xditview.desktop",
    ),
    "xev": (
        "usr/share/man/man1/xev*.1",
        "usr/share/applications/xev.desktop",
    ),
    "xfontsel": (
        "usr/share/man/man1/xfontsel*.1",
        "usr/share/X11/app-defaults/XFontSel*",
        "usr/share/applications/xfontsel.desktop",
    ),
    "xgc": (
        "usr/share/man/man1/xgc*.1",
        "usr/share/X11/app-defaults/Xgc*",
        "usr/share/applications/xgc.desktop",
    ),
    "xkill": (
        "usr/share/man/man1/xkill*.1",
        "usr/share/applications/xkill.desktop",
    ),
    "xmore": (
        "usr/share/man/man1/xmore*.1",
        "usr/share/X11/app-defaults/XMore*",
        "usr/share/applications/xmore.desktop",
    ),
    "xpr": ("usr/share/man/man1/xpr*.1",),
    "xsm": (
        "usr/share/man/man1/xsm*.1",
        "usr/share/X11/app-defaults/XSm*",
        "usr/share/applications/xsm.desktop",
    ),
    "xwd": ("usr/share/man/man1/xwd*.1",),
    "xwud": ("usr/share/man/man1/xwud*.1",),
    "xwininfo": ("usr/share/man/man1/xwininfo*.1",),
    "smproxy": ("usr/share/man/man1/smproxy*.1",),
    "x11perf": (
        "usr/bin/x11perfcomp",
        "usr/lib/X11/x11perfcomp",
        "usr/share/man/man1/x11perf*.1",
    ),
    "xdriinfo": ("usr/share/man/man1/xdriinfo*.1",),
    "xrestop": ("usr/share/man/man1/xrestop*.1",),
    "xvinfo": ("usr/share/man/man1/xvinfo*.1",),
    "xosview": (
        "usr/share/man/man1/xosview2*.1",
        "usr/share/X11/app-defaults/XOsview2",
        "usr/share/doc/xosview2/*",
        "usr/share/licenses/xosview/COPYING.GPL",
        "usr/share/applications/xosview.desktop",
    ),
    "iceauth": ("usr/share/man/man1/iceauth*.1",),
    "xfd": (
        "usr/share/man/man1/xfd*.1",
        "usr/share/X11/app-defaults/Xfd*",
        "usr/share/applications/xfd.desktop",
    ),
    "xauth": ("usr/share/man/man1/xauth*.1",),
    "ico": (
        "usr/share/man/man1/ico*.1",
        "usr/share/applications/ico.desktop",
    ),
    "xbacklight": ("usr/share/man/man1/xbacklight*.1",),
    "xgamma": ("usr/share/man/man1/xgamma*.1",),
    "xhost": ("usr/share/man/man1/xhost*.1",),
    "xinput": ("usr/share/man/man1/xinput*.1",),
    "xmodmap": ("usr/share/man/man1/xmodmap*.1",),
    "xprop": ("usr/share/man/man1/xprop*.1",),
    "xrandr": (
        "usr/bin/xkeystone",
        "usr/share/man/man1/xrandr*.1",
        "usr/share/man/man1/xkeystone*.1",
    ),
    "xrefresh": ("usr/share/man/man1/xrefresh*.1",),
    "xset": ("usr/share/man/man1/xset.1",),
    "xsetroot": ("usr/share/man/man1/xsetroot*.1",),
    "xinit": (
        "usr/bin/startx",
        "etc/X11/xinit/*",
        "usr/share/man/man1/xinit*.1",
        "usr/share/man/man1/startx*.1",
    ),
    "xdpyinfo": ("usr/share/man/man1/xdpyinfo*.1",),
    "xlsatoms": ("usr/share/man/man1/xlsatoms*.1",),
    "xlsclients": ("usr/share/man/man1/xlsclients*.1",),
    "xscope": ("usr/share/man/man1/xscope*.1",),
    "xkbutils": (
        "usr/share/man/man1/xkbbell*.1",
        "usr/share/man/man1/xkbvleds*.1",
        "usr/share/man/man1/xkbwatch*.1",
    ),
    "appres": ("usr/share/man/man1/appres*.1",),
    "listres": ("usr/share/man/man1/listres*.1",),
    "sessreg": ("usr/share/man/man1/sessreg*.1",),
    "setxkbmap": ("usr/share/man/man1/setxkbmap*.1",),
    "transset": ("usr/share/man/man1/transset*.1",),
    "xcmsdb": ("usr/share/man/man1/xcmsdb*.1",),
    "xcompmgr": ("usr/share/man/man1/xcompmgr*.1",),
    "xcursorgen": ("usr/share/man/man1/xcursorgen*.1",),
    "xkbcomp": ("usr/share/man/man1/xkbcomp*.1",),
    "xkbevd": ("usr/share/man/man1/xkbevd*.1",),
    "xkbprint": ("usr/share/man/man1/xkbprint*.1",),
    "xlsfonts": ("usr/share/man/man1/xlsfonts*.1",),
    "xrdb": ("usr/share/man/man1/xrdb*.1",),
    "xstdcmap": ("usr/share/man/man1/xstdcmap*.1",),
    "xvidtune": (
        "usr/share/man/man1/xvidtune*.1",
        "usr/share/X11/app-defaults/Xvidtune*",
    ),
    "bitmap": (
        "usr/share/man/man1/bitmap*.1",
        "usr/share/man/man1/bmtoa*.1",
        "usr/share/man/man1/atobm*.1",
        "usr/share/X11/app-defaults/Bitmap*",
        "usr/share/applications/bitmap.desktop",
    ),
    "fonttosfnt": ("usr/share/man/man1/fonttosfnt*.1",),
    "mkfontscale": (
        "usr/bin/mkfontdir",
        "usr/share/man/man1/mkfontscale*.1",
        "usr/share/man/man1/mkfontdir*.1",
    ),
    "viewres": (
        "usr/share/man/man1/viewres*.1",
        "usr/share/X11/app-defaults/Viewres*",
        "usr/share/applications/viewres.desktop",
    ),
    "luit": ("usr/share/man/man1/luit*.1",),
    "xterm": (
        "usr/share/man/man1/koi8rxterm*.1",
        "usr/share/man/man1/resize*.1",
        "usr/share/man/man1/uxterm*.1",
        "usr/share/man/man1/xterm*.1",
        "usr/share/pixmaps/*xterm*.xpm",
    ),
    "xpdf-tools": (
        "usr/share/man/man1/pdf*.1",
        "usr/share/man/man5/xpdfrc.5",
    ),
    "xcb-util": (
        "usr/lib/libxcb-util.so*",
        "usr/lib/pkgconfig/xcb-atom.pc",
        "usr/lib/pkgconfig/xcb-aux.pc",
        "usr/lib/pkgconfig/xcb-event.pc",
        "usr/lib/pkgconfig/xcb-util.pc",
    ),
    "librsvg-devel": ("usr/lib/librsvg-2.so*",),
    "perl": (
        "usr/bin/cpan",
        "usr/bin/corelist",
        "usr/bin/enc2xs",
        "usr/bin/h2ph",
        "usr/bin/h2xs",
        "usr/bin/instmodsh",
        "usr/bin/json_pp",
        "usr/bin/libnetcfg",
        "usr/bin/perl*",
        "usr/bin/pod*",
    ),
    "fvwm3": (
        "usr/bin/fvwm*",
        "usr/share/locale/*/LC_MESSAGES/fvwm*.mo",
        "usr/share/pixmaps/fvwm*",
    ),
    "nscde": (
        "usr/share/applications/nscde-*.desktop",
        "usr/share/desktop-directories/nscde-*.directory",
    ),
    "glib-tools": (
        "usr/share/man/man1/gapplication*.1",
        "usr/share/man/man1/gdbus*.1",
        "usr/share/man/man1/gio*.1",
        "usr/share/man/man1/glib-*.1",
        "usr/share/man/man1/gobject-query*.1",
        "usr/share/man/man1/gsettings*.1",
        "usr/share/man/man1/gtester*.1",
    ),
    "pango-tools": ("usr/share/man/man1/pango-view*.1",),
    "cairo-tools": ("usr/share/man/man1/cairo-trace*.1",),
    "harfbuzz-tools": ("usr/share/man/man1/hb-*.1",),
    "bzip2-tools": (
        "usr/bin/bunzip2",
        "usr/bin/bz*",
        "usr/share/licenses/documentation/bzip2*",
    ),
    "xz-tools": (
        "usr/bin/lzcat",
        "usr/bin/lzma*",
        "usr/bin/unlzma",
        "usr/bin/unxz",
        "usr/bin/xz*",
        "usr/share/licenses/documentation/xz-5.8.1",
    ),
    "zstd-tools": (
        "usr/bin/unzstd",
        "usr/bin/zstd*",
    ),
    "lz4-tools": (
        "usr/bin/lz4*",
        "usr/bin/unlz4",
    ),
    "libarchive-tools": (
        "usr/bin/bsdcat",
        "usr/bin/bsdcpio",
        "usr/bin/bsdunzip",
    ),
    "e2fsprogs": (
        "usr/lib/libcom_err.so.2*",
        "usr/lib/libe2p.so*",
        "usr/lib/libext2fs.so*",
        "usr/lib/libss.so*",
    ),
    "grub": (
        "usr/bin/grub*",
        "usr/sbin/grub*",
        "usr/share/locale/*/LC_MESSAGES/grub.mo",
    ),
    "procps-ng": (
        "usr/lib/libproc2.so.1*",
        "usr/lib/sysctl.d/50-default.conf",
    ),
    "iputils": ("usr/share/iputils/*",),
    "iptables": (
        "usr/lib/libip4tc.so*",
        "usr/lib/libip6tc.so*",
        "usr/lib/libipq.so*",
        "usr/lib/libxtables.so*",
    ),
    "libnfnetlink": ("usr/lib/libnfnetlink.so.0*",),
    "libndp": ("usr/lib/libndp.so.0*",),
    "libmnl": ("usr/lib/libmnl.so.0*",),
    "networkmanager": (
        "usr/lib/libnm.so.0*",
        "usr/lib/systemd/system/NetworkManager-*.service",
        "usr/lib/udev/rules.d/90-nm-*.rules",
        "usr/share/locale/*/LC_MESSAGES/NetworkManager.mo",
    ),
    "findutils": (
        "usr/lib/findutils",
        "usr/libexec/findutils",
        "usr/share/bash-completion/completions/locate",
    ),
    "grep": ("usr/share/locale/*/LC_MESSAGES/grep.mo",),
    "gawk": (
        "usr/lib/gawk",
        "usr/share/awk",
        "usr/share/locale/*/LC_MESSAGES/gawk.mo",
    ),
    "nano": ("usr/share/locale/*/LC_MESSAGES/nano.mo",),
    "sudo": (
        "usr/share/bash-completion/completions/sudo",
        "usr/share/zsh/site-functions/_sudo",
    ),
    "kmod-libs": ("usr/lib/libkmod.so.2*",),
    "kmod-tools": (
        "usr/share/bash-completion/completions/kmod",
        "usr/share/locale/*/LC_MESSAGES/kmod.mo",
    ),
    "libpci": ("usr/lib/libpci.so.3*",),
    "systemd-libs": (
        "usr/lib/systemd/libsystemd-core-*.so",
        "usr/lib/systemd/libsystemd-shared-*.so",
    ),
    "systemd-tools": (
        "usr/share/bash-completion/completions/systemd-*",
        "usr/share/bash-completion/completions/bootctl",
        "usr/share/bash-completion/completions/journalctl",
        "usr/share/bash-completion/completions/loginctl",
        "usr/share/bash-completion/completions/systemctl",
    ),
    "util-linux-libs": (
        "usr/lib/libblkid.so.*",
        "usr/lib/libfdisk.so.*",
        "usr/lib/libmount.so.*",
        "usr/lib/libsmartcols.so.*",
        "usr/lib/libuuid.so.*",
    ),
    "device-mapper": (
        "usr/lib/libdevmapper.so.1*",
        "usr/lib/udev/rules.d/10-dm.rules",
        "usr/lib/udev/rules.d/13-dm-disk.rules",
        "usr/lib/udev/rules.d/95-dm-notify.rules",
    ),
    "lvm2": (
        "usr/bin/lv*",
        "usr/bin/pv*",
        "usr/bin/vg*",
        "usr/lib/liblvm2cmd.so*",
        "usr/lib/systemd/system/lvm2*",
        "usr/lib/systemd/system-generators/lvm2*",
    ),
    "audit-libs": (
        "usr/lib/libaudit.so.1*",
        "usr/lib/libauparse.so.0*",
    ),
    "libaio": ("usr/lib/libaio.so.1*",),
    "libnvme": ("usr/lib/libnvme.so.1*",),
    "acl-libs": ("usr/lib/libacl.so.1*",),
    "alsa-libs": (
        "usr/lib/libasound.so.2*",
        "usr/lib/libatopology.so.2*",
    ),
    "attr-libs": ("usr/lib/libattr.so.1*",),
    "brotli-libs": (
        "usr/lib/libbrotlicommon.so.1*",
        "usr/lib/libbrotlidec.so.1*",
        "usr/lib/libbrotlienc.so.1*",
    ),
    "brotli-tools": (),
    "cyrus-sasl-libs": ("usr/lib/libsasl2.so.3*",),
    "cyrus-sasl-plugins": ("usr/lib/sasl2",),
    "file": (),
    "giflib": ("usr/lib/libgif.so.7*",),
    "giflib-devel": (),
    "giflib-tools": (),
    "gmp-libs": (
        "usr/lib/libgmp.so.10*",
        "usr/lib/libgmpxx.so.4*",
    ),
    "gnutls-libs": (
        "usr/lib/libgnutls.so.30*",
        "usr/lib/libgnutlsxx.so.30*",
    ),
    "gnutls-tools": (
        "usr/bin/gnutls*",
        "usr/bin/certtool",
        "usr/bin/psktool",
        "usr/bin/danetool",
    ),
    "guile": (
        "usr/bin/guile*",
        "usr/bin/guild*",
    ),
    "ksh93": (),
    "krb5-libs": (
        "usr/lib/libgssapi_krb5.so.*",
        "usr/lib/libk5crypto.so.*",
        "usr/lib/libkadm5clnt_mit.so.*",
        "usr/lib/libkadm5srv_mit.so.*",
        "usr/lib/libkdb5.so.*",
        "usr/lib/libkrb5.so.*",
        "usr/lib/libkrb5support.so.*",
        "usr/lib/krb5",
    ),
    "krb5-tools": (
        "usr/bin/gss-client",
        "usr/bin/gss-server",
        "usr/bin/kdb5_util",
        "usr/bin/sclient",
        "usr/bin/sserver",
        "usr/bin/kvno",
    ),
    "libbsd": ("usr/lib/libbsd.so.0*",),
    "libbsd-devel": (),
    "libcap": (
        "usr/lib/libcap.so.2*",
        "usr/lib/libpsx.so.2*",
    ),
    "libcap-ng": ("usr/lib/libcap-ng.so.0*",),
    "libcap-tools": (),
    "libffi-libs": ("usr/lib/libffi.so.8*",),
    "libgc": (
        "usr/lib/libgc.so.1*",
        "usr/lib/libcord.so.1*",
        "usr/lib/libgccpp.so.1*",
        "usr/lib/libgctba.so.1*",
    ),
    "libidn2-libs": ("usr/lib/libidn2.so.0*",),
    "libltdl": ("usr/lib/libltdl.so.7*",),
    "libmagic": ("usr/lib/libmagic.so.1*",),
    "libmd": ("usr/lib/libmd.so.0*",),
    "libmd-devel": (),
    "libsensors": ("usr/lib/libsensors.so.5*",),
    "libsensors-devel": (),
    "lm-sensors": (),
    "lmdb-libs": (),
    "lmdb-devel": (),
    "lmdb-tools": (),
    "mpfr-libs": ("usr/lib/libmpfr.so.6*",),
    "ncurses-libs": (
        "usr/lib/libncurses.so.6*",
        "usr/lib/libncursesw.so.6*",
        "usr/lib/libform.so.6*",
        "usr/lib/libformw.so.6*",
        "usr/lib/libmenu.so.6*",
        "usr/lib/libmenuw.so.6*",
        "usr/lib/libpanel.so.6*",
        "usr/lib/libpanelw.so.6*",
        "usr/lib/libtinfo.so.6*",
        "usr/lib/libtic.so.6*",
    ),
    "nettle-libs": (
        "usr/lib/libnettle.so.8*",
        "usr/lib/libhogweed.so.6*",
    ),
    "openldap-libs": (
        "usr/lib/libldap*.so.2*",
        "usr/lib/liblber.so.2*",
        "usr/lib/openldap",
    ),
    "openldap-tools": (),
    "openssl-libs": (
        "usr/lib/libcrypto.so.3*",
        "usr/lib/libssl.so.3*",
        "usr/lib/engines-3",
        "usr/lib/ossl-modules",
    ),
    "p11-kit-libs": (
        "usr/lib/libp11-kit.so.0*",
        "usr/lib/p11-kit-proxy.so",
        "usr/lib/pkcs11/p11-kit-trust.so",
    ),
    "pam-libs": (
        "usr/lib/libpam.so.0*",
        "usr/lib/libpam_misc.so.0*",
        "usr/lib/libpamc.so.0*",
        "usr/lib/security",
    ),
    "pcre2-libs": ("usr/lib/libpcre2-*.so.*",),
    "popt-libs": ("usr/lib/libpopt.so.0*",),
    "popt-devel": (),
    "readline-libs": (
        "usr/lib/libreadline.so.8*",
        "usr/lib/libhistory.so.8*",
    ),
    "libtasn1-libs": ("usr/lib/libtasn1.so.6*",),
    "libunistring-libs": ("usr/lib/libunistring.so.5*",),
}


class PackageTree:
    def __init__(self, staging: Path, package_root: Path) -> None:
        self.staging = staging
        self.package_root = package_root
        self.hardlinks: dict[tuple[int, int], Path] = {}
        self.excluded_paths: set[str] = set()

    def add(self, relative: str | Path, *, required: bool = True) -> None:
        relative_path = Path(relative)
        if relative_path.as_posix() in self.excluded_paths:
            return
        source = self.staging / relative_path
        destination = self.package_root / relative_path
        if not source.exists() and not source.is_symlink():
            if required:
                raise FileNotFoundError(f"missing staged package input: {source}")
            return
        if destination.exists() or destination.is_symlink():
            return
        destination.parent.mkdir(parents=True, exist_ok=True)

        if source.is_symlink():
            destination.symlink_to(os.readlink(source))
        elif source.is_dir():
            destination.mkdir()
            for child in sorted(source.iterdir(), key=lambda item: item.name):
                self.add(child.relative_to(self.staging))
            shutil.copystat(source, destination, follow_symlinks=False)
        elif source.is_file():
            stat = source.stat()
            inode = (stat.st_dev, stat.st_ino)
            if stat.st_nlink > 1 and inode in self.hardlinks:
                target = os.path.relpath(self.hardlinks[inode], destination.parent)
                destination.symlink_to(target)
            else:
                shutil.copy2(source, destination)
                if stat.st_nlink > 1:
                    self.hardlinks[inode] = destination
        else:
            raise ValueError(f"unsupported staged package input: {source}")

    def add_glob(self, pattern: str) -> None:
        for source in sorted(self.staging.glob(pattern)):
            self.add(source.relative_to(self.staging), required=False)


def read_field(recipe: Path, name: str) -> str:
    for line in recipe.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == name:
            return value.strip()
    raise ValueError(f"{recipe} has no {name} field")


def sha512_file(path: Path) -> str:
    digest = hashlib.sha512()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def obtain_firefox_archive(archive_path: Path | None, temporary_dir: Path) -> Path:
    if archive_path is None:
        archive_path = temporary_dir / f"firefox-{FIREFOX_VERSION}.tar.xz"
        request = urllib.request.Request(
            FIREFOX_URL, headers={"User-Agent": "arkpkg-repo-package-builder/1"}
        )
        with (
            urllib.request.urlopen(request, timeout=120) as response,
            archive_path.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)
    else:
        archive_path = archive_path.resolve()

    if archive_path.stat().st_size != FIREFOX_ARCHIVE_BYTES:
        raise ValueError(
            f"Firefox archive has unexpected size: {archive_path.stat().st_size}"
        )
    if sha512_file(archive_path) != FIREFOX_SHA512:
        raise ValueError(
            "Firefox archive SHA-512 does not match Mozilla's release checksum"
        )
    return archive_path


def add_firefox_payload(package_root: Path, staging: Path, archive_path: Path) -> None:
    tree = PackageTree(staging, package_root)
    bundle = package_root / "usr/lib/arkpkg/firefox-158.0.tar.xz"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archive_path, bundle)
    os.chmod(bundle, 0o644)

    launcher = Path(__file__).resolve().parent / "payloads/firefox"
    launcher_destination = package_root / "usr/bin/firefox"
    launcher_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(launcher, launcher_destination)
    os.chmod(launcher_destination, 0o755)

    desktop = Path(__file__).resolve().parent / "payloads/firefox.desktop"
    desktop_destination = package_root / "usr/share/applications/firefox.desktop"
    desktop_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(desktop, desktop_destination)
    os.chmod(desktop_destination, 0o644)

    icon_destination = package_root / "usr/share/icons/hicolor/128x128/apps/firefox.png"
    icon_destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, mode="r:xz") as archive:
        member = archive.extractfile(FIREFOX_ICON)
        if member is None:
            raise ValueError(f"Firefox release is missing its icon: {FIREFOX_ICON}")
        with icon_destination.open("wb") as output:
            shutil.copyfileobj(member, output)
    os.chmod(icon_destination, 0o644)

    tree.add("usr/share/NsCDE/integration/firefox")


def add_staged_payload(name: str, package_root: Path, staging: Path) -> None:
    tree = PackageTree(staging, package_root)
    if name == "arkcfg":
        tree.add("usr/bin/arkcfg")
        (package_root / "usr/bin/arkcfg").chmod(0o755)
    elif name == "arkpkg":
        tree.add("usr/bin/arkpkg")
        tree.add("usr/bin/arkpkg-build")
        tree.add("etc/arkpkg/repos.d/arkanaos.json", required=False)
    elif name == "fastfetch":
        for relative in (
            "usr/bin/fastfetch",
            "usr/share/fastfetch",
            "usr/share/licenses/fastfetch",
            "usr/share/man/man1/fastfetch.1",
            "usr/share/bash-completion/completions/fastfetch",
            "usr/share/zsh/site-functions/_fastfetch",
            "usr/share/fish/vendor_completions.d/fastfetch.fish",
        ):
            tree.add(
                relative,
                required=relative
                in {
                    "usr/bin/fastfetch",
                    "usr/share/fastfetch",
                },
            )
        (package_root / "usr/bin/fastfetch").chmod(0o755)
    elif name == "git":
        for relative in (
            "usr/lib/git-core",
            "usr/share/git-core",
            "usr/share/bash-completion/completions/git",
            "usr/share/zsh/site-functions/_git",
            "usr/share/fish/vendor_completions.d/git.fish",
        ):
            tree.add(relative, required=relative in {"usr/lib/git-core"})
        for pattern in (
            "usr/bin/git*",
            "usr/share/man/man1/git*",
            "usr/share/man/man5/git*",
            "usr/share/man/man7/git*",
            "usr/share/doc/git*",
        ):
            tree.add_glob(pattern)
        if not (package_root / "usr/bin/git").is_file():
            raise FileNotFoundError("Git package has no /usr/bin/git executable")
    elif name == "vim":
        for relative in (
            "usr/bin/vim",
            "usr/bin/vimdiff",
            "usr/bin/vimtutor",
            "usr/bin/ex",
            "usr/bin/view",
            "usr/bin/rvim",
            "usr/bin/rview",
            "usr/share/vim",
            "usr/share/doc/vim-9.1.1629",
        ):
            tree.add(
                relative,
                required=relative
                in {
                    "usr/bin/vim",
                    "usr/share/vim",
                },
            )
        for relative in (
            "usr/share/man/man1/vim.1",
            "usr/share/man/man1/vimdiff.1",
            "usr/share/man/man1/vimtutor.1",
        ):
            tree.add(relative, required=False)
        (package_root / "usr/bin/vim").chmod(0o755)
        vi = package_root / "usr/bin/vi"
        vi.symlink_to("vim")
    elif name == "gcc":
        for relative in STAGED_PACKAGE_FILES[name]:
            tree.add(relative)
        for pattern in STAGED_PACKAGE_GLOBS.get(name, ()):
            tree.add_glob(pattern)
    elif name == "gcc-libs":
        excluded = {
            "cc1",
            "cc1plus",
            "lto1",
            "lto-dump",
            "lto-wrapper",
            "collect2",
        }
        source_root = staging / "usr/lib/gcc"
        for source in sorted(source_root.rglob("*")):
            if source.is_dir() and not source.is_symlink():
                continue
            if source.name in excluded and "15.2.0" in source.parts:
                continue
            tree.add(source.relative_to(staging))
        for relative in STAGED_PACKAGE_FILES[name][1:]:
            tree.add(relative)
        for pattern in STAGED_PACKAGE_GLOBS.get(name, ()):
            tree.add_glob(pattern)
        exec_path = package_root / "usr/libexec/gcc"
        exec_path.parent.mkdir(parents=True, exist_ok=True)
        exec_path.symlink_to("../lib/gcc")
    elif name in {"gcc-c", "gcc-cxx", "gcc-tools"}:
        for relative in STAGED_PACKAGE_FILES[name]:
            tree.add(relative)
        for pattern in STAGED_PACKAGE_GLOBS.get(name, ()):
            tree.add_glob(pattern)
        if name == "gcc-tools":
            lto_dump = package_root / "usr/lib/gcc/x86_64-pc-linux-gnu/15.2.0/lto-dump"
            lto_dump.parent.mkdir(parents=True, exist_ok=True)
            lto_dump.symlink_to("../../../../bin/lto-dump")
    elif name == "system-docs":
        repo_packages = Path(__file__).resolve().parents[1] / "packages"
        claimed: set[str] = set()
        doc_roots = ("usr/share/man", "usr/share/info", "usr/share/doc")
        for archive_path in sorted(repo_packages.glob("*.ark")):
            if archive_path.name.startswith("system-docs-"):
                continue
            with (
                lz4.frame.open(archive_path, "rb") as compressed,
                tarfile.open(fileobj=compressed, mode="r|") as archive,
            ):
                for member in archive:
                    if not (member.isfile() or member.issym() or member.islnk()):
                        continue
                    parts = Path(member.name).parts
                    if len(parts) < 3 or parts[0] != "package":
                        continue
                    relative = Path(*parts[1:]).as_posix()
                    if any(
                        relative == root or relative.startswith(root + "/")
                        for root in doc_roots
                    ):
                        claimed.add(relative)

        for root in doc_roots:
            source_root = staging / root
            if not source_root.is_dir():
                continue
            for source in sorted(source_root.rglob("*")):
                if source.is_dir() and not source.is_symlink():
                    continue
                relative = source.relative_to(staging).as_posix()
                if relative not in claimed:
                    tree.add(relative, required=False)
    elif name == "xorg-devel":
        tree.excluded_paths.update(
            {
                "usr/include/X11/extensions/XRes.h",
                "usr/lib/libXRes.so",
                "usr/lib/libXv.so",
            }
        )
        for relative in STAGED_PACKAGE_FILES[name]:
            if relative == "usr/include/X11":
                source_root = staging / relative
                for child in sorted(source_root.iterdir(), key=lambda item: item.name):
                    if child.name != "bitmaps":
                        tree.add(child.relative_to(staging))
            else:
                tree.add(relative)
        for pattern in STAGED_PACKAGE_GLOBS.get(name, ()):
            tree.add_glob(pattern)
    elif name == "openssl-cli":
        for relative in STAGED_PACKAGE_FILES[name]:
            tree.add(relative)
        for pattern in STAGED_PACKAGE_GLOBS.get(name, ()):
            for source in sorted(staging.glob(pattern)):
                relative = source.relative_to(staging).as_posix()
                if relative != "usr/share/man/man1/openssl-rehash.1ssl":
                    tree.add(relative, required=False)
    elif name in STAGED_PACKAGE_FILES:
        for relative in STAGED_PACKAGE_FILES[name]:
            tree.add(relative)
        for pattern in STAGED_PACKAGE_GLOBS.get(name, ()):
            tree.add_glob(pattern)
    else:
        raise ValueError(f"unsupported package recipe: {name}")


def patch_glib_tools_python313(package_root: Path) -> None:
    """Keep GLib 2.78's code generator compatible with Python 3.12 and newer."""
    utils_path = package_root / "usr/share/glib-2.0/codegen/utils.py"
    source = utils_path.read_text(encoding="utf-8")
    old_import = "import distutils.version\n"
    old_compare = "return (distutils.version.LooseVersion(v), key[1])"
    if old_import not in source or old_compare not in source:
        raise ValueError("unexpected GLib gdbus-codegen version comparison code")
    source = source.replace(old_import, "import re\n")
    source = source.replace(
        "def version_cmp_key(key):",
        "def _glib_version_key(value):\n"
        "    return tuple(\n"
        "        (0, int(part)) if part.isdigit() else (1, part.casefold())\n"
        '        for part in re.findall(r"\\d+|[A-Za-z]+", value)\n'
        "    )\n\n\n"
        "def version_cmp_key(key):",
    )
    source = source.replace(old_compare, "return (_glib_version_key(v), key[1])")
    utils_path.write_text(source, encoding="utf-8")


def strip_elf_payload(package_root: Path) -> None:
    strip_tool = shutil.which("strip")
    if strip_tool is None:
        raise FileNotFoundError(
            "strip is required to remove debug data from package binaries"
        )
    for path in package_root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        with path.open("rb") as stream:
            header = stream.read(20)
            if len(header) < 20 or header[:4] != b"\x7fELF":
                continue
            byte_order = {1: "little", 2: "big"}.get(header[5])
            if byte_order is None or int.from_bytes(header[18:20], byte_order) == 0:
                # Guile .go bytecode uses an ELF container with e_machine=0;
                # binutils strip cannot treat these embedded objects as native ELF.
                continue
        mode = path.stat().st_mode & 0o7777
        path.chmod(mode | 0o200)
        try:
            subprocess.run([strip_tool, "--strip-unneeded", str(path)], check=True)
        finally:
            path.chmod(mode)


def compress_large_archive_for_distribution(archive_path: Path) -> None:
    # Git hosting rejects individual blobs at 100 MB; use LZ4 HC for large
    # frames while retaining the same format understood by arkpkg.
    if archive_path.stat().st_size <= 90_000_000:
        return
    compressed_path = archive_path.with_name(archive_path.name + ".hc")
    try:
        with (
            lz4.frame.open(archive_path, "rb") as source,
            lz4.frame.open(
                compressed_path,
                "wb",
                compression_level=16,
                block_size=lz4.frame.BLOCKSIZE_MAX64KB,
            ) as destination,
        ):
            shutil.copyfileobj(source, destination, 1024 * 1024)
        if compressed_path.stat().st_size < archive_path.stat().st_size:
            os.replace(compressed_path, archive_path)
        else:
            compressed_path.unlink()
    finally:
        compressed_path.unlink(missing_ok=True)
    if archive_path.stat().st_size >= 100_000_000:
        raise ValueError(
            f"{archive_path.name} is {archive_path.stat().st_size} bytes; "
            "split this package so it remains below Git hosting limits"
        )


def build_packages(args: argparse.Namespace) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    staging = args.staging.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    package_names = args.packages or PACKAGES

    with tempfile.TemporaryDirectory(prefix="arkpkg-package-build-") as work:
        work_dir = Path(work)
        firefox_archive = (
            obtain_firefox_archive(args.firefox_archive, work_dir)
            if "firefox" in package_names
            else None
        )

        for name in package_names:
            recipe = repo_root / "packages/recipes" / name / "ARKPKG"
            package_root = work_dir / name
            payload_root = package_root / "package"
            payload_root.mkdir(parents=True)
            shutil.copyfile(recipe, package_root / "ARKPKG")

            if name == "firefox":
                if firefox_archive is None:
                    raise ValueError(
                        "Firefox package selected without a verified archive"
                    )
                add_firefox_payload(payload_root, staging, firefox_archive)
            else:
                add_staged_payload(name, payload_root, staging)
                if name == "glib-tools":
                    patch_glib_tools_python313(payload_root)
                if name == "bzip2-devel":
                    (payload_root / "usr/lib/libbz2.so").symlink_to("libbz2.so.1.0")

            strip_elf_payload(payload_root)
            version = read_field(recipe, "Version")
            arch = read_field(recipe, "Arch")
            output = output_dir / f"{name}-{version}-{arch}.ark"
            subprocess.run(
                [
                    str(args.arkpkg_build.resolve()),
                    str(package_root),
                    "--output",
                    str(output),
                ],
                check=True,
            )
            compress_large_archive_for_distribution(output)
            print(f"Built {output} ({output.stat().st_size} bytes)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--arkpkg-build", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--firefox-archive", type=Path)
    parser.add_argument(
        "--packages",
        nargs="+",
        choices=PACKAGES,
        help="Build only the selected packages (default: all packages)",
    )
    args = parser.parse_args()
    if args.output_dir is None:
        args.output_dir = Path(__file__).resolve().parents[1] / "packages"
    return args


if __name__ == "__main__":
    build_packages(parse_args())
