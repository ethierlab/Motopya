// NOTE: All credit goes to Federico Bolanos. His original repo is here: https://github.com/fbolanos/LS7366R/blob/master/LS7366R.py
// I, Cameron Cobb, have updated this library to make it work for my needs
// and to make it usable for Python 3.

// Make sure you watch the video and check schematic for proper wiring.

// C++ library to interface with the chip LS7366R for the Raspberry Pi
// Written by Federico Bolanos
// Last Edit: March 17th 2019 - Cameron Cobb
// Reason: Updated for Python 3.0 and above.

// Make sure you do a "pip install spidev"

// Usage: Create an object by calling LS7366R enc(CSX, CLK, BTMD)
// CSX is either CE0 or CE1, CLK is the speed, BTMD is the bytemode 1-4 the resolution of your counter.
// Example: LS7366R encoder(0, 1000000, 4)
// These are the values I normally use.

#include <iostream>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>
#include <cstring>
#include <cstdint>
#include <stdexcept>
#include <array>

class LS7366R {
public:
    // Commands
    static constexpr uint8_t CLEAR_COUNTER = 0x20;
    static constexpr uint8_t CLEAR_STATUS = 0x30;
    static constexpr uint8_t READ_COUNTER = 0x60;
    static constexpr uint8_t READ_STATUS = 0x70;
    static constexpr uint8_t WRITE_MODE0 = 0x88;
    static constexpr uint8_t WRITE_MODE1 = 0x90;

    // Modes
    static constexpr uint8_t QUADRATURE_COUNT_MODE = 0x00;
    static constexpr uint8_t FOURBYTE_COUNTER = 0x00;
    static constexpr uint8_t THREEBYTE_COUNTER = 0x01;
    static constexpr uint8_t TWOBYTE_COUNTER = 0x02;
    static constexpr uint8_t ONEBYTE_COUNTER = 0x03;

    static constexpr std::array<uint8_t, 4> BYTE_MODE = { ONEBYTE_COUNTER, TWOBYTE_COUNTER, THREEBYTE_COUNTER, FOURBYTE_COUNTER };

    // Values
    static constexpr uint32_t MAX_VAL = 4294967295;

    // Constructor
    LS7366R(int cs, int clk, int btmd) : counterSize(btmd), spi_cs(cs), spi_clk(clk) {
        init_spi();
        init_encoder();
    }

    ~LS7366R() {
        close(spi_fd);
        std::cout << "\nThanks for using me! :)" << std::endl;
    }

    void clearCounter() {
        xfer(CLEAR_COUNTER);
        std::cout << "[DONE]" << std::endl;
    }

    void clearStatus() {
        xfer(CLEAR_STATUS);
        std::cout << "[DONE]" << std::endl;
    }

    int32_t readCounter() {
        std::array<uint8_t, 5> readTransaction = { READ_COUNTER, 0, 0, 0, 0 };
        xfer(readTransaction.data(), readTransaction.size());

        int32_t encoderCount = 0;
        for (int i = 0; i < counterSize; ++i) {
            encoderCount = (encoderCount << 8) + readTransaction[i + 1];
        }

        if (readTransaction[1] != 255) {
            return encoderCount;
        } else {
            return encoderCount - (MAX_VAL + 1);
        }
    }

    uint8_t readStatus() {
        std::array<uint8_t, 2> readTransaction = { READ_STATUS, 0xFF };
        xfer(readTransaction.data(), readTransaction.size());
        return readTransaction[1];
    }

private:
    int spi_fd;
    int counterSize;
    int spi_cs;
    int spi_clk;

    void init_spi() {
        std::string spi_device = "/dev/spidev0." + std::to_string(spi_cs);
        spi_fd = open(spi_device.c_str(), O_RDWR);
        if (spi_fd < 0) {
            throw std::runtime_error("Failed to open SPI device");
        }

        uint8_t mode = SPI_MODE_0;
        uint8_t bits = 8;

        if (ioctl(spi_fd, SPI_IOC_WR_MODE, &mode) == -1 || ioctl(spi_fd, SPI_IOC_WR_BITS_PER_WORD, &bits) == -1 ||
            ioctl(spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &spi_clk) == -1) {
            throw std::runtime_error("Failed to configure SPI device");
        }
    }

    void init_encoder() {
        std::cout << "Clearing Encoder CS" << spi_cs << "'s Count...\t";
        clearCounter();

        std::cout << "Clearing Encoder CS" << spi_cs << "'s Status..\t";
        clearStatus();

        xfer(WRITE_MODE0, QUADRATURE_COUNT_MODE);
        usleep(100000); // 0.1 second delay
        xfer(WRITE_MODE1, BYTE_MODE[counterSize - 1]);
    }

    void xfer(uint8_t cmd) {
        xfer(&cmd, 1);
    }

    void xfer(uint8_t cmd, uint8_t data) {
        std::array<uint8_t, 2> tx = { cmd, data };
        xfer(tx.data(), tx.size());
    }

    void xfer(uint8_t *data, size_t len) {
        struct spi_ioc_transfer tr;
        memset(&tr, 0, sizeof(tr));
        tr.tx_buf = reinterpret_cast<unsigned long>(data);
        tr.rx_buf = reinterpret_cast<unsigned long>(data);
        tr.len = len;
        tr.speed_hz = spi_clk;
        tr.bits_per_word = 8;

        if (ioctl(spi_fd, SPI_IOC_MESSAGE(1), &tr) == -1) {
            throw std::runtime_error("Failed to transfer SPI message");
        }
    }
};

int main() {
    try {
        LS7366R encoder(0, 1000000, 4);

        while (true) {
            std::cout << "Encoder count: " << encoder.readCounter() << " Press CTRL-C to terminate test program." << std::endl;
            usleep(500000); // 0.5 second delay
        }
    } catch (const std::exception &ex) {
        std::cerr << ex.what() << std::endl;
        return 1;
    }

    return 0;
}