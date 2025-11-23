// 音频设备选择组件 - 使用后端 PyAudio 设备列表
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { apiService } from '@/services/api';
import { useTranslationStore } from '@/hooks/useTranslationStore';
import type { AudioDevice } from '@/types';

// 判断是否是虚拟音频设备
const isVirtualDevice = (name: string): boolean => {
  const lowerName = name.toLowerCase();
  return lowerName.includes('cable') ||
         lowerName.includes('vb-audio') ||
         lowerName.includes('virtual');
};

// 判断是否是真实扬声器设备
const isRealSpeaker = (name: string): boolean => {
  const lowerName = name.toLowerCase();
  // 排除虚拟设备
  if (isVirtualDevice(name)) return false;
  // 检查常见的扬声器名称
  return lowerName.includes('speaker') ||
         lowerName.includes('扬声器') ||
         lowerName.includes('realtek') ||
         lowerName.includes('headphone') ||
         lowerName.includes('耳机') ||
         lowerName.includes('output');
};

// 获取设备显示名称（带标记）
const getDeviceDisplayName = (device: AudioDevice, isOutput: boolean): string => {
  const name = device.name;
  const lowerName = name.toLowerCase();

  if (isOutput) {
    // 对输出设备，标记真实扬声器和虚拟设备
    if (isRealSpeaker(name)) {
      return `🔊 ${name} (推荐)`;
    } else if (isVirtualDevice(name)) {
      return `⚠️ ${name} (虚拟设备 - 不推荐)`;
    }
  } else {
    // 对输入设备，标记虚拟音频线缆
    if (lowerName.includes('cable output')) {
      return `✅ ${name} (推荐 - 虚拟音频捕获)`;
    } else if (isVirtualDevice(name)) {
      return `📡 ${name} (虚拟设备)`;
    }
  }
  return name;
};

export const AudioDeviceSelector: React.FC = () => {
  const { t } = useTranslation();
  const { config, setConfig } = useTranslationStore();

  const [inputDevices, setInputDevices] = useState<AudioDevice[]>([]);
  const [outputDevices, setOutputDevices] = useState<AudioDevice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [warning, setWarning] = useState<string>('');

  useEffect(() => {
    loadDevices();
  }, []);

  // 当输出设备改变时检查是否选择了虚拟设备
  useEffect(() => {
    if (config.output_device_index !== undefined && outputDevices.length > 0) {
      const selectedDevice = outputDevices.find(d => d.index === config.output_device_index);
      if (selectedDevice && isVirtualDevice(selectedDevice.name)) {
        setWarning('⚠️ 警告：您选择了虚拟音频设备作为TTS输出，您将无法通过扬声器听到声音！请选择真实的扬声器设备（如 Realtek 或 Speakers）。');
      } else {
        setWarning('');
      }
    }
  }, [config.output_device_index, outputDevices]);

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

      // 输出设备：优先选择真实扬声器（排除虚拟设备）
      if (response.output_devices.length > 0 && config.output_device_index === undefined) {
        // 优先查找明确的扬声器设备
        const realSpeaker = response.output_devices.find(d => isRealSpeaker(d.name));

        if (realSpeaker) {
          setConfig({ output_device_index: realSpeaker.index });
          console.log('[AudioDevice] Auto-selected real speaker:', realSpeaker.name, 'index:', realSpeaker.index);
        } else {
          // 如果没找到明确的扬声器，选择第一个非虚拟设备
          const nonVirtualDevice = response.output_devices.find(d => !isVirtualDevice(d.name));
          if (nonVirtualDevice) {
            setConfig({ output_device_index: nonVirtualDevice.index });
            console.log('[AudioDevice] Auto-selected non-virtual device:', nonVirtualDevice.name);
          } else {
            // 最后手段：使用第一个设备并显示警告
            setConfig({ output_device_index: response.output_devices[0].index });
            setWarning('⚠️ 未找到真实扬声器设备，请手动选择正确的输出设备！');
          }
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

  const handleInputDeviceChange = (value: string) => {
    if (value === '') {
      setConfig({ input_device_index: undefined });
      console.log('[AudioDevice] Input device cleared');
      return;
    }
    const index = Number(value);
    setConfig({ input_device_index: index });
    const device = inputDevices.find(d => d.index === index);
    console.log('[AudioDevice] Input device changed to:', device?.name, 'index:', index);
  };

  const handleOutputDeviceChange = (value: string) => {
    if (value === '') {
      setConfig({ output_device_index: undefined });
      console.log('[AudioDevice] Output device cleared');
      return;
    }
    const index = Number(value);
    setConfig({ output_device_index: index });
    const device = outputDevices.find(d => d.index === index);
    console.log('[AudioDevice] Output device changed to:', device?.name, 'index:', index);
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
      {/* 警告提示 */}
      {warning && (
        <div className="p-3 bg-yellow-50 border border-yellow-400 rounded text-yellow-800 text-sm">
          {warning}
        </div>
      )}

      {/* 输入设备选择 - 虚拟音频线缆 */}
      <div className="p-4 bg-green-50 border border-green-200 rounded">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          🎤 音频输入设备 (Audio Source / Virtual Cable):
        </label>
        <select
          value={config.input_device_index ?? ''}
          onChange={(e) => handleInputDeviceChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          <option value="">-- 选择输入设备 --</option>
          {inputDevices.map((device) => (
            <option key={device.index} value={device.index}>
              [{device.index}] {getDeviceDisplayName(device, false)}
            </option>
          ))}
        </select>
        <p className="mt-2 text-xs text-gray-600">
          选择 VB-Audio CABLE Output 来捕获视频/会议应用的音频
        </p>
      </div>

      {/* 输出设备选择 - 扬声器 */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          🔊 TTS 输出设备 (扬声器/耳机):
        </label>
        <select
          value={config.output_device_index ?? ''}
          onChange={(e) => handleOutputDeviceChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">-- 选择输出设备 --</option>
          {outputDevices.map((device) => (
            <option key={device.index} value={device.index}>
              [{device.index}] {getDeviceDisplayName(device, true)}
            </option>
          ))}
        </select>
        <p className="mt-2 text-xs text-gray-600">
          <strong>重要：</strong>选择真实的扬声器/耳机来听到TTS翻译语音。
          <span className="text-red-600"> 不要选择 CABLE/VB-Audio 设备！</span>
        </p>
      </div>

      {/* 刷新按钮 */}
      <div className="flex justify-end">
        <button
          onClick={loadDevices}
          className="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded text-sm"
        >
          🔄 刷新设备列表
        </button>
      </div>
    </div>
  );
};
