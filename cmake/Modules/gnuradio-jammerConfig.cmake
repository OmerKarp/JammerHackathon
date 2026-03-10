find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_JAMMER gnuradio-jammer)

FIND_PATH(
    GR_JAMMER_INCLUDE_DIRS
    NAMES gnuradio/jammer/api.h
    HINTS $ENV{JAMMER_DIR}/include
        ${PC_JAMMER_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_JAMMER_LIBRARIES
    NAMES gnuradio-jammer
    HINTS $ENV{JAMMER_DIR}/lib
        ${PC_JAMMER_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-jammerTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_JAMMER DEFAULT_MSG GR_JAMMER_LIBRARIES GR_JAMMER_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_JAMMER_LIBRARIES GR_JAMMER_INCLUDE_DIRS)
