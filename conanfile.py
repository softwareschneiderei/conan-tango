import os
import shutil
from shutil import copyfile
from conans import ConanFile, tools, CMake
from conans.errors import ConanException, ConanInvalidConfiguration

DISABLE_RUNTIME_LIBRARY_OVERRIDES = "disable_runtime_library_overrides.patch"
NO_SED_PATCH = "0001-Do-not-use-sed-for-file-enhancements.patch"
CPPZMQ_INSTALL_PATCH = "fix_cppzmq_install_paths.patch"
MAKE_PTHREAD_WIN_TRULY_OPTIONAL = "make_pthread_win_truly_optional.patch"
TANGO_CONFIG_RESILIENT_AGAINST_PREDEFINES = "tango_config_resilient_against_predefines.patch"
DO_NO_INSTALL_DEPENDENCIES = "do_not_install_dependencies.patch"
FIX_LIBRARY_COMPONENTS = "fix_library_components.patch"

PATCHES = [DISABLE_RUNTIME_LIBRARY_OVERRIDES,
           NO_SED_PATCH, CPPZMQ_INSTALL_PATCH,
           DO_NO_INSTALL_DEPENDENCIES,
           MAKE_PTHREAD_WIN_TRULY_OPTIONAL,
           TANGO_CONFIG_RESILIENT_AGAINST_PREDEFINES,
           FIX_LIBRARY_COMPONENTS]


PTHREADS_WIN32 = "https://github.com/tango-controls/Pthread_WIN32/releases/download/2.9.1/pthreads-win32-2.9.1_{0}.zip"


def prepend_file_with(file_path, added):
    lines = []
    with open(file_path) as file:
        lines = file.readlines()

    # Prepend, if we have not already
    if len(lines) >= len(added) and lines[:len(added)] != added:
        lines = added + lines

    with open(file_path, "w") as file:
        file.writelines(lines)


def replace_prefix_everywhere_in_pc_file(file, prefix):
    pkg_config = tools.PkgConfig(file)
    old_prefix = pkg_config.variables["prefix"]
    tools.replace_in_file(file, old_prefix, prefix)


# From https://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth/31039095
def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


