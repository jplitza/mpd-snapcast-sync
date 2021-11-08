#!/usr/bin/env python3

import asyncio
import logging

import argh
import snapcast.control
from mpd.asyncio import MPDClient


class MPDOutput:
    def __init__(self, data):
        self.id = data['outputid']
        self.name = data['outputname']
        self.enabled = data['outputenabled'] == '1'


class MpdSnapcastSyncer:
    def __init__(self, loop):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._loop = loop
        self.mpd_outputs = {}

    async def setup(self, snapcast_server: str, mpd_server: str) -> None:
        snapcast_task = asyncio.create_task(self.setup_snapcast(snapcast_server))
        mpd_task = asyncio.create_task(self.setup_mpd(mpd_server))
        await snapcast_task
        await mpd_task

    def snapcast_client_changed(self, client: snapcast.control.client.Snapclient) -> None:
        self._loop.create_task(self.async_snapcast_client_changed(client))

    async def async_snapcast_client_changed(self, client: snapcast.control.client.Snapclient) -> None:
        name = client.friendly_name
        try:
            output = self.mpd_outputs[name]
        except KeyError:
            # there is no output named like this Snapcast client, ignore event
            self._logger.debug('Ignoring change of snapcast client %s: No matching MPD output' % name)
            return

        if output.enabled != client.muted:
            # If the output is not enabled and the client is muted (or vice
            # versa), everything is fine.
            return

        self._logger.info('Turning %s MPD output %s' % (
            'off' if client.muted else 'on',
            name
        ))

        # determine which method to call
        actor = self.mpd.disableoutput if client.muted else self.mpd.enableoutput

        # fake stored state of the output to avoid calling
        # mpd_output_changed() from mpd_outputs_changed() when MPD notifies us
        # about our own change
        self.mpd_outputs[name].enabled = not self.mpd_outputs[name].enabled

        # call actual actor method
        await actor(output.id)

    async def mpd_outputs_changed(self) -> None:
        async for output in self.mpd.outputs():
            output = MPDOutput(output)
            try:
                # find stored data about this output
                old_output = self.mpd_outputs[output.name]
            except KeyError:
                # the output didn't exist before, don't trigger any action
                pass
            else:
                if output.enabled != old_output.enabled:
                    # the output's enabled state changed
                    await self.mpd_output_changed(output)

            # update our stored copy of output data
            self.mpd_outputs[output.name] = output

    async def mpd_output_changed(self, output: dict) -> None:
        for client in self.snapcast.clients:
            if client.friendly_name != output.name:
                continue

            self._logger.info('%s snapcast client %s (%s)' % (
                'Unmuting' if output.enabled else 'Muting',
                output.name,
                client.identifier
            ))
            await client.set_muted(not output.enabled)
            return
        else:
            self._logger.debug('Ignoring change of MPD output %s: No matching snapcast client' % output.name)

    async def setup_snapcast(self, snapcast_server: str) -> None:
        self.snapcast = await snapcast.control.create_server(
            self._loop,
            snapcast_server,
        )

        for client in self.snapcast.clients:
            client.set_callback(self.snapcast_client_changed)
            self._logger.debug('Set callback for snapcast client %s' % client.friendly_name)

    async def setup_mpd(self, mpd_server: str) -> None:
        self.mpd = MPDClient()
        await self.mpd.connect(mpd_server)

        # get initial state of outputs
        async for output in self.mpd.outputs():
            output = MPDOutput(output)
            self.mpd_outputs[output.name] = output

        # add idle command to to event loop
        self._loop.create_task(self.listen_mpd())

    async def listen_mpd(self) -> None:
        async for event in self.mpd.idle(['output']):
            await self.mpd_outputs_changed()


def main(
        snapcast_server: str = 'localhost',
        mpd_server: str = 'localhost',
        loglevel: bool = 'INFO'):

    logging.basicConfig(level=loglevel)
    loop = asyncio.get_event_loop()
    syncer = MpdSnapcastSyncer(loop)
    loop.run_until_complete(syncer.setup(snapcast_server, mpd_server))
    loop.run_forever()


if __name__ == '__main__':
    argh.dispatch_command(main)
