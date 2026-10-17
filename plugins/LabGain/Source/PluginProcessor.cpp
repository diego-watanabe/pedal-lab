#include "PluginProcessor.h"

#include <span>

namespace
{
const juce::ParameterID gainId{"gain", 1};
}

LabGainProcessor::LabGainProcessor()
    : AudioProcessor(BusesProperties()
                         .withInput("Input", juce::AudioChannelSet::stereo(), true)
                         .withOutput("Output", juce::AudioChannelSet::stereo(), true))
    , parameters(*this, nullptr, "LabGain", createLayout())
{
    gainDb = parameters.getRawParameterValue(gainId.getParamID());
}

juce::AudioProcessorValueTreeState::ParameterLayout LabGainProcessor::createLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    layout.add(std::make_unique<juce::AudioParameterFloat>(gainId, "Gain",
                                                           juce::NormalisableRange<float>(-48.0f, 12.0f, 0.1f), 0.0f,
                                                           juce::AudioParameterFloatAttributes().withLabel("dB")));
    return layout;
}

void LabGainProcessor::prepareToPlay(double sampleRate, int /*maximumExpectedSamplesPerBlock*/)
{
    for (auto& gain : gains)
    {
        gain.setGainDecibels(gainDb->load());
        gain.prepare(sampleRate);
    }
}

bool LabGainProcessor::isBusesLayoutSupported(const BusesLayout& layouts) const
{
    const auto& out = layouts.getMainOutputChannelSet();
    if (out != juce::AudioChannelSet::mono() && out != juce::AudioChannelSet::stereo())
        return false;
    return out == layouts.getMainInputChannelSet();
}

void LabGainProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& /*midi*/)
{
    const juce::ScopedNoDenormals noDenormals;

    const auto numSamples = static_cast<size_t>(buffer.getNumSamples());
    const auto channels = std::min(static_cast<size_t>(buffer.getNumChannels()), gains.size());
    const float dB = gainDb->load();

    for (size_t ch = 0; ch < channels; ++ch)
    {
        gains[ch].setGainDecibels(dB);
        gains[ch].process(std::span<float>(buffer.getWritePointer(static_cast<int>(ch)), numSamples));
    }
}

juce::AudioProcessorEditor* LabGainProcessor::createEditor()
{
    return new juce::GenericAudioProcessorEditor(*this);
}

void LabGainProcessor::getStateInformation(juce::MemoryBlock& destData)
{
    if (auto xml = parameters.copyState().createXml())
        copyXmlToBinary(*xml, destData);
}

void LabGainProcessor::setStateInformation(const void* data, int sizeInBytes)
{
    if (auto xml = getXmlFromBinary(data, sizeInBytes); xml && xml->hasTagName(parameters.state.getType()))
        parameters.replaceState(juce::ValueTree::fromXml(*xml));
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new LabGainProcessor();
}
