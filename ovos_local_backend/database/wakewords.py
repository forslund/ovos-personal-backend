import json
import time
from os import makedirs
from os.path import join, isdir

from json_database import JsonDatabaseXDG

from ovos_local_backend.backend.decorators import requires_opt_in
from ovos_local_backend.configuration import CONFIGURATION


@requires_opt_in
def save_ww_recording(uuid, uploads):
    if not isdir(join(CONFIGURATION["data_path"], "wakewords")):
        makedirs(join(CONFIGURATION["data_path"], "wakewords"))
    name = str(time.time()).replace(".", "")
    wav_path = join(CONFIGURATION["data_path"], "wakewords",
                    name + ".wav")
    meta_path = join(CONFIGURATION["data_path"], "wakewords",
                     name + ".meta")
    for precisefile in uploads:
        fn = uploads[precisefile].filename
        if fn == 'audio':
            uploads[precisefile].save(wav_path)
        if fn == 'metadata':
            uploads[precisefile].save(meta_path)
    with open(meta_path) as f:
        meta = json.load(f)

    meta["accountId"] = uuid
    # {"name": "hey-mycroft",
    # "engine": "0f4df281688583e010c26831abdc2222",
    # "time": "1592192357852",
    # "sessionId": "7d18e208-05b5-401e-add6-ee23ae821967",
    # "accountId": "0",
    # "model": "5223842df0cdee5bca3eff8eac1b67fc"}
    with JsonWakeWordDatabase() as db:
        db.add_wakeword(uuid, meta["name"], wav_path, meta)


class WakeWordRecording:
    def __init__(self, wakeword_id, transcription, path, meta="{}"):
        self.wakeword_id = wakeword_id
        self.transcription = transcription
        self.path = path
        if isinstance(meta, str):
            meta = json.loads(meta)
        self.meta = meta


class JsonWakeWordDatabase(JsonDatabaseXDG):
    def __init__(self):
        super().__init__("ovos_wakewords")

    def add_wakeword(self, transcription, path, meta="{}"):
        wakeword_id = self.total_wakewords() + 1
        wakeword = WakeWordRecording(wakeword_id, transcription, path, meta)
        self.add_item(wakeword)

    def total_wakewords(self):
        return len(self)

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.commit()
        except Exception as e:
            print(e)
