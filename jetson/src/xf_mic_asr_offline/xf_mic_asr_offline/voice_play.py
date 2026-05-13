#!/usr/bin/env python3
# encoding: utf-8
# @Author: Aiden
# @Date: 2022/11/21
import os
import subprocess
import re
#from ament_index_python.packages import get_package_share_directory
#wav_dir = get_package_share_directory('xf_mic_asr_offline')
#wav_path = os.path.join(wav_dir, 'share/xf_ring_mic_asr_offline/feedback_voice')
wav_path = '/home/ubuntu/ros2_ws/src/xf_mic_asr_offline/feedback_voice'

def get_usb_audio_device():
    result = subprocess.run(['aplay', '-l'], stdout=subprocess.PIPE, text=True)
    usb_device = None
    for line in result.stdout.splitlines():
        if 'USB' in line:
            match = re.search(r'card (\d+):.*device (\d+)', line)
            if match:
                card, device = match.groups()
                usb_device = f'{card}'
                break

    if usb_device:
        return usb_device
    else:
        raise RuntimeError("USB Audio Device not found")

def get_path(f, language='Chinese'):
    if language == 'Chinese':
        return os.path.join(wav_path, f + '.wav')
    else:    
        return os.path.join(wav_path, 'english', f + '.wav')

def play(voice, volume=80, language='Chinese'):
    try:
        device = get_usb_audio_device()
        # os.system('amixer -q -D pulse set Master {}%'.format(volume))
        # os.system('aplay -q -Dplughw:3,0 ' + get_path(voice, language))
        os.system(f'aplay -q -Dplughw:{device},0 -fS16_LE -r16000 -c1 -N --buffer-size=81920 ' + get_path(voice, language))

    except BaseException as e:
        print('error', e)

if __name__ == '__main__':
    play('ok')
    play('running', language="English")

