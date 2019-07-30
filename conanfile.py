from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment

SOURCE_ARCHIVE = "tango-9.2.5a.tar.gz"


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
    exports_sources = source_archive,

    def source(self):
        tools.unzip(TangoConan.source_archive)

    def build(self):
        path = "{0}/{1}".format(self.source_folder, self.file_prefix)
        autotools = AutoToolsBuildEnvironment(self)
        autotools.configure(configure_dir=path, args=["--disable-java", "--disable-dbserver", "--disable-dbcreate"])
        autotools.make()

    def system_requirements(self):
        # Probably nicer to do this via conan packages...
        if self.settings.os == "Linux" and tools.os_info.is_linux:
            if tools.os_info.with_apt:
                installer = tools.SystemPackageTool()
                packages = ["libomniorb4-dev", "omniidl"]
                for package in packages:
                    installer.install(package)

    def package(self):
        autotools = AutoToolsBuildEnvironment(self)
        autotools.install()

    def package_info(self):
        self.cpp_info.libs = ["tango"]
        self.cpp_info.includedirs = ["include/tango"]


