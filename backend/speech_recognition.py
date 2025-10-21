"""
语音识别模块
提供语音转文字功能，支持实时语音流处理
使用GPT-4o音频转录API
"""

import logging
import asyncio
from typing import Optional, Callable
import io
from openai import OpenAI

logger = logging.getLogger(__name__)

class SpeechRecognizer:
    """语音识别器类"""

    def __init__(self, language: str = "zh-CN", model: str = "whisper-1"):
        """
        初始化语音识别器

        Args:
            language: 识别语言，默认中文
            model: 使用的模型，默认whisper-1
        """
        self.language = language
        self.model = model
        self.client = OpenAI()

    async def recognize_from_audio_data(self, audio_data: bytes, sample_rate: int = 16000) -> Optional[str]:
        """
        从音频数据识别语音

        Args:
            audio_data: 音频数据（webm格式）
            sample_rate: 采样率

        Returns:
            识别出的文本，如果识别失败返回None
        """
        try:
            # 检查音频数据长度，如果太短则认为没有有效语音
            if len(audio_data) < 1000:
                logger.warning("音频数据太短，无法识别")
                return None

            # 尝试不同的方法来处理音频数据
            # 方法1: 直接使用webm格式
            from io import BytesIO
            audio_file = BytesIO(audio_data)
            audio_file.name = "audio.webm"

            # 使用GPT-4o音频转录API
            logger.info("开始调用GPT-4o音频转录API...")
            try:
                transcription = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=self.language.split('-')[0] if '-' in self.language else self.language,
                    response_format="text"
                )

                text = transcription.strip()
                if text:
                    logger.info(f"语音识别成功: {text}")
                    return text
                else:
                    logger.warning("语音识别返回空文本")
                    return None

            except Exception as api_error:
                logger.warning(f"webm格式失败，尝试转换为wav格式: {api_error}")

                # 方法2: 如果webm失败，尝试转换为简单的wav格式
                # 假设音频数据是16-bit PCM格式
                wav_data = self._convert_to_simple_wav(audio_data, sample_rate)
                if wav_data:
                    wav_file = BytesIO(wav_data)
                    wav_file.name = "audio.wav"

                    transcription = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=wav_file,
                        language=self.language.split('-')[0] if '-' in self.language else self.language,
                        response_format="text"
                    )

                    text = transcription.strip()
                    if text:
                        logger.info(f"语音识别成功 (wav): {text}")
                        return text

                # 如果都失败了，重新抛出原始错误
                raise api_error

        except Exception as e:
            logger.error(f"语音识别异常: {e}")
            return None

    def _convert_to_simple_wav(self, audio_data: bytes, sample_rate: int) -> Optional[bytes]:
        """
        将音频数据转换为简单的WAV格式
        这是一个简化的转换，假设输入是16-bit PCM数据
        """
        try:
            import struct

            # 如果数据看起来像是webm或其他格式，尝试提取PCM数据
            # 这里做一个简单的假设：跳过文件头，直接使用后面的数据作为PCM
            if len(audio_data) > 44:  # webm文件头通常较长
                pcm_data = audio_data[44:]  # 跳过可能的头部
            else:
                pcm_data = audio_data

            # WAV文件头 (44字节)
            # RIFF header
            riff_header = b'RIFF'
            file_size = len(pcm_data) + 36  # 文件总大小
            wave_header = b'WAVE'

            # fmt chunk
            fmt_header = b'fmt '
            fmt_size = 16
            audio_format = 1  # PCM
            num_channels = 1   # 单声道
            sample_rate_bytes = struct.pack('<I', sample_rate)
            byte_rate = struct.pack('<I', sample_rate * num_channels * 2)  # 16-bit
            block_align = struct.pack('<H', num_channels * 2)
            bits_per_sample = struct.pack('<H', 16)

            # data chunk
            data_header = b'data'
            data_size = len(pcm_data)

            wav_header = (riff_header + struct.pack('<I', file_size) + wave_header +
                         fmt_header + struct.pack('<I', fmt_size) +
                         struct.pack('<H', audio_format) + struct.pack('<H', num_channels) +
                         sample_rate_bytes + byte_rate + block_align + bits_per_sample +
                         data_header + struct.pack('<I', data_size))

            return wav_header + pcm_data

        except Exception as e:
            logger.error(f"WAV转换失败: {e}")
            return None


class VoiceProcessor:
    """语音处理器，整合语音识别和处理逻辑"""

    def __init__(self, language: str = "zh-CN"):
        self.recognizer = SpeechRecognizer(language)
        self.is_processing = False

    async def process_voice_message(self, audio_data: bytes) -> Optional[str]:
        """
        处理语音消息

        Args:
            audio_data: 音频数据

        Returns:
            识别出的文本
        """
        if self.is_processing:
            logger.warning("正在处理其他语音消息，请稍后再试")
            return None

        try:
            self.is_processing = True

            # 直接使用音频数据进行识别（模拟）
            text = await self.recognizer.recognize_from_audio_data(audio_data)

            return text

        finally:
            self.is_processing = False

# 全局语音处理器实例
voice_processor = VoiceProcessor()
