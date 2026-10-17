#pragma once

// PEDALLAB_NONBLOCKING marks a function that runs on the audio thread.
//
// With Clang 20+ it expands to [[clang::nonblocking]]. The compiler then warns
// (-Wfunction-effects) when such a function calls something that may block,
// and builds with the realtime sanitizer preset abort at run time if it
// allocates, takes a lock or makes a system call. On other compilers it
// expands to nothing, so the code still builds everywhere.
//
// Put it on every process()/processSample() that the audio callback reaches.

#if defined(__has_cpp_attribute)
    #if __has_cpp_attribute(clang::nonblocking)
        #define PEDALLAB_NONBLOCKING [[clang::nonblocking]]
    #endif
#endif

#ifndef PEDALLAB_NONBLOCKING
    #define PEDALLAB_NONBLOCKING
#endif
