set(PEDALLAB_PLUGIN_FORMATS AU VST3 Standalone CACHE STRING "JUCE plugin formats to build")
if(NOT APPLE)
    list(REMOVE_ITEM PEDALLAB_PLUGIN_FORMATS AU)
endif()

# Copy built plugins to a folder your DAW scans, so a rebuild is all it takes
# to try a change:
#   macOS    ~/Library/Audio/Plug-Ins/{VST3,Components}
#   Windows  %LOCALAPPDATA%\Programs\Common\VST3 (the per-user VST3 folder;
#            no admin rights needed, unlike C:\Program Files\Common Files\VST3)
if(APPLE OR WIN32)
    option(PEDALLAB_COPY_PLUGINS "Copy plugins to a plugin folder after building" ON)
else()
    option(PEDALLAB_COPY_PLUGINS "Copy plugins to a plugin folder after building" OFF)
endif()

# Settings every plugin shares. Pass ${PEDALLAB_PLUGIN_COMMON_ARGS} to juce_add_plugin.
set(PEDALLAB_PLUGIN_COMMON_ARGS
    COMPANY_NAME "pedal-lab"
    PLUGIN_MANUFACTURER_CODE Pdlb
    FORMATS ${PEDALLAB_PLUGIN_FORMATS}
    COPY_PLUGIN_AFTER_BUILD ${PEDALLAB_COPY_PLUGINS})
if(WIN32)
    file(TO_CMAKE_PATH "$ENV{LOCALAPPDATA}/Programs/Common/VST3" _userVst3Dir)
    list(APPEND PEDALLAB_PLUGIN_COMMON_ARGS VST3_COPY_DIR "${_userVst3Dir}")
endif()

# Add one line per plugin.
add_subdirectory(LabGain)
