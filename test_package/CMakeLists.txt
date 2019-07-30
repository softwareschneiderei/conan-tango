cmake_minimum_required(VERSION 3.1.3)
project(PackageTest CXX)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(tango_package_test tango_package_test.cpp)
target_link_libraries(tango_package_test ${CONAN_LIBS})
target_compile_options(tango_package_test
  PUBLIC -std=c++11
)