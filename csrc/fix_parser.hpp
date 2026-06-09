#pragma once
/**
 * C++ FIX 4.4 Wire Format Parser
 * High-performance FIX message parser for tick processing.
 * Handles SOH-delimited tag=value pairs with checksum validation.
 */

#include <cstdint>
#include <cstring>
#include <string_view>
#include <array>
#include <charconv>
#include <algorithm>

namespace atikul::fix {

// FIX Tag constants
enum class Tag : uint16_t {
    BeginString   = 8,
    BodyLength    = 9,
    MsgType       = 35,
    MsgSeqNum     = 34,
    SenderCompID  = 49,
    TargetCompID  = 56,
    SendingTime   = 52,
    Symbol        = 55,
    Side          = 54,
    OrderQty      = 38,
    Price         = 44,
    ClOrdID       = 11,
    OrderID       = 37,
    ExecType      = 150,
    OrdStatus     = 39,
    LeavesQty     = 151,
    CumQty        = 14,
    AvgPx         = 6,
    BidPx         = 270,
    AskPx         = 271,
    BidSize       = 132,
    AskSize       = 135,
    MDEntryType   = 269,
    NoMDEntries   = 268,
    MDEntryPx     = 270,
    MDEntrySize   = 271,
    Checksum      = 10,
    HeartBtInt    = 108,
    EncryptMethod = 98,
    TestReqID     = 112,
    LastMsgSeqNum = 369,
};

// Parsed FIX tag
struct FixTag {
    uint16_t tag;
    std::string_view value;
};

// Parsed market data tick
struct ParsedTick {
    char symbol[16] = {};
    double bid_price = 0.0;
    double ask_price = 0.0;
    double bid_size = 0.0;
    double ask_size = 0.0;
    double last_price = 0.0;
    double last_size = 0.0;
    uint32_t msg_seq_num = 0;
    char msg_type = '\0';
    bool valid = false;
};

// ── FIX Checksum Calculator ───────────────────────────────────────

inline uint8_t fix_checksum(const char* data, size_t len) noexcept {
    uint16_t sum = 0;
    for (size_t i = 0; i < len; ++i) {
        if (data[i] == '\x01') continue;
        sum += static_cast<uint8_t>(data[i]);
    }
    return static_cast<uint8_t>(sum % 256);
}

// ── FIX Parser ────────────────────────────────────────────────────

class FixParser {
    static constexpr size_t MAX_TAGS = 64;
    static constexpr char SOH = '\x01';

    std::array<FixTag, MAX_TAGS> tags_;
    size_t tag_count_ = 0;

public:
    /**
     * Parse a raw FIX message into structured tags.
     * Returns number of tags parsed.
     */
    size_t parse(std::string_view message) noexcept {
        tag_count_ = 0;
        size_t pos = 0;

        while (pos < message.size() && tag_count_ < MAX_TAGS) {
            // Find '='
            size_t eq = message.find('=', pos);
            if (eq == std::string_view::npos) break;

            // Find SOH or end
            size_t soh = message.find(SOH, eq + 1);
            if (soh == std::string_view::npos) soh = message.size();

            // Parse tag number
            uint16_t tag_num = 0;
            auto [ptr, ec] = std::from_chars(
                message.data() + pos, message.data() + eq, tag_num
            );

            if (ec == std::errc()) {
                tags_[tag_count_++] = {
                    tag_num,
                    std::string_view(message.data() + eq + 1, soh - eq - 1)
                };
            }

            pos = soh + 1;
        }

        return tag_count_;
    }

    /**
     * Find a tag by number.
     * Returns pointer to value or nullptr if not found.
     */
    const std::string_view* find(uint16_t tag_num) const noexcept {
        for (size_t i = 0; i < tag_count_; ++i) {
            if (tags_[i].tag == tag_num) {
                return &tags_[i].value;
            }
        }
        return nullptr;
    }

    /**
     * Parse double value from tag.
     */
    double get_double(uint16_t tag_num, double default_val = 0.0) const noexcept {
        auto* val = find(tag_num);
        if (!val) return default_val;

        double result = default_val;
        auto [ptr, ec] = std::from_chars(val->data(), val->data() + val->size(), result);
        return (ec == std::errc()) ? result : default_val;
    }

    /**
     * Parse integer value from tag.
     */
    uint32_t get_uint(uint16_t tag_num, uint32_t default_val = 0) const noexcept {
        auto* val = find(tag_num);
        if (!val) return default_val;

        uint32_t result = default_val;
        auto [ptr, ec] = std::from_chars(val->data(), val->data() + val->size(), result);
        return (ec == std::errc()) ? result : default_val;
    }

    /**
     * Get message type character.
     */
    char msg_type() const noexcept {
        auto* val = find(static_cast<uint16_t>(Tag::MsgType));
        return val && !val->empty() ? val->data()[0] : '\0';
    }

    /**
     * Parse MarketDataSnapshot into ParsedTick.
     */
    ParsedTick parse_market_data() const noexcept {
        ParsedTick tick;
        tick.msg_type = msg_type();
        tick.msg_seq_num = get_uint(static_cast<uint16_t>(Tag::MsgSeqNum));
        tick.valid = true;

        // Symbol
        auto* sym = find(static_cast<uint16_t>(Tag::Symbol));
        if (sym && sym->size() < sizeof(tick.symbol)) {
            std::memcpy(tick.symbol, sym->data(), sym->size());
        }

        // Parse repeating group entries
        uint32_t no_entries = get_uint(static_cast<uint16_t>(Tag::NoMDEntries));

        for (size_t i = 0; i < tag_count_ && no_entries > 0; ++i) {
            if (tags_[i].tag == static_cast<uint16_t>(Tag::MDEntryType)) {
                char entry_type = tags_[i].value.empty() ? '0' : tags_[i].value[0];
                double price = 0.0;
                double size = 0.0;

                // Look ahead for price and size
                for (size_t j = i + 1; j < tag_count_; ++j) {
                    if (tags_[j].tag == static_cast<uint16_t>(Tag::MDEntryPx)) {
                        std::from_chars(tags_[j].value.data(),
                                       tags_[j].value.data() + tags_[j].value.size(),
                                       price);
                    } else if (tags_[j].tag == static_cast<uint16_t>(Tag::MDEntrySize)) {
                        std::from_chars(tags_[j].value.data(),
                                       tags_[j].value.data() + tags_[j].value.size(),
                                       size);
                    } else if (tags_[j].tag == static_cast<uint16_t>(Tag::MDEntryType)) {
                        break;  // Next entry
                    }
                }

                if (entry_type == '0') {       // Bid
                    tick.bid_price = price;
                    tick.bid_size = size;
                } else if (entry_type == '1') { // Offer/Ask
                    tick.ask_price = price;
                    tick.ask_size = size;
                } else if (entry_type == '2') { // Trade
                    tick.last_price = price;
                    tick.last_size = size;
                }
            }
        }

        return tick;
    }

    size_t tag_count() const noexcept { return tag_count_; }
    const FixTag& tag(size_t i) const noexcept { return tags_[i]; }
};

} // namespace atikul::fix
