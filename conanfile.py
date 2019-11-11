import os
from shutil import copyfile
from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.errors import ConanInvalidConfiguration

SOURCE_ARCHIVE = "tango-9.2.5a.tar.gz"
TANGO_CONFIG_FOR_GCC49_PATCH = "tango_config_for_gcc49.patch"


def replace_prefix_everywhere_in_pc_file(file, prefix):
    pkg_config = tools.PkgConfig(file)
    old_prefix = pkg_config.variables["prefix"]
    tools.replace_in_file(file, old_prefix, prefix)


class TangoConan(ConanFile):
    name = "tango"
    version = "9.2.5a"
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
    requires = "zlib/1.2.11@conan/stable", "zmq/4.3.1@bincrafters/stable", "omniorb/4.2.2@None/None"

    def source(self):
        tools.unzip(TangoConan.source_archive)
        # G++ 4.9 does not seem to support abi_tag correctly, but still wants to use it (_GLIBCXX_USE_CXX11_ABI=1)
        tools.patch(patch_file=TANGO_CONFIG_FOR_GCC49_PATCH)

    def configure(self):
        if self.settings.os == "Linux" and tools.os_info.is_linux and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("Conan needs the setting 'compiler.libcxx' to be 'libstdc++11' on linux")

    def build(self):
        path = "{0}/{1}".format(self.source_folder, self.file_prefix)

        # Get and patch the zmq pc file prefix paths
        pc_file = "libzmq.pc"
        libzmq_pc_source = os.path.join(self.deps_cpp_info["zmq"].rootpath, "lib/pkgconfig", pc_file)
        copyfile(libzmq_pc_source, pc_file)
        replace_prefix_everywhere_in_pc_file(pc_file, self.deps_cpp_info["zmq"].rootpath)

        with tools.environment_append({"PKG_CONFIG_PATH": os.getcwd()}):
            autotools = AutoToolsBuildEnvironment(self)

            # It looks like the libs injected from the requirements break the "test compile" stages in the configure stage
            # autotools.libs = []

            args = [
                "--disable-java",
                "--disable-dbserver",
                "--disable-dbcreate",
                "--enable-static={0}".format("no" if self.options.shared else "yes"),
                "--enable-shared={0}".format("yes" if self.options.shared else "no"),
                "--with-zlib={0}".format(self.deps_cpp_info["zlib"].rootpath),
                "--with-zmq={0}".format(self.deps_cpp_info["zmq"].rootpath),
                "--with-omni={0}".format(self.deps_cpp_info["omniorb"].rootpath),
            ]

            autotools.configure(
                configure_dir=path,
                pkg_config_paths=[os.getcwd()],
                args=args)
            autotools.make()

    def package(self):
        autotools = AutoToolsBuildEnvironment(self)
        autotools.install()

    def package_info(self):
        self.cpp_info.libs = ["tango", "log4tango", "dl"]
        self.cpp_info.includedirs = ["include/tango"]
