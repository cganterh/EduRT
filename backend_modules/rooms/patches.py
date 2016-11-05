# -*- coding: UTF-8 -*-

# COPYRIGHT (c) 2016 Cristóbal Ganter
#
# GNU AFFERO GENERAL PUBLIC LICENSE
#    Version 3, 19 November 2007
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from controller import MSGHandler
from src.db import Room
from .. import router
from .wsclass import RoomsWSC

MSGHandler._room = None

@property
def room(self):
    """Current room asociated with this MSGHandler."""
    return self._room

@room.setter
def room(self, new_room):
    self._room = new_room
    self.room_msg_type = \
        'message.filter.room({})'.format(new_room.id)
    router_object = self.ws_objects[
        router.RouterWSC]
    rooms_object = self.ws_objects[RoomsWSC]

    rooms_object.register_action_in(
        self.room_msg_type,
        action=router_object.to_local,
        channels={'d'}
    )
MSGHandler.room = room
