# -*- coding: utf-8 -*-
"""
РЈРїСЂР°РІР»РµРЅРёРµ РїСЂРѕС†РµСЃСЃРѕРј winws2.exe
"""

import subprocess
import time
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from utils.config import Config
from utils.logger import logger


class ZapretManager:
    """РЈРїСЂР°РІР»РµРЅРёРµ РїСЂРѕС†РµСЃСЃРѕРј winws2.exe"""

    def __init__(self):
        self.config = Config
        self.process_start_time: Optional[datetime] = None

    def is_running(self) -> bool:
        """
        РџСЂРѕРІРµСЂРєР° Р·Р°РїСѓС‰РµРЅ Р»Рё winws2.exe

        Returns:
            True РµСЃР»Рё РїСЂРѕС†РµСЃСЃ Р·Р°РїСѓС‰РµРЅ
        """
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq winws2.exe", "/NH"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=self.config.PROCESS_CHECK_TIMEOUT,
            )
            return "winws2.exe" in result.stdout
        except Exception as e:
            logger.error(f"РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё СЃС‚Р°С‚СѓСЃР° winws2.exe: {e}")
            return False

    def get_pid(self) -> Optional[int]:
        """
        РџРѕР»СѓС‡РёС‚СЊ PID РїСЂРѕС†РµСЃСЃР° winws2.exe

        Returns:
            PID РёР»Рё None РµСЃР»Рё РїСЂРѕС†РµСЃСЃ РЅРµ Р·Р°РїСѓС‰РµРЅ
        """
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq winws2.exe", "/NH", "/FO", "CSV"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=self.config.PROCESS_CHECK_TIMEOUT,
            )

            if "winws2.exe" in result.stdout:
                # РџР°СЂСЃРёРј CSV: "winws2.exe","12345",...
                parts = result.stdout.split(",")
                if len(parts) >= 2:
                    pid_str = parts[1].strip('"')
                    return int(pid_str)

        except Exception as e:
            logger.error(f"РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ PID: {e}")

        return None

    def _cleanup_windivert(self):
        """РћС‡РёСЃС‚РєР° WinDivert СЃРµСЂРІРёСЃРѕРІ"""
        logger.info("РћС‡РёСЃС‚РєР° WinDivert СЃРµСЂРІРёСЃРѕРІ")

        for service in self.config.WINDIVERT_SERVICES:
            try:
                # РџСЂРѕРІРµСЂСЏРµРј СЃСѓС‰РµСЃС‚РІРѕРІР°РЅРёРµ СЃРµСЂРІРёСЃР°
                result = subprocess.run(
                    ["sc", "query", service],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5,
                )

                if result.returncode == 0:
                    # РћСЃС‚Р°РЅР°РІР»РёРІР°РµРј
                    subprocess.run(
                        ["net", "stop", service],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=5,
                    )

                    # РЈРґР°Р»СЏРµРј
                    subprocess.run(
                        ["sc", "delete", service],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=5,
                    )

                    logger.info(f"РЎРµСЂРІРёСЃ {service} РѕС‡РёС‰РµРЅ")

            except Exception as e:
                logger.debug(f"РЎРµСЂРІРёСЃ {service}: {e}")

    def _enable_tcp_timestamps(self):
        """Р’РєР»СЋС‡РµРЅРёРµ TCP timestamps"""
        try:
            logger.info("Р’РєР»СЋС‡РµРЅРёРµ TCP timestamps")
            subprocess.run(
                ["netsh", "interface", "tcp", "set", "global", "timestamps=enabled"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )
        except Exception as e:
            logger.warning(f"РќРµ СѓРґР°Р»РѕСЃСЊ РІРєР»СЋС‡РёС‚СЊ TCP timestamps: {e}")

    def start(self) -> bool:
        """
        Р—Р°РїСѓСЃРє winws2.exe СЃ С‚РµРєСѓС‰РёРј РїСЂРµСЃРµС‚РѕРј

        Returns:
            True РµСЃР»Рё Р·Р°РїСѓСЃРє СѓСЃРїРµС€РµРЅ
        """
        try:
            logger.info("=== Р—Р°РїСѓСЃРє zapret ===")

            # РџСЂРѕРІРµСЂРєР° С‡С‚Рѕ СѓР¶Рµ РЅРµ Р·Р°РїСѓС‰РµРЅ
            if self.is_running():
                logger.warning("winws2.exe СѓР¶Рµ Р·Р°РїСѓС‰РµРЅ")
                return True

            # РџСЂРѕРІРµСЂРєР° РЅР°Р»РёС‡РёСЏ winws2.exe
            if not self.config.WINWS2_EXE.exists():
                logger.error(f"winws2.exe РЅРµ РЅР°Р№РґРµРЅ: {self.config.WINWS2_EXE}")
                return False

            # РџСЂРѕРІРµСЂРєР° РЅР°Р»РёС‡РёСЏ Р°РєС‚РёРІРЅРѕРіРѕ РїСЂРµСЃРµС‚Р°
            if not self.config.ACTIVE_PRESET.exists():
                logger.error(
                    f"РђРєС‚РёРІРЅС‹Р№ РїСЂРµСЃРµС‚ РЅРµ РЅР°Р№РґРµРЅ: {self.config.ACTIVE_PRESET}"
                )
                return False

            # РћС‡РёСЃС‚РєР° WinDivert
            self._cleanup_windivert()
            time.sleep(1)

            # Р’РєР»СЋС‡РµРЅРёРµ TCP timestamps
            self._enable_tcp_timestamps()

            # РћРїСЂРµРґРµР»СЏРµРј СЂР°Р±РѕС‡СѓСЋ РґРёСЂРµРєС‚РѕСЂРёСЋ
            # In frozen mode winws2.exe must run from resources/ so relative paths work.
            if self.config.IS_FROZEN:
                cwd = self.config.RESOURCES_DIR
            else:
                cwd = self.config.BASE_DIR

            # Р—Р°РїСѓСЃРє winws2.exe РІ С„РѕРЅРµ
            logger.info(f"Р—Р°РїСѓСЃРє winws2.exe СЃ РїСЂРµСЃРµС‚РѕРј: {self.config.ACTIVE_PRESET}")
            logger.info(f"Р Р°Р±РѕС‡Р°СЏ РґРёСЂРµРєС‚РѕСЂРёСЏ: {cwd}")
            logger.info(f"РљРѕРјР°РЅРґР°: {self.config.WINWS2_EXE} @{self.config.ACTIVE_PRESET}")

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE

            # РЎРѕР·РґР°РµРј РІСЂРµРјРµРЅРЅС‹Р№ С„Р°Р№Р» РґР»СЏ Р»РѕРіРѕРІ winws2.exe
            import tempfile

            log_file = Path(tempfile.gettempdir()) / "ZapretManager" / "winws2.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Р—Р°РїСѓСЃРєР°РµРј СЃ Р·Р°С…РІР°С‚РѕРј РІС‹РІРѕРґР°
            with open(log_file, "w", encoding="utf-8") as log_f:
                process = subprocess.Popen(
                    [str(self.config.WINWS2_EXE), f"@{self.config.ACTIVE_PRESET}"],
                    cwd=str(cwd),
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    startupinfo=startupinfo,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                )

            logger.info(f"winws2.exe Р·Р°РїСѓС‰РµРЅ, PID: {process.pid}")
            logger.info(f"Р›РѕРіРё winws2.exe: {log_file}")
            self.process_start_time = datetime.now()

            # Verify that the process actually started.
            time.sleep(2)

            # РџСЂРѕРІРµСЂСЏРµРј РєРѕРґ РІРѕР·РІСЂР°С‚Р°
            return_code = process.poll()
            if return_code is not None:
                logger.error(f"winws2.exe Р·Р°РІРµСЂС€РёР»СЃСЏ СЃ РєРѕРґРѕРј: {return_code}")
                # Р§РёС‚Р°РµРј Р»РѕРіРё РґР»СЏ РґРёР°РіРЅРѕСЃС‚РёРєРё
                try:
                    if log_file.exists():
                        log_content = log_file.read_text(encoding="utf-8", errors="ignore")
                        logger.error(f"Р’С‹РІРѕРґ winws2.exe:\n{log_content}")
                except Exception as e:
                    logger.error(f"РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРѕС‡РёС‚Р°С‚СЊ Р»РѕРіРё: {e}")
                return False

            if not self.is_running():
                logger.error("winws2.exe РЅРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РїСѓСЃС‚РёС‚СЊ")
                # Р§РёС‚Р°РµРј Р»РѕРіРё РґР»СЏ РґРёР°РіРЅРѕСЃС‚РёРєРё
                try:
                    if log_file.exists():
                        log_content = log_file.read_text(encoding="utf-8", errors="ignore")
                        logger.error(f"Р’С‹РІРѕРґ winws2.exe:\n{log_content}")
                except Exception as e:
                    logger.error(f"РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРѕС‡РёС‚Р°С‚СЊ Р»РѕРіРё: {e}")
                return False

            return True

        except Exception as e:
            logger.error(f"РћС€РёР±РєР° Р·Р°РїСѓСЃРєР° winws2.exe: {e}", exc_info=True)
            return False

    def stop(self) -> bool:
        """
        РћСЃС‚Р°РЅРѕРІРєР° winws2.exe

        Returns:
            True РµСЃР»Рё РѕСЃС‚Р°РЅРѕРІРєР° СѓСЃРїРµС€РЅР°
        """
        try:
            logger.info("=== РћСЃС‚Р°РЅРѕРІРєР° zapret ===")

            if not self.is_running():
                logger.info("winws2.exe РЅРµ Р·Р°РїСѓС‰РµРЅ")
                return True

            # РћСЃС‚Р°РЅР°РІР»РёРІР°РµРј РїСЂРѕС†РµСЃСЃ
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "winws2.exe"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )

            logger.info(f"Р РµР·СѓР»СЊС‚Р°С‚ taskkill: {result.returncode}")

            # Р–РґРµРј Р·Р°РІРµСЂС€РµРЅРёСЏ
            time.sleep(1)

            # РћС‡РёСЃС‚РєР° WinDivert
            self._cleanup_windivert()

            self.process_start_time = None

            # Verify that the process actually stopped.
            if self.is_running():
                logger.warning(
                    "winws2.exe РІСЃРµ РµС‰Рµ Р·Р°РїСѓС‰РµРЅ РїРѕСЃР»Рµ РѕСЃС‚Р°РЅРѕРІРєРё"
                )
                return False

            logger.info("winws2.exe РѕСЃС‚Р°РЅРѕРІР»РµРЅ")
            return True

        except subprocess.TimeoutExpired:
            logger.error("РўР°Р№РјР°СѓС‚ РїСЂРё РѕСЃС‚Р°РЅРѕРІРєРµ winws2.exe")
            return False
        except Exception as e:
            logger.error(f"РћС€РёР±РєР° РѕСЃС‚Р°РЅРѕРІРєРё winws2.exe: {e}", exc_info=True)
            return False

    def restart(self) -> bool:
        """
        РџРµСЂРµР·Р°РїСѓСЃРє winws2.exe

        Returns:
            True РµСЃР»Рё РїРµСЂРµР·Р°РїСѓСЃРє СѓСЃРїРµС€РµРЅ
        """
        logger.info("РџРµСЂРµР·Р°РїСѓСЃРє winws2.exe")

        if not self.stop():
            logger.error("РќРµ СѓРґР°Р»РѕСЃСЊ РѕСЃС‚Р°РЅРѕРІРёС‚СЊ winws2.exe")
            return False

        time.sleep(1)

        if not self.start():
            logger.error("РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РїСѓСЃС‚РёС‚СЊ winws2.exe")
            return False

        return True

    def get_status(self) -> Dict:
        """
        РџРѕР»СѓС‡РёС‚СЊ СЃС‚Р°С‚СѓСЃ РїСЂРѕС†РµСЃСЃР°

        Returns:
            РЎР»РѕРІР°СЂСЊ СЃРѕ СЃС‚Р°С‚СѓСЃРѕРј: running, pid, uptime, preset
        """
        running = self.is_running()
        pid = self.get_pid() if running else None

        # Uptime
        uptime = None
        if running and self.process_start_time:
            delta = datetime.now() - self.process_start_time
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            uptime = f"{hours}С‡ {minutes}Рј"

        # РўРµРєСѓС‰РёР№ РїСЂРµСЃРµС‚
        preset_name = "РЅРµ РІС‹Р±СЂР°РЅ"
        if self.config.CURRENT_PRESET_NAME.exists():
            try:
                preset_name = self.config.CURRENT_PRESET_NAME.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        return {"running": running, "pid": pid, "uptime": uptime, "preset": preset_name}
