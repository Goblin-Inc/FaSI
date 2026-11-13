cmake_minimum_required(VERSION 3.14)
project(fasi_core CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(X11 QUIET)

add_library(fasi_core SHARED
    hotkey_listener.cpp
    bridge.cpp
)

if(X11_FOUND)
    target_compile_definitions(fasi_core PRIVATE HAVE_X11=1)
    target_include_directories(fasi_core PRIVATE ${X11_INCLUDE_DIR})
    target_link_libraries(fasi_core PRIVATE ${X11_LIBRARIES} pthread)
else()
    target_link_libraries(fasi_core PRIVATE pthread)
endif()
