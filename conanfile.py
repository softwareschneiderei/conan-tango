from conans import ConanFile, tools, AutoToolsBuildEnvironment


SOURCE_ARCHIVE = "tango-9.2.5a.tar.gz"
TANGO_CONFIG_FOR_GCC49_PATCH = "tango_config_for_gcc49.patch"


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
        # Work around ZMQ storing absolute paths in the .pc file for pkg-config
        tools.replace_in_file("tango-9.2.5a/configure.ac",
                              "ZMQ_ROOT=`eval pkg-config --variable=prefix libzmq`",
                              "ZMQ_ROOT=${ZMQ_PREFIX}")

    def build(self):
        path = "{0}/{1}".format(self.source_folder, self.file_prefix)
        autotools = AutoToolsBuildEnvironment(self)

        args = [
            "--disable-java",
            "--disable-dbserver",
            "--disable-dbcreate",
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
        self.cpp_info.libs = ["tango", "omniDynamic4", "COS4", "omniORB4", "omnithread", "log4tango", "zmq"]
        self.cpp_info.includedirs = ["include/tango"]


