import os
import random
import pygame
from settings import *


class Audio:
    """Load music + sound effects, route them to dedicated channels, and expose a small named API.

    Loads every asset on construction so playback during gameplay does not
    stall on disk I/O. Music tracks live on dedicated channels (so they can
    be paused/unpaused independently of SFX) and SFX are dispatched through
    a single ``play(name)`` entry point backed by ``SOUND_BINDINGS``.
    """

    # Logical channel name -> mixer channel index. Centralizing the mapping
    # makes it obvious which SFX share a channel (and therefore can cut each
    # other off) and which get a reserved slot.
    CHANNEL_IDS = {
        'intro_music': 0,
        'bg_music':    1,
        'explosion':   2,
        'laser':       3,
        'alarm':       4,
        'ufo':         5,
        'pause':       6,
        'unpause':     7,
        'powerup':     8,
        'hyper':       10,
    }

    # Logical SFX name -> (channel name, attribute holding the loaded Sound).
    # Mirrors AudioManager.SOUND_BINDINGS in dungeon-digger so call sites
    # use ``audio.play('laser')`` instead of touching channel objects.
    SOUND_BINDINGS = {
        'explosion':      ('explosion', 'explosion_sound'),
        'laser':          ('laser',     'laser_sound'),
        'hyper':          ('hyper',     'hyper_sound'),
        'powerup_heart':  ('powerup',   'powerup_heart'),
        'powerup_twin':   ('powerup',   'powerup_twin'),
        'powerup_weapon': ('powerup',   'powerup_weapon'),
        'alarm_med':      ('alarm',     'low_health_alarm1'),
        'alarm_low':      ('alarm',     'low_health_alarm2'),
        'ufo':            ('ufo',       'ufo_sound'),
        'pause':          ('pause',     'pause_sound'),
        'unpause':        ('unpause',   'unpause_sound'),
    }

    def __init__(self) -> None:
        """Initialize the mixer, pre-load every asset, and reserve channels.

        A loading screen should be displayed before constructing this object
        as pre-loading all tracks can cause a brief freeze on slower hardware.
        """
        # Reserve enough channels for the highest index used by CHANNEL_IDS.
        pygame.mixer.set_num_channels(max(self.CHANNEL_IDS.values()) + 1)

        self.master_volume = AudioSettings.DEFAULT_MASTER_VOLUME
        self.muted = AudioSettings.DEBUG_MUTE

        # Music
        self.intro_music = self._load_audio(AudioSettings.MUSIC_DIR, 'star_hero_intro.ogg')
        self.player_down = self._load_audio(AudioSettings.MUSIC_DIR, 'game_over.ogg')

        # Pre-load every BGM track so swapping between songs is allocation-free.
        self.bgm_tracks = [
            self._load_audio(AudioSettings.MUSIC_DIR, filename)
            for filename in AudioSettings.BGM_PLAYLIST
        ]
        self.bg_music = None
        self.last_bgm = None

        # SFX
        self.laser_sound = self._load_audio(AudioSettings.AUDIO_DIR, 'laser.ogg')
        self.hyper_sound = self._load_audio(AudioSettings.AUDIO_DIR, 'hyper.ogg')
        self.explosion_sound = self._load_audio(AudioSettings.AUDIO_DIR, 'explosion.ogg')
        self.low_health_alarm1 = self._load_audio(AudioSettings.AUDIO_DIR, 'sfx_alarm_loop2.ogg')
        self.low_health_alarm2 = self._load_audio(AudioSettings.AUDIO_DIR, 'sfx_alarm_loop1.ogg')
        self.ufo_sound = self._load_audio(AudioSettings.AUDIO_DIR, 'sfx_sound_bling.ogg')
        self.pause_sound = self._load_audio(AudioSettings.AUDIO_DIR, 'sfx_sounds_pause2_in.ogg')
        self.unpause_sound = self._load_audio(AudioSettings.AUDIO_DIR, 'sfx_sounds_pause2_out.ogg')
        self.powerup_twin = self._load_audio(AudioSettings.AUDIO_DIR, 'sfx_sounds_powerup1.ogg')
        self.powerup_weapon = self._load_audio(AudioSettings.AUDIO_DIR, 'sfx_sounds_powerup2.ogg')
        self.powerup_heart = self._load_audio(AudioSettings.AUDIO_DIR, 'sfx_coin_cluster4.ogg')

        # Channel handles, named so call sites do not need to know the index.
        self.channels = {
            name: pygame.mixer.Channel(channel_id)
            for name, channel_id in self.CHANNEL_IDS.items()
        }

        self.update()

    def _load_audio(self, directory: str, filename: str) -> pygame.mixer.Sound:
        """Load one audio asset from disk.

        Args:
            directory: Folder the asset lives in.
            filename: Asset file name relative to ``directory``.

        Returns:
            pygame.mixer.Sound: Loaded sound object ready for playback.
        """
        return pygame.mixer.Sound(os.path.join(directory, filename))

    # -------------------------
    # VOLUME
    # -------------------------

    def _effective_volume(self) -> float:
        """Return the master volume scaled to 0 when debug mute is active.

        Returns:
            float: Effective volume level between 0.0 and 1.0.
        """
        return 0 if self.muted else self.master_volume

    def _half_effective_volume(self) -> float:
        """Return half the effective volume; SFX mix quieter than music.

        Returns:
            float: Half of the current effective volume level.
        """
        return self._effective_volume() / 2

    def update(self) -> None:
        """Reapply the current volume level to every loaded music/SFX asset.

        Call after any change to ``master_volume`` or ``AudioSettings.DEBUG_MUTE``
        so previously-loaded sounds reflect the new level immediately.
        """
        self.muted = AudioSettings.DEBUG_MUTE
        half = self._half_effective_volume()

        self.intro_music.set_volume(self._effective_volume())
        for track in self.bgm_tracks:
            track.set_volume(self._effective_volume())
        self.player_down.set_volume(self._effective_volume())
        self.laser_sound.set_volume(half)
        self.hyper_sound.set_volume(half)
        self.explosion_sound.set_volume(half)
        self.low_health_alarm1.set_volume(half)
        self.low_health_alarm2.set_volume(half)
        self.ufo_sound.set_volume(half)
        self.pause_sound.set_volume(half)
        self.unpause_sound.set_volume(half)
        self.powerup_twin.set_volume(half)
        self.powerup_weapon.set_volume(half)
        self.powerup_heart.set_volume(half)

    # -------------------------
    # SFX
    # -------------------------

    def play(self, name: str) -> None:
        """Play one named sound effect on its reserved channel.

        Args:
            name: A key in ``SOUND_BINDINGS`` (e.g. ``'laser'``, ``'pause'``).
        """
        channel_name, sound_attr = self.SOUND_BINDINGS[name]
        self.channels[channel_name].play(getattr(self, sound_attr))

    # -------------------------
    # MUSIC
    # -------------------------

    def load_random_bgm(self) -> None:
        """Pick the next BGM track, avoiding the most recent one when possible.

        The selected track is stored in ``self.bg_music``. The caller is
        responsible for actually starting playback (so this can be re-run
        without restarting an in-progress track).
        """
        if not self.bgm_tracks:
            return

        choices = self.bgm_tracks
        if self.last_bgm and len(self.bgm_tracks) > 1:
            choices = [track for track in self.bgm_tracks if track is not self.last_bgm]

        self.bg_music = random.choice(choices)
        self.last_bgm = self.bg_music

    def play_intro_music(self) -> None:
        """Start intro music if it isn't already playing."""
        if not self.channels['intro_music'].get_busy():
            self.channels['intro_music'].play(self.intro_music)

    def stop_intro_music(self) -> None:
        """Halt intro music immediately."""
        self.channels['intro_music'].stop()

    def ensure_bgm_playing(self) -> None:
        """Begin a randomly-picked BGM track if no BGM is currently playing."""
        if self.channels['bg_music'].get_busy():
            return
        self.load_random_bgm()
        if self.bg_music is not None:
            self.channels['bg_music'].play(self.bg_music)

    def stop_bgm(self) -> None:
        """Halt background music immediately."""
        self.channels['bg_music'].stop()

    def pause_music(self) -> None:
        """Pause both intro and gameplay music channels (used for pause menu)."""
        self.channels['intro_music'].pause()
        self.channels['bg_music'].pause()

    def unpause_music(self) -> None:
        """Resume the music channels paused by ``pause_music``."""
        self.channels['intro_music'].unpause()
        self.channels['bg_music'].unpause()

    def stop_alarms(self) -> None:
        """Stop the low-health alarm channel; safe to call when not playing."""
        self.channels['alarm'].stop()
