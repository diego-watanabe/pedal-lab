#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <pedallab/Gain.h>

#include <array>

// The plugin layer is a thin wrapper: parameters, state and channel handling.
// All sound-making code lives in dsp/ (pedallab::Gain here).
class LabGainProcessor final : public juce::AudioProcessor
{
public:
    LabGainProcessor();

    void prepareToPlay(double sampleRate, int maximumExpectedSamplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;
    void processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi) override;
    using AudioProcessor::processBlock;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }

    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int /*index*/) override {}
    const juce::String getProgramName(int /*index*/) override { return {}; }
    void changeProgramName(int /*index*/, const juce::String& /*newName*/) override {}

    void getStateInformation(juce::MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;

    juce::AudioProcessorValueTreeState parameters;

private:
    static juce::AudioProcessorValueTreeState::ParameterLayout createLayout();

    std::atomic<float>* gainDb = nullptr; // owned by `parameters`, read on the audio thread
    std::array<pedallab::Gain, 2> gains;  // one per channel

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(LabGainProcessor)
};
