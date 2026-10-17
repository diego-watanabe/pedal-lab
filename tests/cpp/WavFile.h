#pragma once

// Minimal WAV reader for tests: mono or interleaved 16/24/32-bit PCM or
// 32-bit float, returned as float. Test-only code, so it may allocate.

#include <cstdint>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace pedallab::test
{

struct Wav
{
    std::vector<float> samples; // channel 0 only
    int sampleRate = 0;
    int channels = 0;
};

inline Wav readWav(const std::string& path)
{
    std::ifstream in(path, std::ios::binary);
    if (!in)
        throw std::runtime_error("cannot open " + path);
    std::vector<char> bytes((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());

    auto u16 = [&](size_t at)
    {
        std::uint16_t v = 0;
        std::memcpy(&v, bytes.data() + at, 2);
        return v;
    };
    auto u32 = [&](size_t at)
    {
        std::uint32_t v = 0;
        std::memcpy(&v, bytes.data() + at, 4);
        return v;
    };

    if (bytes.size() < 12 || std::memcmp(bytes.data(), "RIFF", 4) != 0 || std::memcmp(bytes.data() + 8, "WAVE", 4) != 0)
        throw std::runtime_error(path + " is not a WAV file");

    Wav wav;
    int format = 0;
    int bits = 0;
    size_t pos = 12;
    while (pos + 8 <= bytes.size())
    {
        const size_t size = u32(pos + 4);
        const char* id = bytes.data() + pos;
        const size_t body = pos + 8;
        if (std::memcmp(id, "fmt ", 4) == 0)
        {
            format = u16(body);
            wav.channels = u16(body + 2);
            wav.sampleRate = static_cast<int>(u32(body + 4));
            bits = u16(body + 14);
            if (format == 0xFFFE) // WAVE_FORMAT_EXTENSIBLE: real format in the subformat GUID
                format = u16(body + 24);
        }
        else if (std::memcmp(id, "data", 4) == 0)
        {
            if (wav.channels <= 0 || bits == 0)
                throw std::runtime_error(path + ": data chunk before fmt chunk");
            const size_t bytesPerSample = static_cast<size_t>(bits) / 8;
            const size_t frameBytes = bytesPerSample * static_cast<size_t>(wav.channels);
            const size_t frames = size / frameBytes;
            wav.samples.resize(frames);
            for (size_t i = 0; i < frames; ++i)
            {
                const char* p = bytes.data() + body + i * frameBytes;
                float value = 0.0f;
                if (format == 3 && bits == 32)
                    std::memcpy(&value, p, 4);
                else if (format == 1 && bits == 16)
                {
                    std::int16_t s = 0;
                    std::memcpy(&s, p, 2);
                    value = static_cast<float>(s) / 32768.0f;
                }
                else if (format == 1 && bits == 24)
                {
                    const auto b0 = static_cast<std::uint8_t>(p[0]);
                    const auto b1 = static_cast<std::uint8_t>(p[1]);
                    const auto b2 = static_cast<std::uint8_t>(p[2]);
                    auto s = static_cast<std::int32_t>((static_cast<std::uint32_t>(b2) << 24) |
                                                       (static_cast<std::uint32_t>(b1) << 16) |
                                                       (static_cast<std::uint32_t>(b0) << 8));
                    value = static_cast<float>(s >> 8) / 8388608.0f;
                }
                else if (format == 1 && bits == 32)
                {
                    std::int32_t s = 0;
                    std::memcpy(&s, p, 4);
                    value = static_cast<float>(static_cast<double>(s) / 2147483648.0);
                }
                else
                    throw std::runtime_error(path + ": unsupported sample format");
                wav.samples[i] = value;
            }
            return wav;
        }
        pos = body + size + (size & 1u);
    }
    throw std::runtime_error(path + ": no data chunk");
}

} // namespace pedallab::test
