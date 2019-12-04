import os
import shutil
from shutil import copyfile
from conans import ConanFile, tools, CMake
from conans.errors import ConanException, ConanInvalidConfiguration

SOURCE_ARCHIVE = "tango-9.2.5a.tar.gz"
TANGO_CONFIG_FOR_GCC49_PATCH = "tango_config_for_gcc49.patch"


def replace_prefix_everywhere_in_pc_file(file, prefix):
    pkg_config = tools.PkgConfig(file)
    old_prefix = pkg_config.variables["prefix"]
    tools.replace_in_file(file, old_prefix, prefix)


class TangoConan(ConanFile):
    name = "tango"
    version = "9.3.3"
    license = "LGPL-3.0"
    author = "Marius Elvert marius.elvert@softwareschneiderei.de"
    url = "https://github.com/softwareschneiderei/conan-tango"
    description = "Tango Control System "
    topics = ("control-system",)
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    generators = "cmake"
    file_prefix = "{0}-{1}".format(name, version)
    source_archive = "{0}.tar.gz".format(file_prefix)
    exports_sources = source_archive, TANGO_CONFIG_FOR_GCC49_PATCH
    requires = "zlib/1.2.11@conan/stable", "zmq/4.3.1@bincrafters/stable",\
               "cppzmq/4.4.1@bincrafters/stable", "omniorb/4.2.2@None/None"

    def source(self):
        tools.Git(folder="cppTango")\
            .clone("https://github.com/tango-controls/cppTango.git",
                   branch="9.3.3", shallow=True)
        tools.Git(folder="tango-idl")\
            .clone("https://github.com/tango-controls/tango-idl",
                   branch="1e5edb84d966814ad367f2674ac9a5658b6724ac", shallow=True)

    def configure(self):
        if self.settings.os == "Linux" and tools.os_info.is_linux and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("Conan needs the setting 'compiler.libcxx' to be 'libstdc++11' on linux")

    def _configured_cmake(self):
        source_location = os.path.join(self.source_folder, "cppTango")
        idl_location = os.path.join(self.source_folder, "tango-idl")
        os.makedirs("tango-idl/include", exist_ok=True)
        shutil.copy(os.path.join(idl_location, "tango.idl"), os.path.join(self.build_folder, "tango-idl/include/"))

        # conan seems to only support in-source builds right now
        shutil.copytree(source_location, self.build_folder, dirs_exist_ok=True)

        cmake = CMake(self)
        with tools.environment_append({"OMNI_BASE": self.deps_cpp_info["omniorb"].rootpath}):
            cmake.configure(
                source_folder=self.build_folder,
                defs={
                    'IDL_BASE': os.path.join(self.build_folder, "tango-idl"),
                    'OMNI_BASE': self.deps_cpp_info["omniorb"].rootpath,
                    'ZMQ_BASE': self.deps_cpp_info["zmq"].rootpath,
                    'CPPZMQ_BASE': self.deps_cpp_info["cppzmq"].rootpath,
                })
        return cmake

    def build(self):
        target = "tango" if self.options.shared else "tango-static"
        self._configured_cmake().build(target=target)

    def package(self):
        self._configured_cmake().install()

    def package_info(self):
        self.cpp_info.libs = ["tango", "log4tango", "dl"]
        self.cpp_info.includedirs = ["include/tango"]
