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

import src
from src.wsclass import subscribe
from src import messages as msg

_path = 'backend_modules.router'


class RouterWSC(src.wsclass.WSClass):
    _path = msg.join_path(_path, 'RouterWSC')

    @subscribe('toFrontend', channels={'l', 'd', 'w'})
    def to_frontend(self, message):
        self.redirect_content_to('w', message)

    @subscribe('toDatabase', channels={'l'})
    def to_database(self, message):
        self.redirect_content_to('d', message)

    @subscribe('toLocal', channels={'d', 'w'})
    def to_local(self, message):
        self.redirect_content_to('l', message)
