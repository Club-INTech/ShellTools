// cppimport

#include <upd/python.hpp>
#include <upd/keyring.hpp>

std::uint32_t double_u32(std::uint32_t); 

upd::keyring keyring{upd::flist<double_u32>, upd::little_endian, upd::two_complement};

PYBIND11_MODULE(test_extension_module, pymodule) {
  upd::py::unpack_keyring(pymodule, keyring);
}

<% setup_unpadded(cfg) %>