class CppTangoConan(ConanFile):
    name = "cpptango"
    version = "9.3.3"
    license = "LGPL-3.0"
    author = "Marius Elvert marius.elvert@softwareschneiderei.de"
    url = "https://github.com/softwareschneiderei/conan-cpptango"
    description = "Tango Control System C++ Libraries"
    topics = ("control-system",)
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "pthread_windows": [True, False]
    }
    default_options = {
        "shared": False,
        "pthread_windows": False
    }
    generators = "cmake"
    file_prefix = "{0}-{1}".format(name, version)
    source_archive = "{0}.tar.gz".format(file_prefix)
    exports_sources = PATCHES
    requires = "zlib/1.2.11@conan/stable", "zmq/4.3.2@bincrafters/stable",\
               "cppzmq/4.4.1@bincrafters/stable", "omniorb/4.2.3@softwareschneiderei/stable"

    def _download_windows_pthreads(self):
        if self.settings.arch == "x86_64":
            arch = "x64"
        elif self.settings.arch == "x86":
            arch = "win32"
        else:
            raise ConanInvalidConfiguration("Can only build for x86 or x86_64")
        # VS 2019 is ABI compatible to VS 2017, fortunately
        visual_studio_version = min(int(str(self.settings.compiler.version)), 15)
        suffix = "{0}-msvc{1}".format(arch, visual_studio_version)
        url = PTHREADS_WIN32.format(suffix)
        self.output.info("Downloading from {0}".format(url))
        zip_file = "pthreads-win32.zip"
        tools.download(url, zip_file, overwrite=True)
        tools.unzip(zip_file, "pthreads-win32")
        os.unlink(zip_file)

    def source(self):
        tools.Git(folder="cppTango")\
            .clone("https://github.com/tango-controls/cppTango.git",
                   branch="refs/tags/9.3.3", shallow=True)

        idl = tools.Git(folder="tango-idl")
        idl.clone("https://github.com/tango-controls/tango-idl")
        idl.checkout("1e5edb84d966814ad367f2674ac9a5658b6724ac")

    def configure(self):
        if self.settings.os == "Linux" and tools.os_info.is_linux and self.settings.compiler.libcxx != "libstdc++11":
            raise ConanInvalidConfiguration("Conan needs the setting 'compiler.libcxx' to be 'libstdc++11' on linux")
        
        self.options["omniorb"].shared = self.options.shared
        self.options["zmq"].shared = self.options.shared

    def config_options(self):
        if self.settings.os != "Windows":
            del self.options.pthread_windows

    def _env_and_vars(self):
        return {
            "OMNI_BASE": self.deps_cpp_info["omniorb"].rootpath.replace("\\", "/"),
            'ZMQ_BASE': self.deps_cpp_info["zmq"].rootpath.replace("\\", "/"),
            'CPPZMQ_BASE': self.deps_cpp_info["cppzmq"].rootpath.replace("\\", "/"),
        }

    def _configured_cmake(self):
        cmake = CMake(self)
        env_and_vars = self._env_and_vars()
        with tools.environment_append(env_and_vars):
            defs = {
                'IDL_BASE': os.path.join(self.build_folder, "tango-idl").replace("\\", "/"),
                'CMAKE_INSTALL_COMPONENT': "dynamic" if self.options.shared else "static",
            }
            if self.settings.os == "Windows" and self.options.pthread_windows:
                defs["PTHREAD_WIN"] = os.path.join(self.build_folder, "pthreads-win32").replace("\\", "/")
            if self.settings.os == "Windows":
                defs["CMAKE_DEBUG_POSTFIX"] = "d"
                defs["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = "ON" if self.options.shared else "OFF"
            defs.update(env_and_vars)

            cmake.configure(
                source_folder=self.build_folder,
                defs=defs)
        return cmake

    def _cmake_comment_out(self, file, content):
        tools.replace_in_file(file, content, "# " + content)

    def build(self):
        if self.settings.os == "Windows" and self.options.pthread_windows:
            self._download_windows_pthreads()

        source_location = os.path.join(self.source_folder, "cppTango")
        idl_location = os.path.join(self.source_folder, "tango-idl")

        os.makedirs("tango-idl/include", exist_ok=True)
        shutil.copy(os.path.join(idl_location, "tango.idl"), os.path.join(self.build_folder, "tango-idl/include/"))

        # tango seems to only support in-source builds right now
        copytree(source_location, self.build_folder, ignore=shutil.ignore_patterns(".git"))

        # Apply all patches
        for patch in PATCHES:
            self.output.info("Applying patch: {0}".format(patch))
            tools.patch(patch_file=os.path.join(self.source_folder, patch))

        # Disable installation of the wrong variant (shared/static)
        if self.settings.os == "Linux":
            cmake_linux = os.path.join(self.build_folder, "configure/cmake_linux.cmake")
            if not self.options.shared:
                self._cmake_comment_out(cmake_linux, 'install(TARGETS tango LIBRARY DESTINATION "${CMAKE_INSTALL_FULL_LIBDIR}")')
            else:
                self._cmake_comment_out(cmake_linux, 'install(TARGETS tango-static ARCHIVE DESTINATION "${CMAKE_INSTALL_FULL_LIBDIR}")')
        
        # Replace library dependencies by what conan provides
        if self.settings.os == "Windows":
            new_dependency_settings = [
                'set(OMNIORB_PKG_LIBRARIES {0})\n'.format(';'.join(self.deps_cpp_info["omniorb"].libs)),
                'set(ZMQ_PKG_LIBRARIES {0})\n'.format(';'.join(self.deps_cpp_info["zmq"].libs)),
                'set(PTHREAD_WIN_PKG_LIBRARIES "")\n',
                'link_directories(${ZMQ_BASE}/lib)\n',
            ]
            prepend_file_with(os.path.join(self.build_folder, "configure/CMakeLists.txt"), new_dependency_settings)
            cmake_windows = os.path.join(self.build_folder, "configure/cmake_win.cmake")
            dependency_variables = ["OMNIORB_PKG_LIBRARIES", "ZMQ_PKG_LIBRARIES", "PTHREAD_WIN_PKG_LIBRARIES"]
            for dependency_suffix in ["DYN", "STA"]:
                for variable in dependency_variables:
                    tools.replace_in_file(cmake_windows, '${{{1}_{0}}}'.format(dependency_suffix, variable), '${{{0}}}'.format(variable))

        target = "tango" if self.options.shared else "tango-static"
        cmake = self._configured_cmake()
        cmake.build(target=target)

    def package(self):
        library_component = "dynamic" if self.options.shared else "static"
        for component in [library_component, "headers", "Unspecified"]:
            cmd = "cmake {0} -DCMAKE_INSTALL_COMPONENT={1} -DCMAKE_INSTALL_CONFIG_NAME={2} -P cmake_install.cmake"\
                .format(CMake(self).command_line, component, self.settings.build_type)
            self.run(command=cmd, cwd=self.build_folder)

    def package_info(self):
        if self.settings.os == "Windows":
            debug_suffix = "d" if self.settings.build_type == "Debug" else ""
            library_prefix = "lib" if not self.options.shared else ""
            tango_library = library_prefix + "tango" + debug_suffix
            self.cpp_info.libs = [
                tango_library,
                "Comctl32", # Need this for InitCommonControls
            ]
        else:
            self.cpp_info.libs = ["tango", "dl"]
        self.cpp_info.includedirs = ["include", "include/tango"]
