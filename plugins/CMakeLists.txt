set(PEDALLAB_PLUGIN_FORMATS AU VST3 Standalone CACHE STRING "JUCE plugin formats to build")
if(NOT APPLE)
    list(REMOVE_ITEM PEDALLAB_PLUGIN_FORMATS AU)
endif()

# On macOS, copy built plugins into ~/Library/Audio/Plug-Ins so your DAW finds them.
if(APPLE)
    option(PEDALLAB_COPY_PLUGINS "Copy plugins to the system plugin folders after building" ON)
else()
    option(PEDALLAB_COPY_PLUGINS "Copy plugins to the system plugin folders after building" OFF)
endif()

# Add one line per plugin.
add_subdirectory(LabGain)
