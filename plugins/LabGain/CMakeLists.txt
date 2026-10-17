# LabGain: the template plugin. Copy this folder to start a new one, then
# change the name, PLUGIN_CODE and BUNDLE_ID.
juce_add_plugin(LabGain
    COMPANY_NAME "pedal-lab"
    PRODUCT_NAME "Lab Gain"
    BUNDLE_ID com.pedallab.labgain
    PLUGIN_MANUFACTURER_CODE Pdlb
    PLUGIN_CODE Lgn1
    FORMATS ${PEDALLAB_PLUGIN_FORMATS}
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    COPY_PLUGIN_AFTER_BUILD ${PEDALLAB_COPY_PLUGINS})

set(LABGAIN_SOURCES
    Source/PluginProcessor.cpp
    Source/PluginProcessor.h)

target_sources(LabGain PRIVATE ${LABGAIN_SOURCES})
pedallab_warn(${LABGAIN_SOURCES})

target_compile_definitions(LabGain PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0)

target_link_libraries(LabGain
    PRIVATE
        pedallab::dsp
        juce::juce_audio_utils
        juce::juce_dsp
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags)
