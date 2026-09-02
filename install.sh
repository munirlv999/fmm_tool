#!/bin/bash
# Install script for FMM Tool v3 - Modular Edition

echo "=========================================="
echo "FMM Tool v3 - Modular Edition Installer"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 tidak ditemukan"
    echo "Silakan install Python 3 terlebih dahulu"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "=========================================="
echo "Installasi selesai!"
echo "=========================================="
echo ""
echo "Cara menjalankan:"
echo "  1. Pastikan file .dat ada di direktori yang sama"
echo "  2. Jalankan: python3 -m fmm_tool"
echo "     atau"
echo "  3. Jalankan: python3 fmm_tool/main.py"
echo ""
