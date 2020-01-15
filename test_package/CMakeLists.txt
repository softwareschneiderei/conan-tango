cmake_minimum_required(VERSION 3.1.3)
project(PackageTest CXX)

set(CMAKE_CXX_STANDARD 11)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(tango_package_test tango_package_test.cpp)
target_link_libraries(tango_package_test ${CONAN_LIBS})
