"""Check the installed fork and opentele binding without network or disk sessions."""
import asyncio
import importlib.metadata as metadata
import json
from pathlib import Path

import telethon
from opentele.tl import TelegramClient as OpenTeleClient
from telethon.extensions import BinaryReader
from telethon.sessions import MemorySession
from telethon.tl import functions, types
from telethon.tl.alltlobjects import LAYER


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


async def check():
    manifest = json.loads(Path(__file__).with_name('manifest.json').read_text())
    require(metadata.version('Telethon') == manifest['version'], 'Wrong Telethon distribution version')
    require(telethon.__version__ == manifest['version'], 'Imported Telethon differs from installed distribution')
    require(metadata.version('opentele') == manifest['opentele_version'], 'Wrong opentele version')
    require(LAYER == manifest['layer'], 'Wrong generated TL layer')
    require(issubclass(OpenTeleClient, telethon.TelegramClient), 'opentele is using another Telethon class')
    session = MemorySession()
    client = OpenTeleClient(session, api_id=1, api_hash='0' * 32, receive_updates=False)
    require(client.session is session, 'opentele is using another session implementation')
    require(not client.is_connected(), 'Compatibility check unexpectedly connected')
    # Exercise generated classes and their shared registry without making RPCs.
    for obj in (types.InputPeerUser(123, 456), functions.help.GetConfigRequest()):
        with BinaryReader(bytes(obj)) as reader:
            decoded = reader.tgread_object()
        require(type(decoded) is type(obj), 'TL registry class mismatch')
        require(bytes(decoded) == bytes(obj), 'TL serialization mismatch')
    print(json.dumps({'version': telethon.__version__, 'layer': LAYER,
                      'opentele': metadata.version('opentele'),
                      'opentele_binding': 'ok', 'tl_roundtrip': 'ok',
                      'connected': client.is_connected()}, indent=2))


if __name__ == '__main__':
    asyncio.run(check())
