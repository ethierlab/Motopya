# Setting Up and Using `ads1015-python` on Raspberry Pi 5

## Prerequisites

Ensure your Raspberry Pi 5 is running Raspbian OS and is connected to the internet.

## Step-by-Step Guide

### 1. Update Your System

Open a terminal and run:
```bash
sudo apt update
sudo apt upgrade
```

### 2. Install Git

If Git is not installed, install it by running:
```bash
sudo apt install git
```

### 3. Clone the Repository

Clone the `ads1015-python` repository:
```bash
git clone https://github.com/pimoroni/ads1015-python
cd ads1015-python
```

### 4. Install `python3-venv`

If `python3-venv` is not installed, install it by running:
```bash
sudo apt install python3-venv
```

### 5. Create and Activate a Virtual Environment

Create a virtual environment:
```bash
python3 -m venv venv
```

Activate the virtual environment:
```bash
source venv/bin/activate
```

### 6. Install Dependencies

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 7. Install the Package in Editable Mode

Ensure the `ads1015` package is available by installing it in editable mode:
```bash
pip install -e .
```

### 8. Enable I2C Interface

Enable the I2C interface by running:
```bash
sudo raspi-config
```

Navigate to `Interfacing Options` -> `I2C` and enable it. Reboot your Raspberry Pi:
```bash
sudo reboot
```

### 9. Verify I2C Interface

After rebooting, check if the I2C interface is available:
```bash
ls /dev/i2c-*
```

You should see `/dev/i2c-1` in the output.

### 10. Install I2C Tools

Install the I2C tools:
```bash
sudo apt install i2c-tools
```

### 11. Test I2C Interface

Scan for I2C devices connected to your Raspberry Pi:
```bash
sudo i2cdetect -y 1
```

### 12. Run the Example Script

With the virtual environment activated, run the example script:
```bash
python examples/read-all.py
```

### 13. Deactivate the Virtual Environment

Once you're done, deactivate the virtual environment:
```bash
deactivate
```

## Summary of Commands

```bash
sudo apt update
sudo apt upgrade
sudo apt install git
git clone https://github.com/pimoroni/ads1015-python
cd ads1015-python
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
sudo raspi-config
# Enable I2C in Interfacing Options and reboot
sudo reboot
ls /dev/i2c-*
sudo apt install i2c-tools
sudo i2cdetect -y 1
python examples/read-all.py
deactivate
```

### Wiring the ADS1015

Ensure that you have connected the ADS1015 to your Raspberry Pi correctly:
- VDD to 3.3V or 5V
- GND to GND
- SCL to SCL (GPIO 3)
- SDA to SDA (GPIO 2)

### Troubleshooting

If you encounter any issues, ensure that:
- The I2C interface is enabled.
- The wiring is correct.
- You are running the script from within the virtual environment.
