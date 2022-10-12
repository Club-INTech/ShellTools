// cppimport

#include <pybind11/pybind11.h>
#include <readline/readline.h>

PYBIND11_MODULE(readline_extension, pymodule) {
  pymodule
    .def(
        "forced_update_display",
        rl_forced_update_display,
        pybind11::doc{"Call `rl_forced_update_display` from the GNU Readline Library"});
}

<%
  cfg["libraries"] = ["readline"]
  setup_unpadded(cfg)
%>
