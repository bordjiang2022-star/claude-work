// 音频设备管理服务
class AudioDeviceService {
  private outputDevices: MediaDeviceInfo[] = [];
  private selectedOutputDeviceId: string = '';

  /**
   * 初始化并枚举音频输出设备
   */
  async initialize(): Promise<void> {
    try {
      // 请求媒体权限以获取设备标签
      await navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        stream.getTracks().forEach(track => track.stop());
      });

      // 枚举设备
      await this.enumerateDevices();

      console.log('[AudioDevice] Initialized, found', this.outputDevices.length, 'output devices');
    } catch (error) {
      console.error('[AudioDevice] Failed to initialize:', error);
      throw error;
    }
  }

  /**
   * 枚举音频输出设备
   */
  async enumerateDevices(): Promise<MediaDeviceInfo[]> {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      this.outputDevices = devices.filter(device => device.kind === 'audiooutput');

      console.log('[AudioDevice] Found output devices:', this.outputDevices.map(d => ({
        id: d.deviceId,
        label: d.label,
        groupId: d.groupId,
      })));

      // 如果还没选择设备，使用第一个非VB-Audio设备
      if (!this.selectedOutputDeviceId && this.outputDevices.length > 0) {
        // 优先选择不是VB-Audio的设备（通常是真实扬声器）
        const nonVirtualDevice = this.outputDevices.find(
          d => !d.label.toLowerCase().includes('cable') &&
               !d.label.toLowerCase().includes('vb-audio')
        );
        this.selectedOutputDeviceId = nonVirtualDevice?.deviceId || this.outputDevices[0].deviceId;
        console.log('[AudioDevice] Auto-selected device:', this.getSelectedDeviceLabel());
      }

      return this.outputDevices;
    } catch (error) {
      console.error('[AudioDevice] Failed to enumerate devices:', error);
      throw error;
    }
  }

  /**
   * 获取所有输出设备
   */
  getOutputDevices(): MediaDeviceInfo[] {
    return this.outputDevices;
  }

  /**
   * 设置选中的输出设备
   */
  setOutputDevice(deviceId: string): void {
    const device = this.outputDevices.find(d => d.deviceId === deviceId);
    if (device) {
      this.selectedOutputDeviceId = deviceId;
      console.log('[AudioDevice] Selected output device:', device.label);
    } else {
      console.warn('[AudioDevice] Device not found:', deviceId);
    }
  }

  /**
   * 获取选中的输出设备ID
   */
  getSelectedOutputDeviceId(): string {
    return this.selectedOutputDeviceId;
  }

  /**
   * 获取选中的输出设备标签
   */
  getSelectedDeviceLabel(): string {
    const device = this.outputDevices.find(d => d.deviceId === this.selectedOutputDeviceId);
    return device?.label || 'Default';
  }

  /**
   * 检查浏览器是否支持setSinkId
   */
  supportsSinkId(): boolean {
    const audio = document.createElement('audio');
    return 'setSinkId' in audio;
  }
}

export const audioDeviceService = new AudioDeviceService();
