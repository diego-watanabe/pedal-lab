# Strict warnings for code in this repo, never for JUCE or other dependencies.
#
#   pedallab_warnings      INTERFACE target for targets made only of our code (tests)
#   pedallab_warn(<files>) applies the same flags to individual source files, for
#                          targets that also compile JUCE module code (plugins)
if(MSVC)
    set(PEDALLAB_WARNING_FLAGS /W4 /permissive-)
    if(PEDALLAB_WERROR)
        list(APPEND PEDALLAB_WARNING_FLAGS /WX)
    endif()
else()
    set(PEDALLAB_WARNING_FLAGS
        -Wall -Wextra -Wpedantic
        -Wshadow -Wconversion -Wsign-conversion -Wdouble-promotion
        -Wold-style-cast -Wcast-align -Wnon-virtual-dtor -Woverloaded-virtual
        -Wnull-dereference -Wimplicit-fallthrough)
    if(PEDALLAB_WERROR)
        list(APPEND PEDALLAB_WARNING_FLAGS -Werror)
    endif()
endif()

add_library(pedallab_warnings INTERFACE)
target_compile_options(pedallab_warnings INTERFACE ${PEDALLAB_WARNING_FLAGS})

function(pedallab_warn)
    set_property(SOURCE ${ARGN} APPEND PROPERTY COMPILE_OPTIONS ${PEDALLAB_WARNING_FLAGS})
endfunction()
