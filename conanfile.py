import os
from shutil import copyfile
from conans import ConanFile, tools, AutoToolsBuildEnvironment


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
    url = "http://misc:8008/wera/conan-tango"
    description = "Tango Control System "
    topics = ("control-system", )
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    generators = "cmake"
    file_prefix = "{0}-{1}".format(name, version)
    source_archive = "{0}.tar.gz".format(file_prefix)
    exports_sources = source_archive, TANGO_CONFIG_FOR_GCC49_PATCH
    requires = "zlib/1.2.11@conan/stable", "zmq/4.3.1@bincrafters/stable"

    def source(self):
        tools.unzip(TangoConan.source_archive)
        # G++ 4.9 does not seem to support abi_tag correctly, but still wants to use it (_GLIBCXX_USE_CXX11_ABI=1)
        tools.patch(patch_file=TANGO_CONFIG_FOR_GCC49_PATCH)

    def build(self):
        path = "{0}/{1}".format(self.source_folder, self.file_prefix)

        # Get and patch the zmq pc file prefix paths
        pc_file = "libzmq.pc"
        libzmq_pc_source = os.path.join(self.deps_cpp_info["zmq"].rootpath, "lib/pkgconfig", pc_file)
        copyfile(libzmq_pc_source, pc_file)
        replace_prefix_everywhere_in_pc_file(pc_file, self.deps_cpp_info["zmq"].rootpath)

        with tools.environment_append({"PKG_CONFIG_PATH": os.getcwd()}):
            autotools = AutoToolsBuildEnvironment(self)

            args = [
                "--disable-java",
                "--disable-dbserver",
                "--disable-dbcreate",
                "--enable-static={0}".format("no" if self.options.shared else "yes"),
                "--enable-shared={0}".format("yes" if self.options.shared else "no"),
                "--with-zlib={0}".format(self.deps_cpp_info["zlib"].rootpath),
                "--with-zmq={0}".format(self.deps_cpp_info["zmq"].rootpath),
            ]
            autotools.configure(
                configure_dir=path,
                args=args)
            autotools.make()

    def system_requirements(self):
        # Probably nicer to do this via conan packages, e.g. https://github.com/nwoetzel/conan-omniorb
        if self.settings.os == "Linux" and tools.os_info.is_linux:
            if tools.os_info.with_apt:
                installer = tools.SystemPackageTool()
                packages = ["libomniorb4-dev", "omniorb", "omniidl", "libcos4-dev"]
                for package in packages:
                    installer.install(package)

    def package(self):
        autotools = AutoToolsBuildEnvironment(self)
        autotools.install()

    def package_info(self):
        self.cpp_info.libs = ["tango", "omniDynamic4", "COS4", "omniORB4", "omnithread", "log4tango", "dl"]
        self.cpp_info.includedirs = ["include/tango"]


