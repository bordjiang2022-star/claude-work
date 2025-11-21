// 音频设备选择组件
import React, { useEffect, useState } from 'react';
import { audioDeviceService } from '@/services/audioDevice';

export const AudioDeviceSelector: React.FC = () => {
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    initializeDevices();
  }, []);

  const initializeDevices = async () => {
    try {
      await audioDeviceService.initialize();
      const outputDevices = audioDeviceService.getOutputDevices();
      setDevices(outputDevices);
      setSelectedDeviceId(audioDeviceService.getSelectedOutputDeviceId());
      setIsInitialized(true);
    } catch (err: any) {
      console.error('Failed to initialize audio devices:', err);
      setError('Failed to access audio devices. Please grant microphone permission.');
    }
  };

  const handleDeviceChange = (deviceId: string) => {
    audioDeviceService.setOutputDevice(deviceId);
    setSelectedDeviceId(deviceId);
    console.log('TTS output device changed to:', deviceId);
  };

  if (error) {
    return (
      <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm">
        <p className="text-yellow-700">{error}</p>
        <button
          onClick={initializeDevices}
          className="mt-2 px-3 py-1 bg-yellow-500 hover:bg-yellow-600 text-white rounded text-xs"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!isInitialized || devices.length === 0) {
    return (
      <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded text-sm">
        <p className="text-gray-600">Loading audio devices...</p>
      </div>
    );
  }

  return (
    <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded">
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        🔊 TTS Output Device (扬声器选择):
      </label>
      <select
        value={selectedDeviceId}
        onChange={(e) => handleDeviceChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {devices.map((device) => (
          <option key={device.deviceId} value={device.deviceId}>
            {device.label || `Device ${device.deviceId.substring(0, 8)}`}
          </option>
        ))}
      </select>
      <p className="mt-2 text-xs text-gray-600">
        💡 选择真实扬声器输出TTS翻译声音，视频声音可以输出到VB-Audio用于识别
      </p>
      {!audioDeviceService.supportsSinkId() && (
        <p className="mt-2 text-xs text-orange-600">
          ⚠️ Your browser doesn't support audio output device selection
        </p>
      )}
    </div>
  );
};
