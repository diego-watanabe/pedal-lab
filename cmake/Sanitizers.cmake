# Optional sanitizers, selected with -DPEDALLAB_SANITIZER=<name> (see CMakePresets.json).
#   address    use-after-free, buffer overruns, leaks
#   undefined  integer overflow, bad casts, misaligned access
#   thread     data races between the UI and audio threads
#   realtime   allocation, locks or syscalls inside [[clang::nonblocking]] functions
#              (needs Clang 20 or newer; Apple's Xcode Clang may lag behind)
add_library(pedallab_sanitizers INTERFACE)

if(PEDALLAB_SANITIZER)
    if(MSVC)
        message(FATAL_ERROR "Sanitizer presets are set up for Clang/GCC only")
    endif()
    if(PEDALLAB_SANITIZER STREQUAL "address")
        set(_flags -fsanitize=address -fno-omit-frame-pointer)
    elseif(PEDALLAB_SANITIZER STREQUAL "undefined")
        set(_flags -fsanitize=undefined -fno-sanitize-recover=undefined)
    elseif(PEDALLAB_SANITIZER STREQUAL "thread")
        set(_flags -fsanitize=thread)
    elseif(PEDALLAB_SANITIZER STREQUAL "realtime")
        if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR CMAKE_CXX_COMPILER_VERSION VERSION_LESS 20)
            message(FATAL_ERROR "RealtimeSanitizer needs Clang 20+ (found ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}). "
                                "On macOS: brew install llvm, then use the rtsan preset.")
        endif()
        set(_flags -fsanitize=realtime)
        target_compile_definitions(pedallab_sanitizers INTERFACE PEDALLAB_RTSAN=1)
    else()
        message(FATAL_ERROR "Unknown PEDALLAB_SANITIZER '${PEDALLAB_SANITIZER}'")
    endif()
    target_compile_options(pedallab_sanitizers INTERFACE ${_flags})
    target_link_options(pedallab_sanitizers INTERFACE ${_flags})
    message(STATUS "pedal-lab: ${PEDALLAB_SANITIZER} sanitizer enabled")
endif()
