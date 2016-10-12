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


from tornado.gen import coroutine
import src
from src.wsclass import subscribe
class AlterQuestionLockingPanel(
        src.boiler_ui_module.BoilerUIModule):
    id_ = 'alternatives-question-panel'
    classes = {'scrolling-panel', 'student'}
    name = 'Panel de Preguntas'
    conf = {
        'static_url_prefix': '/alternatives/question/',
        'static_path':
            './locking_panels/alternatives/question/static',
        'js_files': ['alternatives_question.js'],
        'css_files': ['alternatives_question.css'],
    }

    def render(self):
        return self.render_string(
            '../locking_panels/alternatives/question/'
            'alternatives_question.html')


class AlterQuestionWSC(src.wsclass.WSClass):
    pass
