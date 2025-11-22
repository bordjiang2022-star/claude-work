// 音频设备选择组件 - 使用后端 PyAudio 设备列表
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { apiService } from '@/services/api';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import type { AudioDevice } from '@/types';

export const AudioDeviceSelector: React.FC = () => {
  const { t } = useTranslation();
  const { config, setConfig } = useTranslationStore();

  const [inputDevices, setInputDevices] = useState<AudioDevice[]>([]);
  const [outputDevices, setOutputDevices] = useState<AudioDevice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await apiService.getAudioDevices();
      setInputDevices(response.input_devices);
      setOutputDevices(response.output_devices);

      // 自动选择推荐的设备
      // 输入设备：优先选择 VB-Audio / CABLE Output（虚拟音频线缆的输出端，用作输入源）
      if (response.input_devices.length > 0 && config.input_device_index === undefined) {
        const virtualCable = response.input_devices.find(
          d => d.name.toLowerCase().includes('cable output') ||
               d.name.toLowerCase().includes('vb-audio')
        );
        if (virtualCable) {
          setConfig({ input_device_index: virtualCable.index });
        }
      }

      // 输出设备：优先选择真实扬声器（排除 VB-Audio）
      if (response.output_devices.length > 0 && config.output_device_index === undefined) {
        const realSpeaker = response.output_devices.find(
          d => !d.name.toLowerCase().includes('cable') &&
               !d.name.toLowerCase().includes('vb-audio')
        );
        if (realSpeaker) {
          setConfig({ output_device_index: realSpeaker.index });
        } else {
          // 如果没找到真实扬声器，使用第一个设备
          setConfig({ output_device_index: response.output_devices[0].index });
        }
      }

      console.log('[AudioDevice] Loaded devices from backend:', {
        input: response.input_devices.length,
        output: response.output_devices.length
      });
    } catch (err: any) {
      console.error('Failed to load audio devices:', err);
      setError('Failed to load audio devices. Backend may not have PyAudio installed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputDeviceChange = (index: number) => {
    setConfig({ input_device_index: index });
    const device = inputDevices.find(d => d.index === index);
    console.log('[AudioDevice] Input device changed to:', device?.name);
  };

  const handleOutputDeviceChange = (index: number) => {
    setConfig({ output_device_index: index });
    const device = outputDevices.find(d => d.index === index);
    console.log('[AudioDevice] Output device changed to:', device?.name);
  };

  if (error) {
    return (
      <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm">
        <p className="text-yellow-700">{error}</p>
        <button
          onClick={loadDevices}
          className="mt-2 px-3 py-1 bg-yellow-500 hover:bg-yellow-600 text-white rounded text-xs"
        >
          Retry
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded text-sm">
        <p className="text-gray-600">Loading audio devices from backend...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 输入设备选择 - 虚拟音频线缆 */}
      <div className="p-4 bg-green-50 border border-green-200 rounded">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Input Device (Audio Source / Virtual Cable):
        </label>
        <select
          value={config.input_device_index ?? ''}
          onChange={(e) => handleInputDeviceChange(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          <option value="">-- Select Input Device --</option>
          {inputDevices.map((device) => (
            <option key={device.index} value={device.index}>
              [{device.index}] {device.name}
            </option>
          ))}
        </select>
        <p className="mt-2 text-xs text-gray-600">
          Select VB-Audio CABLE Output to capture audio from video/conference apps
        </p>
      </div>

      {/* 输出设备选择 - 扬声器 */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          TTS Output Device (Speaker):
        </label>
        <select
          value={config.output_device_index ?? ''}
          onChange={(e) => handleOutputDeviceChange(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">-- Select Output Device --</option>
          {outputDevices.map((device) => (
            <option key={device.index} value={device.index}>
              [{device.index}] {device.name}
            </option>
          ))}
        </select>
        <p className="mt-2 text-xs text-gray-600">
          Select your real speakers/headphones to hear TTS translation output
        </p>
      </div>

      {/* 刷新按钮 */}
      <div className="flex justify-end">
        <button
          onClick={loadDevices}
          className="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded text-sm"
        >
          Refresh Devices
        </button>
      </div>
    </div>
  );
};
