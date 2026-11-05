#!/usr/bin/env bash
# Sourced by bootstrap.sh; run() handles previews. Keep distro policy here.
install_prerequisites() {
    if command -v apt-get >/dev/null 2>&1; then
        run sudo apt-get update
        run sudo apt-get install -y build-essential procps curl file git ca-certificates
    elif command -v dnf >/dev/null 2>&1; then
        run sudo dnf install -y gcc gcc-c++ make procps-ng curl file git ca-certificates
    elif command -v pacman >/dev/null 2>&1; then
        run sudo pacman -S --needed base-devel procps-ng curl file git ca-certificates
    else
        echo 'No prerequisite adapter for this distro. Install a C/C++ compiler, make, procps, curl, file, Git and CA certificates, then rerun with --skip-prerequisites.' >&2
        return 1
    fi
}
