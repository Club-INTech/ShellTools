// cppimport

#include <upd/python.hpp>
#include <upd/keyring.hpp>

std::uint8_t double_u8(std::uint8_t);
std::uint16_t double_u16(std::uint16_t);
std::uint32_t double_u32(std::uint32_t);
std::int8_t double_i8(std::int8_t);
std::int16_t double_i16(std::int16_t);
std::int32_t double_i32(std::int32_t);
std::int64_t double_i64(std::int64_t);
std::int64_t identity_i64(std::int64_t);

inline void reply(std::int64_t) {}

upd::keyring keyring{upd::flist<
    double_u8,
    double_u16,
    double_u32,
    double_i8,
    double_i16,
    double_i32,
    double_i64,
    identity_i64>,
  upd::little_endian, upd::two_complement};
upd::keyring dispatcher_keyring{upd::flist<reply>, upd::little_endian, upd::two_complement};

PYBIND11_MODULE(test_extension_module, pymodule) {
  upd::py::unpack_keyring(pymodule, keyring);
  upd::py::declare_dispatcher(pymodule, "Dispatcher", dispatcher_keyring);
}

<% setup_unpadded(cfg) %>
