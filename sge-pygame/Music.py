# Copyright (C) 2012, 2013 Julian Marchant <onpon4@lavabit.com>
# 
# This file is part of SGE Pygame.
# 
# SGE Pygame is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# SGE Pygame is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with SGE Pygame.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os

import pygame

import sge


__all__ = ['Music']


class Music(object):

    """Music handling class.

    This class stores and plays music.  Music is very similar to sound
    effects, but only one music file can be played at a time, and it is
    more efficient for larger files than `sge.Sound`.

    What music formats are supported depends on the implementation of
    SGE, but Ogg Vorbis is generally a good choice.  See the
    implementation-specific information for a full list of supported
    formats.

    You should avoid the temptation to use MP3 files; MP3 is a patent-
    encumbered format, so many systems do not support it and royalties
    to the patent holders may be required for commercial use.  There are
    many programs which can convert your MP3 files to the free Ogg
    Vorbis format.

    Attributes:
    - ``volume`` -- The volume of the music in percent from 0 to 100 (0
      for no sound, 100 for maximum volume).

    Read-Only Attributes:
    - ``fname`` -- The file name of the music given when it was created.
    - ``id`` -- The unique identifier of the music.
    - ``length`` -- The length of the music in milliseconds.
    - ``playing`` -- Whether or not the music is playing.
    - ``position`` -- The current position (time) playback of the music
      is at in milliseconds.

    """

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = min(value, 100)

        if self.playing:
            pygame.mixer.music.set_volume(value / 100)

    @property
    def length(self):
        return self._length

    @property
    def playing(self):
        return sge.game._music is self and pygame.mixer.music.get_busy()

    @property
    def position(self):
        if self.playing:
            return self._start + pygame.mixer.music.get_pos()
        else:
            return 0

    def __init__(self, fname, id_=None, volume=100, **kwargs):
        """Create a new music object.

        Arguments:
        - ``fname`` -- The name of the sound file in one of the paths
          specified in ``music_directories``.  If set to None, this
          object will not actually play any music.  If this is neither a
          valid sound file nor None, IOError is raised.
        - ``id`` -- The unique identifier of the music.  If set to None,
          ``fname`` minus the extension will be used, modified by SGE if
          it is already the unique idenfifier of another music object.

        All other arguments set the respective initial attributes of the
        music.  See the documentation for `Music` for more information.

        """
        # Since the docs say that ``id`` is a valid keyword argument,
        # you should do this to make sure that that is true.
        id_ = kwargs.setdefault('id', id_)

        self.fname = fname
        self.volume = volume
        self._timeout = None
        self._fade_time = None
        self._start = 0

        if self.fname is not None and pygame.mixer.get_init():
            self._full_fname = None
            for path in sge.music_directories:
                path = os.path.join(path, fname)
                if os.path.isfile(path):
                    self._full_fname = path
                    break

            if self._full_fname is None:
                print("Directories searched:")
                for d in sge.music_directories:
                    print(os.path.normpath(os.path.abspath(d)))
                msg = 'File "{0}" not found.'.format(self.fname)
                raise IOError(msg)

            if id_ is not None:
                self.id = id_
            else:
                self.id = self.fname
                while self.id in sge.game.music:
                    self.id += "_"
        else:
            self._full_fname = None

            if id_ is not None:
                self.id = id_
            else:
                i = 0
                while i in sge.game.music:
                    i += 1

                self.id = i

        sge.game.music[self.id] = self

    def play(self, start=0, loops=0, maxtime=None, fade_time=None):
        """Play the music.

        Arguments:

        - ``start`` -- The number of milliseconds from the beginning to
          start playing at.

        See the documentation for `sge.Sound.play` for more information.

        """
        if self._full_fname is not None:
            if not self.playing:
                pygame.mixer.music.load(self._full_fname)

            if loops is None:
                loops = -1

            sge.game._music = self
            self._timeout = maxtime
            self._fade_time = fade_time

            if self._fade_time > 0:
                pygame.mixer.music.set_volume(0)

            if self.fname.lower().endswith(".mod"):
                # MOD music is handled differently in Pygame: it uses
                # the pattern order number rather than the time to
                # indicate the start time.
                self._start = 0
                pygame.mixer.music.play(loops, start)
            else:
                self._start = start
                try:
                    pygame.mixer.music.play(loops, start / 1000)
                except NotImplementedError:
                    pygame.mixer.music.play(loops)

    def queue(self, start=0, loops=0, maxtime=None, fade_time=None):
        """Queue the music for playback.

        This will cause the music to be added to a list of music to play
        in order, after the previous music has finished playing.

        See the documentation for `Music.play` for more information.

        """
        sge.game._music_queue.append((self, start, loops, maxtime, fade_time))

    @staticmethod
    def stop(fade_time=None):
        """Stop the currently playing music.

        See the documentation for `sge.Sound.stop` for more information.

        """
        if fade_time:
            pygame.mixer.music.fadeout(fade_time)
        else:
            pygame.mixer.music.stop()

    @staticmethod
    def pause():
        """Pause playback of the currently playing music."""
        pygame.mixer.music.pause()

    @staticmethod
    def unpause():
        """Resume playback of the currently playing music if paused."""
        pygame.mixer.music.unpause()

    @staticmethod
    def clear_queue():
        """Clear the music queue."""
        sge.game._music_queue = []
